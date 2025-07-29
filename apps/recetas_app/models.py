# blog-base/apps/recetas_app/models.py
from django.db import models
from django.contrib.auth.models import User # Importamos el modelo User de Django
from apps.usuarios.models import CategoriaFavorita 
from django.utils.text import slugify

#Modelo para las categorías de recetas
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True) 

    class Meta:
        verbose_name_plural = "Categorías"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Receta(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    # Cambiado related_name para ser consistente o dejarlo sin él si no se usa explícitamente
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recetas_creadas') 
    imagen = models.ImageField(upload_to='recetas_imagenes/', null=True, blank=True)
    tipo = models.CharField(max_length=50, blank=True, null=True) # Campo 'tipo' mantenido
    # Cambiado related_name para ser consistente o dejarlo como estaba si 'recetas_por_categoria' es preferido
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='recetas') 
    tiempo_preparacion = models.IntegerField(help_text="Tiempo en minutos", blank=True, null=True)
    porciones = models.IntegerField(help_text="Número de porciones", blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_publicacion'] # Re-añadido para ordenar recetas por fecha
        verbose_name_plural = "Recetas" # Re-añadido para nombre plural

    def __str__(self):
        return self.titulo

class Ingrediente(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='ingredientes')
    # ¡IMPORTANTE! Cambiado de DecimalField a CharField para permitir texto como "2 tazas"
    cantidad = models.CharField(max_length=50) 
    # Añadido blank=True, null=True para permitir unidades opcionales
    unidad = models.CharField(max_length=50, blank=True, null=True) 
    nombre = models.CharField(max_length=100) # Nombre movido al final para consistencia

    def __str__(self):
        # Ajustado para mostrar correctamente si la unidad es nula
        if self.unidad:
            return f"{self.cantidad} {self.unidad} de {self.nombre}"
        return f"{self.cantidad} de {self.nombre}"


class Paso(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='pasos')
    orden = models.PositiveIntegerField()
    descripcion = models.TextField()

    class Meta:
        ordering = ['orden'] # Asegura que los pasos se ordenen correctamente

    def __str__(self):
        return f"Paso {self.orden}: {self.descripcion[:50]}..." # Ajustado para mostrar una parte de la descripción

#Modelo de Comentario
class Comentario(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='comentarios')
    # Cambiado related_name para ser consistente o dejarlo como estaba si 'comentarios_hechos' es preferido
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mis_comentarios') 
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
    
# Modelo para las recetas favoritas de un usuario (mantenido como lo tenías)
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
