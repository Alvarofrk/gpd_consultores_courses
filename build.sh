#!/usr/bin/env bash
# Exit on error
set -o errexit

# Print commands
set -x

# Install dependencies
pip install -r requirements.txt

# Install gunicorn if not already installed
pip install gunicorn

# Verify gunicorn configuration
if [ -f "gunicorn.conf.py" ]; then
    echo "✅ Gunicorn configuration found"
else
    echo "❌ Gunicorn configuration not found"
fi

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Cache is handled automatically by Django
# No need for createcachetable or clear_cache commands

# Verify static files
ls -la staticfiles/

# Print Python version
python --version

# Print installed packages
pip freeze

echo "Build completed successfully!"