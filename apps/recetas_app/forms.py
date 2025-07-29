from django import forms
from django.forms import inlineformset_factory 
from .models import Comentario, Receta, Ingrediente, Paso, Categoria

# Formulario para que los usuarios dejen comentarios en las recetas
class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto', 'respuesta_a'] 
        widgets = {
            'texto': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Escribe tu comentario aquí...'}),
            'respuesta_a': forms.HiddenInput(), 
        }
        labels = {
            'texto': 'Tu Comentario',
        }

# Formulario para crear o editar una receta
class RecetaForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        empty_label="Selecciona una categoría", 
        required=False, 
        label="Categoría",
        widget=forms.Select(attrs={'class': 'form-select'}) 
    )

    class Meta:
        model = Receta
        fields = ['titulo', 'descripcion', 'imagen', 'categoria', 'tiempo_preparacion', 'porciones'] 
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Título de la Receta'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 6, 'placeholder': 'Una breve descripción de la receta...'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-input'}), 
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

# Formulario para agregar ingredientes a una receta
IngredienteFormSet = inlineformset_factory(
    Receta, 
    Ingrediente, 
    fields=['nombre', 'cantidad', 'unidad'],
    extra=1, 
    can_delete=True, 
    max_num=None, # Permitir un número ilimitado de formularios
    min_num=0,    # Permitir 0 formularios si no hay ingredientes
    widgets={
        'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Harina'}),
        'cantidad': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 250 gramos / 2 tazas'}), 
        'unidad': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: gramos, tazas (opcional)'}), 
    }
)

# Formulario para agregar pasos a una receta
PasoFormSet = inlineformset_factory(
    Receta, 
    Paso, 
    fields=['titulo', 'descripcion'],
    extra=1, 
    can_delete=True, 
    max_num=None, # Permitir un número ilimitado de formularios
    min_num=0,    # Permitir 0 formularios si no hay pasos
    widgets={
        # CAMBIO AQUÍ: 'orden' se cambia a 'titulo' y es TextInput
        'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Preparación de la masa'}),
        'descripcion': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Describe este paso...'}),
    },
    labels={
        # CAMBIO AQUÍ: Etiqueta para el nuevo campo 'titulo'
        'titulo': 'Nombre del Paso',
    }
)

# Formulario para crear o editar una categoría
class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion'] 
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre de la Categoría'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Descripción de la categoría (opcional)'}), 
        }
        labels = {
            'nombre': 'Nombre de la Categoría',
            'descripcion': 'Descripción de la Categoría',
        }
