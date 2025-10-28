from pathlib import Path
import environ, os

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
# Cargar .env solo en desarrollo/local para NO sobrescribir variables de entorno
# provistas por el entorno de ejecución (por ejemplo Cloud Run). Si estamos
# desplegados en Cloud Run se provee INSTANCE_CONNECTION_NAME y no queremos que
# el contenido de .env (p. ej. DB_PASSWORD=${{DB_PASSWORD}}) reemplace la
# variable real provista por la plataforma.
if (BASE_DIR / ".env").exists() and not os.environ.get("INSTANCE_CONNECTION_NAME"):
    environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="unsafe")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "app_core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "chatbot_project.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "chatbot_project.wsgi.application"

# --------- DB: Cloud Run (socket UNIX) / Local TCP -----------
DB_BACKEND = env("DB_BACKEND", default="postgres")  # postgres | sqlite
INSTANCE_CONNECTION_NAME = env("INSTANCE_CONNECTION_NAME", default=None)
DB_SOCKET_DIR = "/cloudsql"  # Cloud Run montará esto con --add-cloudsql-instances

if DB_BACKEND == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # Si se proporcionó INSTANCE_CONNECTION_NAME, usar socket Unix (producción Cloud Run)
    if INSTANCE_CONNECTION_NAME:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": env("DB_NAME"),
                "USER": env("DB_USER"),
                "PASSWORD": env("DB_PASSWORD"),
                "HOST": os.path.join(DB_SOCKET_DIR, INSTANCE_CONNECTION_NAME),
                "PORT": "5432",
            }
        }
    else:
        # Local TCP (por ejemplo, Docker local o PGAdmin)
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": env("DB_NAME", default="analia_db"),
                "USER": env("DB_USER", default="postgres"),
                "PASSWORD": env("DB_PASSWORD", default="postgres"),
                "HOST": env("DB_HOST", default="127.0.0.1"),
                "PORT": env("DB_PORT", default="5432"),
            }
        }

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"]
}

# Static
STATIC_URL = env("DJANGO_STATIC_URL", default="/static/")
STATIC_ROOT = Path(env("STATIC_ROOT", default=str(BASE_DIR / "staticfiles")))
STATICFILES_DIRS = [BASE_DIR / "app_core" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"