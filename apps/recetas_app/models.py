from django.db import models
from django.contrib.auth.models import User # Importamos el modelo User de Django

class Receta(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='recetas_imagenes/', null=True, blank=True)

    def __str__(self):
        return self.titulo

class Ingrediente(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='ingredientes')
    nombre = models.CharField(max_length=100)
    cantidad = models.DecimalField(max_digits=5, decimal_places=2)
    unidad = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.cantidad} {self.unidad} de {self.nombre}"

class Paso(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='pasos')
    orden = models.PositiveIntegerField()
    descripcion = models.TextField()

    class Meta:
        ordering = ['orden'] # Asegura que los pasos se ordenen correctamente

    def __str__(self):
        return f"Paso {self.orden} de {self.receta.titulo}"

#Modelo de Comentario
class Comentario(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_hechos')
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # Campo opcional para respuestas a comentarios (comentarios anidados)
    respuesta_a = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='respuestas'
    )

    class Meta:
        ordering = ['fecha_creacion'] # Ordenar comentarios por fecha

    def __str__(self):
        return f'Comentario de {self.autor.username} en {self.receta.titulo}'