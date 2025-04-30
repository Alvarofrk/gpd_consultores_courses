# Usar una imagen base de Python ligera
FROM python:3.11-slim

# Establecer variables de entorno para optimizar Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos y instalar las dependencias
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Realizar las migraciones (opcional en Dockerfile)
# RUN python manage.py migrate

# Compilar archivos estáticos
# Nota: Debido a la configuración de Google Cloud Storage, es mejor omitir collectstatic aquí
# RUN python manage.py collectstatic --noinput

# Exponer el puerto que usará el contenedor (opcional, Cloud Run usa 8080 por defecto)
EXPOSE 8080

# Comando para ejecutar la aplicación usando Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080"]
