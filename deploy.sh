#!/bin/bash

# Script de despliegue para Render.com
# Incluye limpieza de caché y verificación de dependencias

echo "🚀 Iniciando despliegue..."

# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Aplicar migraciones
echo "🗄️ Aplicando migraciones..."
python manage.py migrate

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Limpiar caché
echo "🧹 Limpiando caché..."
python manage.py clear_cache --all

# Verificar configuración
echo "✅ Verificando configuración..."
python manage.py check

echo "🎉 Despliegue completado exitosamente!"
