#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "✨ Collecting static files..."
python manage.py collectstatic --no-input

echo "🚀 Running database migrations..."
python manage.py migrate --no-input

echo "🌱 Seeding data..."
python seed_data.py || echo "⚠️ Seeding failed, but continuing deployment..."

echo "✅ Build completed successfully!"
