#!/bin/sh

# Salir inmediatamente si ocurre un error
set -e

# Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar Gunicorn
echo "Iniciando Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8080
