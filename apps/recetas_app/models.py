from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify

# Modelo para Categorías de Recetas
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Título de la Categoría") # Renombrado para la UI
    descripcion = models.TextField(blank=True)
    slug = models.SlugField(unique=True, max_length=100, blank=True, help_text="Se generará automáticamente a partir del título.")
    imagen = models.ImageField(upload_to='categorias_imagenes/', blank=True, null=True, verbose_name="Imagen de la Categoría") # Nuevo campo

    class Meta:
        verbose_name_plural = "Categorías" # Nombre para el admin
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

# Modelo para Recetas
class Receta(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='recetas_imagenes/', blank=True, null=True)
    fecha_publicacion = models.DateTimeField(default=timezone.now)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recetas_creadas')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='recetas')
    tiempo_preparacion = models.IntegerField(help_text="En minutos", blank=True, null=True)
    porciones = models.IntegerField(blank=True, null=True)
    is_featured = models.BooleanField(default=False, verbose_name="¿Receta de la Semana?")

    class Meta:
        ordering = ['-fecha_publicacion'] # Ordenar por fecha de publicación descendente
        verbose_name_plural = "Recetas"

    def __str__(self):
        return self.titulo

# Modelo para Ingredientes de una Receta
class Ingrediente(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='ingredientes')
    nombre = models.CharField(max_length=100)
    cantidad = models.CharField(max_length=50) # Cambiado a CharField para permitir "2 tazas", "un puñado", etc.
    unidad = models.CharField(max_length=50, blank=True, null=True) # Ej: gramos, ml, tazas, unidades

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = "Ingredientes"

    def __str__(self):
        return f"{self.cantidad} {self.unidad or ''} de {self.nombre} ({self.receta.titulo[:20]}...)"

# Modelo para Pasos de una Receta
class Paso(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='pasos')
    titulo = models.CharField(max_length=200, help_text="Ej: Preparación de la salsa, Cocción de la pasta")
    descripcion = models.TextField()

    class Meta:
        ordering = ['id'] # Mantiene el orden de creación si no hay un campo de orden explícito
        verbose_name_plural = "Pasos"

    def __str__(self):
        return f"{self.titulo} ({self.receta.titulo[:20]}...)"

# Modelo para Comentarios en Recetas
class Comentario(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_hechos')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(default=timezone.now)
    # Para respuestas a comentarios
    respuesta_a = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='respuestas')

    class Meta:
        ordering = ['fecha_creacion']
        verbose_name_plural = "Comentarios"

    def __str__(self):
        return f'Comentario de {self.autor.username} en {self.receta.titulo}'

# Modelo para Recetas Favoritas de Usuarios
class RecetaFavorita(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recetas_favoritas')
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('usuario', 'receta') # Un usuario solo puede tener una receta como favorita una vez
        verbose_name_plural = "Recetas Favoritas"

    def __str__(self):
        return f'{self.usuario.username} - {self.receta.titulo}'

# Modelo para Mensajes Privados
class Mensaje(models.Model):
    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados_recetas')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_recibidos_recetas')
    asunto = models.CharField(max_length=255)
    cuerpo = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    is_leido = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_envio']
        verbose_name = "Mensaje Privado"
        verbose_name_plural = "Mensajes Privados"

    def __str__(self):
        return f'De: {self.remitente} - Para: {self.destinatario} - Asunto: {self.asunto}'
