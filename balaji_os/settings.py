"""
Django settings for balaji_os project.
Dashboard data is stored in MongoDB.
"""

from pathlib import Path
import os
from urllib.parse import urlparse
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Only load .env files in development (not on Render or production)
if not os.environ.get('RENDER'):
    load_dotenv(BASE_DIR / '.env')
    load_dotenv(BASE_DIR / '.env.local', override=True)

# ── Security ───────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY') or 'django-insecure-static-build-only'

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', '')
if not MONGODB_URI:
    raise ImproperlyConfigured(
        'MONGODB_URI environment variable is required. '
        'Set it to your MongoDB Atlas connection string.'
    )

MONGODB_DATABASE = (
    os.environ.get('MONGODB_DATABASE')
    or urlparse(MONGODB_URI).path.lstrip('/').split('/')[0]
    or 'balaji_os'
)

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.vercel.app',          # all *.vercel.app subdomains
    '.now.sh',
    '.railway.app',         # Railway domains
    '.onrender.com',        # Render domains
]

# Allow custom domain if set
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN', '')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)

# Railway provides PUBLIC_DOMAIN
RAILWAY_PUBLIC_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

# Render provides RENDER_EXTERNAL_HOSTNAME
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# ── Apps ───────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'dashboard',
]

# ── Middleware ─────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # serves static files
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dashboard.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'balaji_os.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.csrf',
            ],
        },
    },
]

WSGI_APPLICATION = 'balaji_os.wsgi.application'

# ── Internationalisation ───────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ── Static files ───────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise serves static files directly
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
}

# ── Security headers (production only) ────────────
if not DEBUG:
    X_FRAME_OPTIONS = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Vercel sends this
