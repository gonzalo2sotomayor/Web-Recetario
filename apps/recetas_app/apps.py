from django.apps import AppConfig

class RecetasAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.recetas_app' # La ruta completa a la aplicación
    label = 'recetas_app' # El nombre corto que Django usará para esta app 
    verbose_name = 'Aplicación de Recetas' #Nombre para el panel de administración 
