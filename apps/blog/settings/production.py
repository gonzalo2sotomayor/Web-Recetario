from .base import *

DEBUG = False

ALLOWED_HOSTS = ['tu_dominio.com', 'www.tu_dominio.com', 'IP_de_tu_servidor'] # ¡IMPORTANTE: Cambiar en producción!

# Configuración para static files en producción (puedes recolectarlos en un solo lugar)
STATIC_ROOT = BASE_DIR / 'staticfiles' # Donde Django recolectará los archivos estáticos en producción

# Si usas alguna solución de almacenamiento de archivos en la nube, configúrala aquí.

# Seguridad adicional para producción
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000 # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True