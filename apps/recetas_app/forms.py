from django import forms
from django.forms import inlineformset_factory
from .models import Receta, Categoria, Comentario, Ingrediente, Paso, Mensaje

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
    fields=['titulo', 'descripcion'],
    extra=1, 
    can_delete=True, 
    widgets={
        'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Título del Paso'}),
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
        fields = ['nombre', 'fa_icon']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre de la Categoría'}),
            'fa_icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: fas fa-utensils'}),
        }
        labels = {
            'nombre': 'Nombre de la Categoría',
            'fa_icon': 'Clase de Ícono (Font Awesome)',
        }

# Formulario para enviar mensajes privados
class MensajeForm(forms.ModelForm):
    destinatario = forms.CharField(label="Destinatario", max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Nombre de usuario'}))
    
    class Meta:
        model = Mensaje
        fields = ['destinatario', 'asunto', 'cuerpo']
        widgets = {
            'asunto': forms.TextInput(attrs={'placeholder': 'Asunto del mensaje'}),
            'cuerpo': forms.Textarea(attrs={'placeholder': 'Escribe tu mensaje aquí...', 'rows': 5}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destinatario'].widget.attrs.update({'class': 'form-control'})
        self.fields['asunto'].widget.attrs.update({'class': 'form-control'})
        self.fields['cuerpo'].widget.attrs.update({'class': 'form-control'})
