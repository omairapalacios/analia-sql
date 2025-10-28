import os
import re
import logging
from pathlib import Path
from typing import List, Dict
from urllib.parse import quote_plus

from django.conf import settings

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent  # LC 0.3

from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


# ---------- Vertex AI LLM provider ----------
from langchain_google_vertexai import ChatVertexAI

def _init_llm():
    return ChatVertexAI(
        model=os.getenv("VERTEX_MODEL_NAME", "gemini-pro"),
        project=os.getenv("VERTEX_PROJECT_ID"),
        location=os.getenv("VERTEX_LOCATION", "us-central1"),
        temperature=0.2,
        max_output_tokens=1024,
    )


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

        # Loguear si faltan credenciales (solo booleanos, no valores)
        if not user or not pwd:
            logging.warning("DB user or password appears empty in settings.DATABASES['default'] (user_present=%s, pwd_present=%s)", bool(user), bool(pwd))

        # URL-encode credentials to safely include special characters
        user_enc = quote_plus(user)
        pwd_enc = quote_plus(pwd)
    
        # Si el host comienza con /cloudsql/, es una instancia de Cloud SQL
        # Usamos las credenciales URL-encoded (user_enc/pwd_enc) para evitar
        # problemas cuando la contraseña contiene caracteres especiales.
        if host.startswith('/cloudsql/'):
            # Usar el socket Unix para Cloud SQL
            url = f"postgresql+psycopg2://{user_enc}:{pwd_enc}@/{name}?host={host}"
        else:
            # Usar TCP para conexiones normales
            url = f"postgresql+psycopg2://{user_enc}:{pwd_enc}@{host}:{port}/{name}"

        # Log parcial (sin exponer contraseña) para depuración
        try:
            logging.info("Construyendo SQLAlchemy URL para DB host=%s name=%s user_present=%s", host, name, bool(user))
        except Exception:
            pass
        return url
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
    except Exception as e:
        print(f"Error al invocar Vertex AI: {str(e)}")
        if "Model not found" in str(e):
            raise RuntimeError(
                "Error de configuración: El modelo de Vertex AI especificado no existe. "
                "Verifica el nombre del modelo y que esté disponible en tu región."
            ) from e
        elif "Permission denied" in str(e):
            raise RuntimeError(
                "Error de permisos: La cuenta de servicio no tiene los permisos necesarios "
                "para acceder a Vertex AI."
            ) from e
        else:
            raise RuntimeError(
                f"Error al procesar la consulta con Vertex AI: {str(e)}"
            ) from e
    print(f'RESULTADO DEL MODELO: {result}')
    answer = result["output"] if isinstance(result, dict) and "output" in result else str(result)
    print(f'RESPUESTA: {answer}')

    # Guard extra por si el modelo devolviera SQL bruto en el texto
    if re.search(r"\b(insert|update|delete|drop|alter)\b", answer.lower()):
        return "Se bloqueó una operación no permitida. Solo SELECT está permitido."
    return answer
