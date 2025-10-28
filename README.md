# 🤖 ANALIA — Chatbot SQL con Memoria (LangChain + Django)

**ANALIA** es un asistente conversacional que interpreta preguntas en lenguaje natural y responde consultando una base de datos SQL. 
Utiliza **Django REST Framework**, **LangChain** y **Vertex AI** (o **OpenAI**) para ofrecer un entorno de análisis conversacional con memoria persistente por sesión.


## 🧭 Contexto
En entornos de analítica de operaciones y BPO, el acceso a datos suele requerir conocimiento técnico (SQL, BI Tools, etc.).  
**ANALIA** permite a supervisores, líderes y analistas interactuar con sus datos de rendimiento mediante lenguaje natural.

### Objetivos principales:
- Democratizar el acceso a la información.
- Reducir tiempos de generación de reportes y análisis.
- Mostrar una arquitectura reproducible en **GCP (Google Cloud Platform)** con costos bajos.
- Probar integración de IA Generativa (**Gemini de Vertex AI**) dentro de una app Python.


## 💡 Descripción general
El sistema está dividido en tres capas principales:


### 🔹 Frontend
- Interfaz web ligera (`templates/chat.html`) desarrollada con HTML, CSS y JavaScript.
- Permite crear sesiones, enviar preguntas y mostrar las respuestas del asistente.
- Se comunica con la API REST mediante `fetch()` y gestiona el `session_id`.

### 🔹 Backend
- Construido con **Django + Django REST Framework**.
- Gestiona sesiones de chat, historial de mensajes y conexión a la base de datos.
- Exposición de endpoints REST:
  - `/api/chat/` → procesamiento principal del mensaje.
  - `/api/health` → diagnóstico del sistema.
  - `/api/sessions` → gestión de sesiones activas.

### 🔹 Módulo de Inteligencia Artificial
- Implementado con **LangChain 0.3** y el modelo **Gemini (Vertex AI)**.
- Usa el componente `create_sql_agent()` para transformar lenguaje natural en SQL.
- Integra **SQLAlchemy** para ejecutar consultas y retornar resultados reales.
- Incluye **memoria conversacional persistente** (`SQLChatMessageHistory`), lo que permite mantener contexto entre mensajes.
- Se establecen **guardrails** para restringir operaciones a solo lectura (`SELECT`).
---

## ⚙️ Funcionalidades principales

| Tipo | Descripción |
|------|--------------|
| 💬 **Conversación natural** | Permite realizar preguntas en lenguaje natural sobre datos empresariales. |
| 🧠 **Generación de SQL automática** | Convierte texto en consultas SQL de solo lectura. |
| 🗂️ **Memoria de sesión** | Mantiene el contexto conversacional por usuario/sesión. |
| 🔒 **Seguridad de consultas** | Bloquea comandos peligrosos (INSERT, UPDATE, DELETE, DROP, ALTER). |
---

## 🧩 Arquitectura general
```
Usuario final (chat web)
       │
Django API REST (/api/chat/, /api/sessions/, /api/health/)
       │
LangChain SQL Agent (VertexAI u OpenAI)
       │
Base de Datos (PostgreSQL)
```



## 🧱 Stack tecnológico

| Capa | Tecnología | Descripción |
|------|-------------|--------------|
| **Frontend** | HTML, CSS, JS | Interfaz simple y ligera de chat. |
| **Backend** | Django + Django REST Framework | API REST y gestión de sesiones/mensajes. |
| **IA** | LangChain 0.3 + Vertex AI (Gemini 2.5 flash) | Agente SQL para generación de consultas. |
| **BD** | PostgreSQL / SQLite | Almacenamiento de datos y sesiones. |
| **Infraestructura** | Docker, Cloud Run, Cloud SQL | Despliegue escalable en GCP. |
| **Seguridad** | Guardrails + Validaciones DRF | Control de consultas SQL y entradas del usuario. |

---

## 🗃️ Estructura del proyecto
```
analia-chatbot/
├── chatbot_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── app_core/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── services/sql_agent.py
│   └── management/commands/
│       ├── hello.py
│       └── seed_demo.py
├── templates/chat.html
├── requirements.txt
└── manage.py
```

## ☁️ Ejecución y despliegue

### Ejecución local
```bash
cd chatbot_project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
# Visita http://127.0.0.1:8000
```

### Despliegue en GCP
```bash
# Build de la imagen
docker build -t us-central1-docker.pkg.dev/<PROJECT_ID>/analia-repo/analia-chatbot:latest .

# Push a Artifact Registry
docker push us-central1-docker.pkg.dev/<PROJECT_ID>/analia-repo/analia-chatbot:latest

# Desplegar en Cloud Run
gcloud run deploy analia-chatbot \
  --image us-central1-docker.pkg.dev/<PROJECT_ID>/analia-repo/analia-chatbot:latest \
  --region us-central1 \
  --add-cloudsql-instances "<INSTANCE_CONNECTION_NAME>" \
  --set-env-vars "VERTEX_PROJECT_ID=<PROJECT_ID>,VERTEX_MODEL_NAME=gemini-5.5-flash,VERTEX_LOCATION=us-central1"
```



## 🧠 Futuras mejoras
- Visualización de datos tabulares.
- Autenticación JWT por roles.
- Conexión multi–fuente SQL.
- Integración con RAG y documentos externos.
- Logging estructurado y métricas LLM.


## 🧾 Licencia

> Proyecto ideal como base para productos internos, asistentes de datos o soluciones educativas con IA.

---

© 2025 – Proyecto académico y demostrativo. Licencia MIT.
