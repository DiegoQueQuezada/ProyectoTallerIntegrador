# Imagen base liviana con Python
FROM python:3.11-slim

# Establecer variables de entorno para no crear archivos pyc y logs de buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para muchas librerías (como psycopg2, torch, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar pip actualizado
RUN pip install --upgrade pip

# Copiar solo el requirements primero (mejora cache)
COPY requirements.txt .

# Instalar dependencias (sin cache para reducir tamaño)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . .

# Recuerda: Railway usa PORT como variable de entorno
ENV PORT=8000

# Comando para ejecutar el servidor de Django
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "tu_proyecto.wsgi:application"]
