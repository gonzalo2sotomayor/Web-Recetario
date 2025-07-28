from django import forms
from django.forms import inlineformset_factory 
from .models import Comentario, Receta, Ingrediente, Paso

# Formulario para que los usuarios dejen comentarios en las recetas
class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto', 'respuesta_a'] # 'respuesta_a' se usará para hilos de comentarios
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escribe tu comentario aquí...'}),
            'respuesta_a': forms.HiddenInput(), # Campo oculto para manejar respuestas a comentarios
        }
        labels = {
            'texto': 'Tu Comentario',
        }

# Formulario para crear o editar una receta
class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['titulo', 'descripcion', 'imagen'] # 'autor' y 'fecha_publicacion' se asignan en la vista
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Título de la Receta'}),
            'descripcion': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Una breve descripción de la receta...'}),
        }
        labels = {
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'imagen': 'Imagen Principal',
        }

# Formulario para agregar ingredientes a una receta
IngredienteFormSet = inlineformset_factory(
    Receta, # Modelo padre
    Ingrediente, # Modelo hijo
    fields=['nombre', 'cantidad', 'unidad'],
    extra=1, # Número de formularios vacíos a mostrar inicialmente
    can_delete=True, # Permite eliminar ingredientes existentes
    widgets={
        'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Harina'}),
        'cantidad': forms.NumberInput(attrs={'placeholder': 'Ej: 250'}),
        'unidad': forms.TextInput(attrs={'placeholder': 'Ej: gramos'}),
    }
)

# Formulario para agregar pasos a una receta
PasoFormSet = inlineformset_factory(
    Receta, # Modelo padre
    Paso, # Modelo hijo
    fields=['orden', 'descripcion'],
    extra=1, # Número de formularios vacíos a mostrar inicialmente
    can_delete=True, # Permite eliminar pasos existentes
    widgets={
        'orden': forms.NumberInput(attrs={'placeholder': 'Ej: 1'}),
        'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe este paso...'}),
    }
)