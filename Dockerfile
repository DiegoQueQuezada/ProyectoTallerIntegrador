# Imagen base liviana con Python
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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY conectar_sqlserver.py ./
COPY manage.py ./
COPY EntidexEnterprise ./EntidexEnterprise/

CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "EntidexEnterprise.wsgi:application"]
