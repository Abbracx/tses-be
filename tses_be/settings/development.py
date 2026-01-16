from .base import *  # noqa
from .base import env

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    "SECRET_KEY",
    default="oXPWQPA3C3sdBCuBeXUKq3LBp9YDJ33-306p9EAKf1ja1xkWnKY",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["0.0.0.0", "127.0.0.1", "localhost"]

CSRF_TRUSTED_ORIGINS = ["http://0.0.0.0:8080", "http://127.0.0.1:8080", "http://localhost:8080"]

EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = env("EMAIL_HOST", default="mailhog")  # Use "mailhog" for local development
EMAIL_PORT = env("EMAIL_PORT", default="1025")
EMAIL_HOST_USER= env("EMAIL_HOST_USER", default="mailtrap_user")  
EMAIL_HOST_PASSWORD= env("EMAIL_HOST_PASSWORD", default="Password123")  

# EMAIL_HOST="sandbox.smtp.mailtrap.io"
# EMAIL_HOST_USER="61aa281f95c778"
# EMAIL_HOST_PASSWORD="a9f956d6416957"
# EMAIL_PORT="2525"

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="tses BE <no-reply@localhost>",
)
DOMAIN = env("DOMAIN")
SITE_NAME = "tses BE"