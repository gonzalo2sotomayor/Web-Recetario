# blog-base/apps/usuarios/context_processors.py

from django.apps import apps # Importar apps

def unread_messages_count(request):
    # Solo si el usuario está autenticado, intentamos obtener el conteo de mensajes
    if request.user.is_authenticated:
        try:
            # Usamos apps.get_model para cargar los modelos de forma segura.
            # Esto asegura que el registro de aplicaciones esté listo.
            Perfil = apps.get_model('usuarios', 'Perfil')
            Mensaje = apps.get_model('usuarios', 'Mensaje')

            # Intentar obtener el perfil del usuario.
            # Usamos .first() para evitar un error si no hay perfil (aunque debería haberlo)
            # y para no lanzar un DoesNotExist si no se encuentra.
            perfil = Perfil.objects.filter(user=request.user).first()

            if perfil:
                # Contar mensajes no leídos dirigidos a este perfil
                unread_count = Mensaje.objects.filter(
                    destinatario=perfil,
                    leido=False
                ).count()
                return {'unread_messages_count': unread_count}
            else:
                # Si no hay perfil, el conteo es 0
                return {'unread_messages_count': 0}
        except Exception as e:
            # En caso de cualquier error 
            # devolvemos 0 para evitar que la página falle.
            print(f"Error en unread_messages_count context processor: {e}")
            return {'unread_messages_count': 0}
    # Si el usuario no está autenticado, no hay mensajes no leídos para él
    return {'unread_messages_count': 0}
