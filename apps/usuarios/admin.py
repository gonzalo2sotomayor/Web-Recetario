from django.contrib import admin
from apps.recetas_app.models import RecetaFavorita
from .models import Perfil, CategoriaFavorita, Mensaje

admin.site.register(Perfil)
admin.site.register(CategoriaFavorita)
admin.site.register(RecetaFavorita)
admin.site.register(Mensaje)