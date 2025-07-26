from django.contrib import admin
from .models import Receta, Ingrediente, Paso, Comentario

admin.site.register(Receta)
admin.site.register(Ingrediente)
admin.site.register(Paso)
admin.site.register(Comentario)