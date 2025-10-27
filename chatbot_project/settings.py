"""
Django settings for chatbot_project project.
"""
from pathlib import Path
import environ, os

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env")) if (BASE_DIR / ".env").exists() else None

# Seguridad / Debug
SECRET_KEY = env('SECRET_KEY', default='unsafe')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# Apps
INSTALLED_APPS = [
    'app_core',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chatbot_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'chatbot_project.wsgi.application'

# --------- BASE DE DATOS: Cloud Run por socket UNIX / Local por TCP -----------
DB_BACKEND = env('DB_BACKEND', default='postgres')  # postgres | sqlite
INSTANCE_CONNECTION_NAME = env('INSTANCE_CONNECTION_NAME', default=None)
DB_SOCKET_DIR = "/cloudsql"  # Cloud Run monta esto con --add-cloudsql-instances

if DB_BACKEND == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / env('SQLITE_NAME', default='db.sqlite3'),
        }
    }
else:
    # Si DB_HOST está definido, asumimos ejecución local por TCP (proxy v2 a 127.0.0.1)
    if env('DB_HOST', default=None):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('DB_NAME'),
                'USER': env('DB_USER'),
                'PASSWORD': env('DB_PASSWORD'),
                'HOST': env('DB_HOST'),
                'PORT': env('DB_PORT', default='5432'),
                'CONN_MAX_AGE': 600,
            }
        }
    else:
        # Cloud Run: connectarse vía socket Unix montado por --add-cloudsql-instances
        if not INSTANCE_CONNECTION_NAME:
            raise RuntimeError("INSTANCE_CONNECTION_NAME es requerido en Cloud Run para Postgres.")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('DB_NAME'),
                'USER': env('DB_USER'),
                'PASSWORD': env('DB_PASSWORD'),
                'HOST': f"{DB_SOCKET_DIR}/{INSTANCE_CONNECTION_NAME}",
                'PORT': '5432',
                'CONN_MAX_AGE': 600,
            }
        }

# Password validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# i18n
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# DRF
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer']
}

# Static
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'app_core' / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'