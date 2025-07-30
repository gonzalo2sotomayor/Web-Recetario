from django import forms
from django.forms import inlineformset_factory
from .models import Receta, Categoria, Comentario, Ingrediente, Paso

# Formulario para crear/editar recetas
class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['titulo', 'descripcion', 'imagen', 'categoria', 'tiempo_preparacion', 'porciones']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Título de la Receta'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Una breve descripción de tu receta...'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'tiempo_preparacion': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Minutos'}),
            'porciones': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 4'}),
        }
        labels = {
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'imagen': 'Imagen Principal',
            'categoria': 'Categoría',
            'tiempo_preparacion': 'Tiempo de Preparación (minutos)',
            'porciones': 'Porciones',
        }

# Formset para ingredientes (para añadir múltiples ingredientes a una receta)
IngredienteFormSet = inlineformset_factory(
    Receta,
    Ingrediente,
    fields=['nombre', 'cantidad', 'unidad'],
    extra=1, # Número inicial de formularios vacíos
    can_delete=True, # Permite eliminar ingredientes existentes
    widgets={
        'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Harina'}),
        'cantidad': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 250'}),
        'unidad': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: gramos'}),
    }
)

# Formset para pasos de preparación (para añadir múltiples pasos a una receta)
PasoFormSet = inlineformset_factory(
    Receta,
    Paso,
    fields=['titulo', 'descripcion'], # Corregido de 'numero' a 'titulo'
    extra=1, # Número inicial de formularios vacíos
    can_delete=True, # Permite eliminar pasos existentes
    widgets={
        'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Título del Paso'}), # Añadido placeholder
        'descripcion': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Describe este paso...'}),
    }
)

# Formulario para añadir un nuevo comentario
class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Escribe tu comentario aquí...'}),
        }
        labels = {
            'contenido': 'Tu Comentario',
        }

# Formulario para editar un comentario existente
class ComentarioEditForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }
        labels = {
            'contenido': 'Editar Comentario',
        }

# Formulario para crear/editar categorías (solo para superusuarios)
class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre de la Categoría'}),
        }
        labels = {
            'nombre': 'Nombre de la Categoría',
            'imagen': 'Imagen de la Categoría (Opcional)',
        }
