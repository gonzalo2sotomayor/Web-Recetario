# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
    
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    recibir_emails_recetas_nuevas = models.BooleanField(default=True)
    recibir_emails_mensajes_privados = models.BooleanField(default=True)
    permitir_mensajes_privados = models.BooleanField(default=True)

    localidad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    acerca_de_mi = models.TextField(blank=True, null=True)
    
    mostrar_cumpleanos = models.BooleanField(default=True)
    mostrar_edad = models.BooleanField(default=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

    @property
    def edad(self):
        if self.fecha_nacimiento:
            import datetime
            today = datetime.date.today()
            age = today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
            return age
        return None

class CategoriaFavorita(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categorias_favoritas')
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Categoría de Favorito"
        verbose_name_plural = "Categorías de Favoritos"
        unique_together = ('user', 'nombre')

    def __str__(self):
        return f"{self.nombre} ({self.user.username})"
    
class Mensaje(models.Model):
    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_recibidos')
    asunto = models.CharField(max_length=200, blank=True)
    cuerpo = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_envio']
        verbose_name = "Mensaje Privado"
        verbose_name_plural = "Mensajes Privados"

    def __str__(self):
        return f"De: {self.remitente.username} a: {self.destinatario.username} - Asunto: {self.asunto[:50]}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
    else:
        Perfil.objects.create(user=instance)
    