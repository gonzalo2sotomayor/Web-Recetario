# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User # Importamos el modelo User de Django
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.recetas_app.models import Receta

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    recibir_emails_recetas_nuevas = models.BooleanField(default=True)
    recibir_emails_mensajes_privados = models.BooleanField(default=True)
    permitir_mensajes_privados = models.BooleanField(default=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

# Modelo para las categorías personalizadas de recetas favoritas
class CategoriaFavorita(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categorias_favoritas')
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Categoría de Favorito"
        verbose_name_plural = "Categorías de Favoritos"
        unique_together = ('user', 'nombre') # Un usuario no puede tener dos categorías con el mismo nombre

    def __str__(self):
        return f"{self.nombre} ({self.user.username})"

# Modelo para las recetas favoritas de un usuario
class RecetaFavorita(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recetas_favoritas')
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    categoria = models.ForeignKey(
        CategoriaFavorita,
        on_delete=models.SET_NULL, # Si la categoría se elimina, la receta favorita no se elimina, solo se queda sin categoría
        null=True,
        blank=True,
        related_name='recetas'
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Receta Favorita"
        verbose_name_plural = "Recetas Favoritas"
        unique_together = ('user', 'receta') # Un usuario no puede tener la misma receta favorita dos veces

    def __str__(self):
        return f"{self.receta.titulo} - {self.user.username}"

# Señales para crear y guardar el perfil automáticamente cuando se crea un usuario
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.perfil.save()
