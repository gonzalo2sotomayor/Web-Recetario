from django.apps import AppConfig

class RecetasAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.recetas_app' # <-- ¡Cambiado! Debe ser la ruta completa aquí también.