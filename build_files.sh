#!/bin/bash
# Vercel static-build runs separately from the Python function builder.
set -euo pipefail

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: Python 3 is not available in the Vercel build environment." >&2
  exit 1
fi

echo "==> Using $("$PYTHON" --version 2>&1)"
echo "==> Installing Python requirements for collectstatic..."
"$PYTHON" -m pip install --disable-pip-version-check -r requirements.txt

echo "==> Collecting static files..."
"$PYTHON" manage.py collectstatic --noinput

echo "==> Build complete."
