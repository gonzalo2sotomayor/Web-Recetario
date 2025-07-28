# usuarios/forms.py
from django import forms
from django.contrib.auth.models import User # Importamos el modelo User de Django
from django.contrib.auth.forms import UserCreationForm 
from .models import Perfil, CategoriaFavorita, Mensaje 

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
        fields = [
            'avatar',
            'nickname',
            'fecha_nacimiento',
            'localidad', 
            'pais',     
            'acerca_de_mi',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'acerca_de_mi': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Cuéntanos algo sobre ti...'}), # Widget para textarea
        }

# Formulario para las preferencias de seguridad y notificaciones
class SeguridadPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = [
            'recibir_emails_recetas_nuevas',
            'recibir_emails_mensajes_privados',
            'permitir_mensajes_privados',
            'mostrar_cumpleanos', 
            'mostrar_edad',       
        ]

#Formulario para crear una categoría de favoritos
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

#Formulario para enviar mensajes privados
class MensajeForm(forms.ModelForm):
    # Campo para seleccionar el destinatario. Excluye al usuario actual.
    # Se llenará en la vista para filtrar por usuarios válidos.
    destinatario = forms.ModelChoiceField(
        queryset=User.objects.all(), # Se ajustará en la vista
        label='Para',
        empty_label="Selecciona un usuario"
    )

    class Meta:
        model = Mensaje
        fields = ['destinatario', 'asunto', 'cuerpo']
        widgets = {
            'asunto': forms.TextInput(attrs={'placeholder': 'Asunto del mensaje'}),
            'cuerpo': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Escribe tu mensaje aquí...'}),
        }
        labels = {
            'asunto': 'Asunto',
            'cuerpo': 'Mensaje',
        }

    def __init__(self, *args, **kwargs):
        # El 'sender_user' se pasa desde la vista para excluirlo de la lista de destinatarios
        sender_user = kwargs.pop('sender_user', None)
        super().__init__(*args, **kwargs)
        if sender_user:
            # Asegura que el usuario no pueda enviarse mensajes a sí mismo
            self.fields['destinatario'].queryset = User.objects.exclude(id=sender_user.id)        