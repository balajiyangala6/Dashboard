"""
WSGI config for balaji_os project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.exceptions import ImproperlyConfigured
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'balaji_os.settings')

if os.environ.get('VERCEL') == '1':
    missing_variables = [
        name for name in ('SECRET_KEY', 'MONGODB_URI')
        if not os.environ.get(name)
    ]
    if missing_variables:
        raise ImproperlyConfigured(
            'Set these environment variables in Vercel: '
            + ', '.join(missing_variables)
            + '.'
        )

application = get_wsgi_application()
