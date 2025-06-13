# Imagen base liviana con Python
FROM python:3.11-slim

# No crear archivos pyc y logs con buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Variable de puerto usada por Railway
ENV PORT=8000

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias necesarias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip
RUN pip install --upgrade pip

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar solo los archivos y carpetas necesarias del proyecto
COPY conectar_sqlserver.py ./
COPY manage.py ./
COPY EntidexEnterprise ./EntidexEnterprise/
COPY PDFapp ./PDFapp/

# Ejecutar el servidor de Django
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "EntidexEnterprise.wsgi:application"]

