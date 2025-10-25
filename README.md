# 🤖 ANALIA — Chatbot SQL con Memoria (LangChain + Django)

**ANALIA** es un asistente conversacional que interpreta preguntas en lenguaje natural y responde consultando una base de datos SQL. 
Utiliza **Django REST Framework**, **LangChain** y **Vertex AI** (o **OpenAI**) para ofrecer un entorno de análisis conversacional con memoria persistente por sesión.

---

## 🧭 Contexto
En entornos de analítica de operaciones y BPO, el acceso a datos suele requerir conocimiento técnico (SQL, BI Tools, etc.).  
**ANALIA** permite a supervisores, líderes y analistas interactuar con sus datos de rendimiento mediante lenguaje natural.

---

## 💡 Descripción general
El sistema está dividido en tres capas principales:

| Capa | Descripción |
|------|--------------|
| **Frontend (Chat UI)** | Interfaz HTML+JS tipo chat con chips de ejemplos, exportación, copia de cURL y borrado de sesiones. |
| **Backend (API REST Django)** | Endpoints para mensajes, gestión de sesiones y health check. |
| **Agente NL→SQL (LangChain)** | Traduce lenguaje natural a SQL seguro (solo SELECT) con memoria por sesión. |

---

## ⚙️ Funcionalidades principales
1. **Chat conversacional NL→SQL**
   - `POST /api/chat/` — responde consultas SQL automáticas.
2. **Memoria de conversación**
   - Persiste el contexto por `session_id`.
3. **Gestión de sesiones**
   - Crear, listar o eliminar sesiones activas.
4. **Chequeo de salud**
   - `GET /api/health/` informa proveedor LLM, BD y hora.
5. **UI web ligera**
   - Chat HTML+JS con exportación JSON, chips y copiar cURL.
6. **Comandos de gestión**
   - `python manage.py hello`
   - `python manage.py seed_demo`

---

## 🧩 Arquitectura general
```
Usuario final (chat web)
       │
Django API REST (/api/chat/, /api/sessions/, /api/health/)
       │
LangChain SQL Agent (VertexAI u OpenAI)
       │
Base de Datos (SQLite o PostgreSQL)
```

---

## 🧱 Stack tecnológico
| Componente | Tecnología |
|-------------|-------------|
| **Backend** | Django 5.x, Django REST Framework |
| **IA / LLM** | LangChain 0.3+, VertexAI (gemini-1.5-pro) o OpenAI (gpt-4o-mini) |
| **Base de datos** | SQLite / PostgreSQL |
| **Infraestructura** | Gunicorn / Uvicorn / Docker-ready |
| **Frontend** | HTML + CSS + JS nativo |
| **Dependencias clave** | `langchain`, `sqlalchemy`, `django-environ`, `psycopg2-binary` |

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

---

## 🚀 Instalación rápida
```bash
git clone https://github.com/<tu-usuario>/analia-chatbot.git
cd analia-chatbot
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abrir 👉 [http://localhost:8000](http://localhost:8000)

---

## 🧠 Futuras mejoras
- Visualización de datos tabulares.
- Autenticación JWT por roles.
- Conexión multi–fuente SQL.
- Logging estructurado y métricas LLM.
- Despliegue en GCP Cloud Run o AWS ECS.
- Integración con RAG y documentos externos.

---

## 🧰 Comandos útiles de desarrollo y despliegue

### 🧪 Pruebas
```bash
python manage.py test
```

### 🐳 Docker
```bash
docker build -t analia-chatbot .
docker run -p 8000:8000 analia-chatbot
```

### ☁️ Cloud Run (GCP)
```bash
gcloud run deploy analia-chatbot   --source .   --region us-central1   --platform managed   --allow-unauthenticated
```

---

## 🧾 Licencia
MIT © 2025 — Curso Final Cibertec
