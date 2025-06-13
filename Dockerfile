# Imagen base
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Copiar e instalar requerimientos
COPY EntidexEnterprise/requirements-prod.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos del proyecto
COPY EntidexEnterprise/conectar_sqlserver.py ./
COPY EntidexEnterprise/manage.py ./
COPY EntidexEnterprise/EntidexEnterprise ./EntidexEnterprise/
COPY EntidexEnterprise/PDFapp ./PDFapp/
COPY static ./static/

# Ejecutar collectstatic para producción
RUN python manage.py collectstatic --noinput

# Ejecutar servidor Django con Gunicorn
CMD sh -c "gunicorn --bind 0.0.0.0:$PORT EntidexEnterprise.wsgi:application"
