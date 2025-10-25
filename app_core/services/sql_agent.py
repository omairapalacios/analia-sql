import os
import re
from pathlib import Path
from typing import List, Dict

from django.conf import settings

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent  # LC 0.3

from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


# ---------- LLM providers ----------
PROVIDER = os.getenv("MODEL_PROVIDER", "vertexai").lower()

def _init_llm():
    if PROVIDER == "vertexai":
        # pip install langchain-google-vertexai google-cloud-aiplatform
        from langchain_google_vertexai import ChatVertexAI
        return ChatVertexAI(
            model=os.getenv("VERTEX_MODEL_NAME", "gemini-1.5-pro"),
            project=os.getenv("VERTEX_PROJECT_ID"),
            location=os.getenv("VERTEX_LOCATION", "us-central1"),
            temperature=0.2,
            max_output_tokens=1024,
        )
    elif PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    else:
        from langchain.chat_models.fake import FakeListChatModel
        return FakeListChatModel(responses=["(DEV) No LLM configured."])


# ---------- DB helpers (usa la MISMA DB que Django) ----------
def _alchemy_url_from_django() -> str:
    """
    Construye el URL de SQLAlchemy a partir de settings.DATABASES['default'].
    Soporta sqlite y postgresql.
    """
    cfg = settings.DATABASES["default"]
    engine = cfg["ENGINE"]
    if engine.endswith("sqlite3"):
        path = Path(cfg["NAME"]).resolve()
        return f"sqlite:///{path.as_posix()}"
    elif "postgresql" in engine:
        user = cfg.get("USER", "")
        pwd  = cfg.get("PASSWORD", "")
        host = cfg.get("HOST", "127.0.0.1")
        port = cfg.get("PORT", "5432")
        name = cfg.get("NAME")
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"
    else:
        raise RuntimeError(f"Motor no soportado por el agente: {engine}")

_ENGINE = None
_SQLDB = None

def get_engine():
    """Crea el engine on-demand (evita fallar en import si la DB no está lista)."""
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(_alchemy_url_from_django(), pool_pre_ping=True, future=True)
    return _ENGINE

def get_sqldb():
    """Crea SQLDatabase on-demand (evita inspección temprana)."""
    global _SQLDB
    if _SQLDB is None:
        _SQLDB = SQLDatabase(
            engine=get_engine(),
            include_tables=None,            # o ['core_agent','core_indicator'] para endurecer
            sample_rows_in_table_info=2,
        )
    return _SQLDB


# ---------- Guardrails ----------
def _select_only_guard(sql: str):
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Solo se permiten consultas de lectura (SELECT).")

def run_raw_select(sql: str) -> List[Dict]:
    """Ejecuta SELECT seguro y retorna lista de dicts."""
    _select_only_guard(sql)
    try:
        with get_engine().connect() as conn:
            res = conn.execute(text(sql))
            cols = res.keys()
            return [dict(zip(cols, row)) for row in res.fetchall()]
    except OperationalError as e:
        raise RuntimeError(
            "No se pudo conectar a la base de datos. "
            "Verifica que el servicio esté arriba, las credenciales (.env) y que la DB exista."
        ) from e


# ---------- Memoria persistente ----------
def _make_history(session_id: str) -> SQLChatMessageHistory:
    return SQLChatMessageHistory(
        session_id=session_id,
        connection=_alchemy_url_from_django(),
        table_name=os.getenv("CHAT_HISTORY_TABLE", "langchain_chat_history"),
    )


# ---------- Agente SQL (LangChain 0.3) + memoria ----------
_RUNNABLE = None

def _build_runnable_with_memory():
    llm = _init_llm()
    agent = create_sql_agent(
        llm=llm,
        db=get_sqldb(),                     # se evalúa aquí, no en import
        agent_type="openai-tools",          # reemplazo de OPENAI_FUNCTIONS
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=8,                    # aumentado de 5 a 8 para dar más tiempo de pensamiento
        early_stopping_method="stop",        # cambiado a "stop" para permitir finalización natural
    )
    return RunnableWithMessageHistory(
        agent,
        lambda session_id: _make_history(session_id),
        input_messages_key="input",
        history_messages_key="chat_history",
    )

def _get_runnable():
    global _RUNNABLE
    if _RUNNABLE is None:
        _RUNNABLE = _build_runnable_with_memory()
    return _RUNNABLE


# ---------- API principal ----------
def ask_sql_agent(session_id: str, user_query: str) -> str:
    """
    NL -> SQL -> ejecución -> respuesta.
    Memoria conversacional persistente con SQLChatMessageHistory.
    """
    runnable = _get_runnable()

    system_prefix = (
        "Eres un asistente de BI. Responde SOLO con datos reales de la base. "
        "Si no hay datos suficientes, responde 'No encuentro datos para esa consulta'. "
        "Nunca inventes. Prioriza SELECT a tablas Agent e Indicator. "
        "Si el usuario pregunta por '¿Y en Lima cuántos hay?', recuerda la campaña reciente. "
        "No ejecutes INSERT/UPDATE/DELETE."
    )

    try:
        result = runnable.invoke(
            {"input": f"{system_prefix}\n\nPregunta: {user_query}"},
            config={"configurable": {"session_id": session_id}},
        )
    except OperationalError as e:
        raise RuntimeError(
            "No se pudo conectar a la base de datos durante la inicialización del agente. "
            "Revisa servicio, credenciales y que la DB exista."
        ) from e

    answer = result["output"] if isinstance(result, dict) and "output" in result else str(result)

    # Guard extra por si el modelo devolviera SQL bruto en el texto
    if re.search(r"\b(insert|update|delete|drop|alter)\b", answer.lower()):
        return "Se bloqueó una operación no permitida. Solo SELECT está permitido."
    return answer
