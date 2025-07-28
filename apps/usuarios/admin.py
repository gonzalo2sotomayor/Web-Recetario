from django.contrib import admin
from .models import Perfil, CategoriaFavorita, RecetaFavorita, Mensaje

admin.site.register(Perfil)
admin.site.register(CategoriaFavorita)
admin.site.register(RecetaFavorita)
admin.site.register(Mensaje)