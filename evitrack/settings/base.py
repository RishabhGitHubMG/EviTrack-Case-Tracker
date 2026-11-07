"""
Django shared base settings for EviTrack project.

Generated for EviTrack: Digital Evidence and Case Tracker.
Production-ready configuration adhering to strict security and audit standards.
"""
from datetime import timedelta
import os
from pathlib import Path
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR points to /home/rishabh/Downloads/files/evitrack
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'EVITRACK_SECRET_KEY',
    'django-insecure-evitrack-dev-secret-key-change-in-production-!@#$%^&*()_+',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't', 'yes')

ALLOWED_HOSTS: list[str] = []

# Application definition
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',

    # Third-party apps
    'rest_framework',
    'django_filters',
    'axes',

    # EviTrack local apps
    'apps.accounts',
    'apps.cases',
    'apps.evidence',
    'apps.custody',
    'apps.hearings',
    'apps.notifications',
    'apps.reports',
    'apps.audit',
    'apps.core',
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Custom Bootstrap 5 form renderer
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'apps.accounts.middleware.SessionTimeoutMiddleware',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'evitrack-default',
    }
}

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend should be first to monitor all login attempts
    'axes.backends.AxesStandaloneBackend',
    # Default ModelBackend for Django authentication
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'evitrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.global_context',
                'apps.notifications.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'evitrack.wsgi.application'

# Password hashers: Argon2 first, then bcrypt, pbkdf2
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Authentication URLs
AUTH_LOGIN_URL = '/accounts/login/'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Django-Axes configuration (Account Lockout)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'

# Session Security & Timeout settings
SESSION_COOKIE_AGE = 900  # 15 minutes
SESSION_SAVE_EVERY_REQUEST = True
SESSION_TIMEOUT_SECONDS = 900
SESSION_WARNING_SECONDS = 120

# Evidence Vault & Storage settings
# Evidence stored strictly outside the web root
EVIDENCE_ROOT = os.environ.get('EVIDENCE_ROOT', str(BASE_DIR / 'evidence_store'))
EVIDENCE_MAX_SIZE = 100 * 1024 * 1024  # 100 MB

EVIDENCE_ALLOWED_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.bmp',
    '.tiff', '.tif', '.gif', '.mp3', '.wav', '.mp4', '.avi',
    '.mov', '.txt', '.csv', '.rtf', '.odt',
]

EVIDENCE_ALLOWED_MIMES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/png',
    'image/bmp',
    'image/x-ms-bmp',
    'image/tiff',
    'image/gif',
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/x-wav',
    'audio/wave',
    'video/mp4',
    'video/x-msvideo',
    'video/avi',
    'video/quicktime',
    'text/plain',
    'text/csv',
    'application/csv',
    'application/rtf',
    'text/rtf',
    'application/vnd.oasis.opendocument.text',
]

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat schedule for reminder scanning (every 5 minutes)
CELERY_BEAT_SCHEDULE = {
    'scan-and-send-due-reminders': {
        'task': 'apps.notifications.tasks.scan_and_send_due_reminders',
        'schedule': crontab(minute='*/5'),
    },
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'EviTrack <noreply@evitrack.local>'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Reminder timing defaults (offsets in minutes before target event)
REMINDER_DEFAULTS = {
    'hearing_reminders': [7 * 24 * 60, 24 * 60, 120],  # 7 days, 1 day, 2 hours
    'deadline_reminders': [3 * 24 * 60, 24 * 60],        # 3 days, 1 day
}

EVIDENCE_USE_X_ACCEL = os.environ.get('EVIDENCE_USE_X_ACCEL', 'False').lower() in ('true', '1', 't', 'yes')
EVIDENCE_X_ACCEL_LOCATION = '/protected-evidence/'

EMAIL_OTP_TTL_MINUTES = 10
EMAIL_OTP_MAX_ATTEMPTS = 5
EMAIL_OTP_LOCKOUT_MINUTES = 15
AUTH_LOGIN_RATE_LIMIT = int(os.environ.get('AUTH_LOGIN_RATE_LIMIT', 10))
AUTH_LOGIN_RATE_WINDOW_SECONDS = int(os.environ.get('AUTH_LOGIN_RATE_WINDOW_SECONDS', 60))
OTP_VERIFY_RATE_LIMIT = int(os.environ.get('OTP_VERIFY_RATE_LIMIT', 10))
OTP_VERIFY_RATE_WINDOW_SECONDS = int(os.environ.get('OTP_VERIFY_RATE_WINDOW_SECONDS', 60))
EVIDENCE_UPLOAD_RATE_LIMIT = int(os.environ.get('EVIDENCE_UPLOAD_RATE_LIMIT', 10))
EVIDENCE_UPLOAD_RATE_WINDOW_SECONDS = int(os.environ.get('EVIDENCE_UPLOAD_RATE_WINDOW_SECONDS', 60))

REMINDER_MAX_ATTEMPTS = 3
REMINDER_BACKOFF_BASE_MINUTES = 5

SMS_GATEWAY_BACKEND = 'apps.notifications.gateways.ConsoleSMSGateway'

EVITRACK_CSP = {
    'default-src': ["'self'"],
    'script-src': ["'self'", 'https://cdn.jsdelivr.net'],
    'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
    'font-src': ["'self'", 'data:', 'https://cdn.jsdelivr.net', 'https://fonts.gstatic.com'],
    'img-src': ["'self'", 'data:', 'blob:'],
    'media-src': ["'self'", 'blob:'],
    'frame-src': ["'self'"],
    'connect-src': ["'self'"],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
    'frame-ancestors': ["'self'"],
}
