    from .models import Mensaje

    def unread_messages_count(request):
        if request.user.is_authenticated:
            count = Mensaje.objects.filter(destinatario=request.user, leido=False).count()
            return {'unread_messages_count': count}
        return {'unread_messages_count': 0}