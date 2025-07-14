from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*'] # Permite todas las peticiones para desarrollo, cámbialo en producción.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}