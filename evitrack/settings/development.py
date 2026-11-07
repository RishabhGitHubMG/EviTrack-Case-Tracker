"""
Django development settings for EviTrack project.
"""
import os
import urllib.parse
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Default to SQLite unless USE_SQLITE is explicitly set to false/0
USE_SQLITE = os.environ.get('USE_SQLITE', '1').lower() in ('1', 'true', 't', 'yes')

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Check DATABASE_URL first, then fallback to individual DB_* env vars
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        url = urllib.parse.urlparse(database_url)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': url.path.lstrip('/') or 'evitrack',
                'USER': url.username or 'evitrack',
                'PASSWORD': url.password or 'evitrack',
                'HOST': url.hostname or 'localhost',
                'PORT': str(url.port or 5432),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME', 'evitrack'),
                'USER': os.environ.get('DB_USER', 'evitrack'),
                'PASSWORD': os.environ.get('DB_PASSWORD', 'evitrack'),
                'HOST': os.environ.get('DB_HOST', 'localhost'),
                'PORT': os.environ.get('DB_PORT', '5432'),
            }
        }

# Console email backend for development inspection
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Internal IPs for debug toolbar and local debugging
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]
