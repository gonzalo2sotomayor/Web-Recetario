from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.recetas_app.urls')), # Incluye las URLs de la app de recetas
    path('usuarios/', include('apps.usuarios.urls')), # Incluye las URLs de la app de usuarios
    #path('recetas/', include('recetas_app.urls')),
]

# Configuración para servir archivos estáticos y de medios en desarrollo
if settings.DEBUG:
    #urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static')) #Más directo que el anterior
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    