#!/bin/bash
# Vercel build script — runs after pip install
set -euo pipefail

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Build complete."
