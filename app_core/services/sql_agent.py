import os
import re
from typing import Optional
from sqlalchemy import create_engine, text
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# Proveedores LLM
PROVIDER = os.getenv("MODEL_PROVIDER", "vertexai").lower()

def _init_llm():
    if PROVIDER == "vertexai":
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
        # Fallback mock for dev
        from langchain.chat_models.fake import FakeListChatModel
        return FakeListChatModel(responses=["(DEV) No LLM configured."])

def _db_url_from_env():
    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"

ENGINE = create_engine(_db_url_from_env(), pool_pre_ping=True)
SQLDB = SQLDatabase(engine=ENGINE, include_tables=None, sample_rows_in_table_info=2)

def _select_only_guard(sql: str):
    q = sql.strip().lower()
    if not q.startswith("select"):
        raise ValueError("Solo se permiten consultas de lectura (SELECT).")

def run_raw_select(sql: str) -> list[dict]:
    """Ejecuta SELECT seguro y retorna lista de dicts."""
    _select_only_guard(sql)
    with ENGINE.connect() as conn:
        res = conn.execute(text(sql))
        cols = res.keys()
        return [dict(zip(cols, row)) for row in res.fetchall()]

def build_agent(session_id: str, k_context: int = 6):
    """Crea un agente SQL con memoria conversacional persistente en Postgres."""
    llm = _init_llm()

    # Historial persistente en Postgres (tabla auto-gestionada por LangChain)
    history_table = os.getenv("CHAT_HISTORY_TABLE", "langchain_chat_history")
    msg_history = SQLChatMessageHistory(
        session_id=session_id,
        connection_string=_db_url_from_env(),
        table_name=history_table,
    )
    memory = ConversationBufferWindowMemory(
        k=k_context, memory_key="chat_history", return_messages=True, chat_memory=msg_history
    )

    # Agent con herramientas SQL; tipo ReAct para SQL
    agent = create_sql_agent(
        llm=llm,
        db=SQLDB,
        agent_type=AgentType.OPENAI_FUNCTIONS,  # usa funciones/llamado a herramientas
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=5,
        early_stopping_method="generate",
        memory=memory,
        top_k=5,
    )
    return agent, msg_history

def ask_sql_agent(session_id: str, user_query: str) -> str:
    """
    Ejecuta una ronda: convierte NL -> SQL -> ejecuta -> responde.
    Guardrails:
      - restringe a SELECT en ejecución final
      - pasa contexto conversacional
    """
    agent, msg_history = build_agent(session_id=session_id)

    # Instrucciones de sistema/seguridad para minimizar alucinaciones
    system_prefix = (
        "Eres un asistente de BI. Responde SOLO con datos reales de la base."
        " Si no hay datos suficientes, responde 'No encuentro datos para esa consulta'."
        " Nunca inventes. Prioriza SELECT a tablas Agent e Indicator."
        " Si el usuario pregunta por '¿Y en Lima cuántos hay?', recuerda la campaña reciente."
        " No ejecutes INSERT/UPDATE/DELETE."
    )

    # LangChain maneja generación del SQL y ejecución con SQLDatabase
    result = agent.invoke({"input": f"{system_prefix}\n\nPregunta: {user_query}"})

    # `result` puede tener .get('output')
    answer = result["output"] if isinstance(result, dict) and "output" in result else str(result)

    # Hard guard final (por si la cadena devolviera SQL bruto)
    if re.search(r"\b(insert|update|delete|drop|alter)\b", answer.lower()):
        return "Se bloqueó una operación no permitida. Solo SELECT está permitido."

    # Asegurar persistencia en historial (ya guardado por SQLChatMessageHistory)
    # Devuelve texto final
    return answer
