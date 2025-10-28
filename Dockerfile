# syntax=docker/dockerfile:1
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl sed \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=chatbot_project.settings

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copia código (incluye entrypoint.sh)
COPY . /app

# Normaliza CRLF y da permisos
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Preparar staticfiles y ejecutar collectstatic (como root) para que los
# assets estén disponibles dentro de la imagen. Luego ajustamos permisos.
RUN mkdir -p /app/staticfiles \
 && python manage.py collectstatic --noinput || true

# Crea usuario y da propiedad de /app al usuario no privilegiado
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/api/health || exit 1

CMD ["/app/entrypoint.sh"]
