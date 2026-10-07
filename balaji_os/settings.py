"""
Django settings for balaji_os project.
Supports local dev (SQLite) and Vercel production (Neon PostgreSQL).
"""

from pathlib import Path
import os
from urllib.parse import unquote, urlparse
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# Load .env file for local development
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ───────────────────────────────────────
IS_VERCEL = os.environ.get('VERCEL') == '1'

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if IS_VERCEL:
        raise ImproperlyConfigured('Set SECRET_KEY in the Vercel project environment variables.')
    SECRET_KEY = 'django-insecure-local-development-only'

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.vercel.app',          # all *.vercel.app subdomains
    '.now.sh',
]

# Allow custom domain if set
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN', '')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)

# ── Apps ───────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard',
]

# ── Middleware ─────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # serves static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'balaji_os.wsgi.application'

# ── Database ───────────────────────────────────────
# Uses DATABASE_URL env var on Vercel (Neon PostgreSQL).
# Falls back to SQLite for local development.
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL:
    url = urlparse(DATABASE_URL)
    if (
        url.scheme not in ('postgres', 'postgresql')
        or not url.hostname
        or not url.username
        or not url.path.strip('/')
    ):
        raise ImproperlyConfigured('DATABASE_URL must be a valid PostgreSQL connection URL.')

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME':     unquote(url.path.lstrip('/')),
            'USER':     unquote(url.username),
            'PASSWORD': unquote(url.password or ''),
            'HOST':     url.hostname,
            'PORT':     url.port or 5432,
            'OPTIONS': {
                'sslmode': 'require',   # Neon requires SSL
            },
        }
    }
else:
    if IS_VERCEL:
        raise ImproperlyConfigured('Set DATABASE_URL to your PostgreSQL connection URL in Vercel.')

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── Password validation ────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

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

# ── Default primary key ────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Security headers (production only) ────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Vercel sends this
