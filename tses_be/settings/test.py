from .base import *  # noqa
from .base import env

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    "SECRET_KEY",
    default="oXPWQPA3C3sdBCuBeXUKq3LBp9YDJ33-306p9EAKf1ja1xkWnKY",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["0.0.0.0", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS = ["http://0.0.0.0:8000", "http://127.0.0.1:8000"]

# EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST="sandbox.smtp.mailtrap.io"
EMAIL_HOST_USER="61aa281f95c778"
EMAIL_HOST_PASSWORD="a9f956d6416957"
EMAIL_PORT="2525"

DEFAULT_FROM_EMAIL = "tankoraphael6@gmail.com"
DOMAIN = env("DOMAIN")
SITE_NAME = "Loan BE"

# Disable cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable celery for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable email sending in tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
