# usuarios/forms.py
from django import forms
from django.contrib.auth.models import User # Importamos el modelo User de Django
from django.contrib.auth.forms import UserCreationForm # ¡Importante: Importar UserCreationForm!
from .models import Perfil, CategoriaFavorita # Importamos nuestro modelo Perfil, categoría favorita y receta favorita

# Formulario de Registro Personalizado
class RegistroForm(UserCreationForm):
    email = forms.EmailField(label='Correo', required=True)
    first_name = forms.CharField(label='Nombre', required=True)
    last_name = forms.CharField(label='Apellido', required=True)
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

# Formulario para actualizar los campos del modelo User
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

# Formulario para actualizar los campos de nuestro modelo Perfil
class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['avatar', 'nickname', 'fecha_nacimiento']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

# Formulario para las preferencias de seguridad y notificaciones
class SeguridadPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = [
            'recibir_emails_recetas_nuevas',
            'recibir_emails_mensajes_privados',
            'permitir_mensajes_privados'
        ]

# Nuevo formulario para crear una categoría de favoritos
class CategoriaFavoritaForm(forms.ModelForm):
    class Meta:
        model = CategoriaFavorita
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre de la Categoría',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Postres, Cenas Rápidas'}),
        }