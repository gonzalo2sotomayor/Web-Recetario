# blog-base/apps/recetas_app/models.py
from django.db import models
from django.contrib.auth.models import User # Importamos el modelo User de Django
from apps.usuarios.models import CategoriaFavorita

#Modelo para las categorías de recetas
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Categoría de Receta"
        verbose_name_plural = "Categorías de Recetas"

    def __str__(self):
        return self.nombre

class Receta(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='recetas_imagenes/', null=True, blank=True)
    tipo = models.CharField(max_length=50, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='recetas_por_categoria')

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
    
# Modelo para las recetas favoritas de un usuario
class RecetaFavorita(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recetas_favoritas')
    receta = models.ForeignKey('Receta', on_delete=models.CASCADE) # Relación con el modelo Receta
    categoria = models.ForeignKey(
        'usuarios.CategoriaFavorita', # Referencia de cadena, ya que CategoriaFavorita está en usuarios
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recetas'
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Receta Favorita"
        verbose_name_plural = "Recetas Favoritas"
        unique_together = ('user', 'receta')

    def __str__(self):
        return f"{self.receta.titulo} - {self.user.username}"
