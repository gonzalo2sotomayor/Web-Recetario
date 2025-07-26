from django import forms
from .models import Comentario # Importar el modelo Comentario

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