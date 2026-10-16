from datetime import timedelta
import os
from pathlib import Path
from urllib.parse import urlsplit

from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

def env_list(name, default):
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def env_bool(name, default):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def origin_from_url(value):
    raw_value = (value or "").strip().rstrip("/")
    if not raw_value:
        return ""
    parsed = urlsplit(raw_value)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return raw_value


def unique_nonempty(values):
    seen = set()
    result = []
    for value in values:
        normalized = origin_from_url(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-x1%6bo16ir)3_pvvdy2+wva^x--^y_@rln7wtteq1@tfah7q0b",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", os.getenv("ALLOWED_HOSTS", "*"))

# Security hardening
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", False)
SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 0)
SECURE_CONTENT_TYPE_NOSNIFF = env_bool("SECURE_CONTENT_TYPE_NOSNIFF", True)


FRONTEND_BASE_URL = os.getenv(
    "DJANGO_FRONTEND_BASE_URL",
    os.getenv("FRONTEND_BASE_URL", ""),
).rstrip("/")
PUBLIC_BACKEND_BASE_URL = os.getenv(
    "DJANGO_PUBLIC_BACKEND_BASE_URL",
    os.getenv("PUBLIC_BACKEND_BASE_URL", os.getenv("BACKEND_BASE_URL", "")),
).rstrip("/")
LOCAL_DEVELOPMENT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
DEFAULT_CORS_ALLOWED_ORIGINS = unique_nonempty(
    [FRONTEND_BASE_URL] + (LOCAL_DEVELOPMENT_ORIGINS if DEBUG else [])
)
CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    os.getenv("CORS_ALLOWED_ORIGINS", ",".join(DEFAULT_CORS_ALLOWED_ORIGINS)),
)
CORS_ALLOW_CREDENTIALS = True
DEFAULT_CSRF_TRUSTED_ORIGINS = unique_nonempty(
    CORS_ALLOWED_ORIGINS + [PUBLIC_BACKEND_BASE_URL]
)
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    os.getenv("CSRF_TRUSTED_ORIGINS", ",".join(DEFAULT_CSRF_TRUSTED_ORIGINS)),
)
EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND",
    os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"),
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
PASSWORD_RESET_TOKEN_TTL_MINUTES = env_int("PASSWORD_RESET_TOKEN_TTL_MINUTES", 60)
DEFAULT_FROM_EMAIL = os.getenv(
    "DJANGO_DEFAULT_FROM_EMAIL",
    os.getenv("DEFAULT_FROM_EMAIL", "University Portal <no-reply@example.edu>"),
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_cleanup.apps.CleanupConfig',
]

EXTERNAL_APPS = [
    "accountant_app",
    "auth_app.apps.AuthAppConfig",
    "notifications_package.apps.NotificationsPackageConfig",
    "admin_app",
    "applicant_app",
    "caterer_app",
    "chatbot_app",
    "executive_app",
    "gradebook_app",
    "home_app",
    "hr_app",
    "librarian_app",
    "quiz_app",
    "student_app",
    "teacher_app",
    "technician_app",
]


INSTALLED_APPS += EXTERNAL_APPS


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'admin_app.ums_policy.UmsPolicyMiddleware',
    'admin_app.audit.AuditActionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME') or os.getenv('POSTGRES_DB', 'portal_db'),
        'USER': os.getenv('DB_USER') or os.getenv('POSTGRES_USER', 'portal_user'),
        'PASSWORD': os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'postgresql'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': env_int('DB_CONN_MAX_AGE', 300),
        'CONN_HEALTH_CHECKS': env_bool('DB_CONN_HEALTH_CHECKS', True),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv(
            "DJANGO_CACHE_URL",
            os.getenv("REDIS_CACHE_URL", "redis://redis:6379/2"),
        ),
        "KEY_PREFIX": os.getenv("DJANGO_CACHE_KEY_PREFIX", "portal"),
        "TIMEOUT": env_int("DJANGO_CACHE_TIMEOUT_SECONDS", 300),
    }
}

TEST_RUNNER = "core.test_runner.IsolatedCacheTestRunner"


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Background tasks

TASKS = {
    "default": {
        "BACKEND": "core.task_backend.CeleryTaskBackend",
        "QUEUES": ["default"],
    }
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TIMEZONE = os.getenv("DJANGO_CELERY_TIMEZONE", os.getenv("CELERY_TIMEZONE", TIME_ZONE))
CELERY_BEAT_SCHEDULE = {
    "process-due-reminders-every-minute": {
        "task": "core.enqueue_django_task",
        "schedule": crontab(),
        "args": ("notifications_package.tasks.process_due_reminders_task",),
    },
    "mark-overdue-fines-hourly": {
        "task": "core.enqueue_django_task",
        "schedule": crontab(minute=0),
        "args": ("accountant_app.tasks.mark_overdue_fines_task",),
    },
    "initialize-canteen-allowances-monthly": {
        "task": "core.enqueue_django_task",
        "schedule": crontab(minute=0, hour=8, day_of_month=1),
        "args": ("caterer_app.tasks.initialize_canteen_allowances_task",),
    },
    "send-monthly-database-backup-email": {
        "task": "core.enqueue_django_task",
        "schedule": crontab(minute=0, hour=8, day_of_month=1),
        "args": ("admin_app.tasks.send_monthly_database_backup_email_task",),
    },
}


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles"))
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))
DEFAULT_FILE_STORAGE = "core.upload_security.SecureFileSystemStorage"







# JWT Configurations
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'auth_app.permissions.IsActiveUmsUser',
    ),
    # 'DEAULT_RENDERER_CLASSES':('rest_framework.renderers.JSONRenderer',)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '200/minute',
        'public_read': os.getenv('PUBLIC_READ_THROTTLE_RATE', '3000/minute'),
        'login': os.getenv('LOGIN_THROTTLE_RATE', '10/minute'),
        'applicant_registration': os.getenv('APPLICANT_REGISTRATION_THROTTLE_RATE', '10/minute'),
        'token_refresh': os.getenv('TOKEN_REFRESH_THROTTLE_RATE', '30/minute'),
    },
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_SCHEMA_CLASS': 'core.schema.PortalAutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,

}

SPECTACULAR_SETTINGS = {
    "TITLE": "Portal API",
    "DESCRIPTION": "Authenticated API schema for the portal backend.",
    "VERSION": "1.0.0",
    "SERVE_PUBLIC": False,
    "SERVE_PERMISSIONS": ["auth_app.permissions.IsAdminRole"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/(auth|admin|student|teacher|executive|applicant|finance|canteen|chatbot|gradebook|hr|librarian|quiz|ict-helpdesk|notifications)",
}


CHATBOT_OLLAMA_BASE_URL = os.getenv(
    "CHATBOT_OLLAMA_BASE_URL",
    os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
).rstrip("/")
CHATBOT_MODEL = os.getenv("CHATBOT_MODEL", "qwen3:14b")
CHATBOT_FAST_MODEL = os.getenv("CHATBOT_FAST_MODEL", "qwen3:8b")
CHATBOT_LLM_ENABLED = env_bool("CHATBOT_LLM_ENABLED", False)
CHATBOT_LLM_TIMEOUT_SECONDS = env_int("CHATBOT_LLM_TIMEOUT_SECONDS", 45)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=3),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}
