from django.contrib import admin
from .models import Receta, Ingrediente, Paso, Comentario

#admin.site.register(Ingrediente)
#admin.site.register(Paso)
admin.site.register(Comentario)

#Para mostrar ingredientes y pasos directamente en el admin de Receta
class IngredienteInline(admin.TabularInline):
    model = Ingrediente
    extra = 1 # Número de campos extra para añadir

class PasoInline(admin.TabularInline):
    model = Paso
    extra = 1

@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    inlines = [IngredienteInline, PasoInline] # Incluimos los inlines aquí
    list_display = ('titulo', 'autor', 'fecha_publicacion')
    search_fields = ('titulo', 'descripcion', 'autor__username')
    list_filter = ('autor', 'fecha_publicacion')