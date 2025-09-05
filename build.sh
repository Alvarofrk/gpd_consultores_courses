#!/usr/bin/env bash
# Exit on error
set -o errexit

# Print commands
set -x

# Install dependencies
pip install -r requirements.txt

# Install gunicorn if not already installed
pip install gunicorn

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create cache table
python manage.py createcachetable

# Clear cache to ensure fresh start
python manage.py clear_cache --all

# Verify static files
ls -la staticfiles/

# Print Python version
python --version

# Print installed packages
pip freeze

echo "Build completed successfully!"