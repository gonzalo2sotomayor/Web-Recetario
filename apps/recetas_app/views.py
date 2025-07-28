from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse # Importar HttpResponse si se usa para depuración o respuestas simples
from django.contrib.auth.decorators import login_required
from .models import Receta, Ingrediente, Paso, Comentario # Importar Comentario
from .forms import ComentarioForm # Importar ComentarioForm
import random

# Vista para la página de inicio (Home)
def home(request):
    """
    Renderiza la página de inicio del blog de recetas, mostrando todas las recetas.
    """
    recetas = Receta.objects.all() # Obtener todas las recetas de la base de datos
    return render(request, 'recetas_app/home.html', {'recetas': recetas})

# Vista para el detalle de una receta específica
def detalle_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)
    
    # Obtener todos los comentarios de nivel superior para esta receta
    # Los comentarios de nivel superior son aquellos que no son respuestas a otros comentarios
    comentarios_principales = Comentario.objects.filter(
        receta=receta,
        respuesta_a__isnull=True
    ).order_by('fecha_creacion')

    if request.method == 'POST':
        # Asegurarse de que el usuario esté autenticado para comentar
        if not request.user.is_authenticated:
            # Puedes redirigir a la página de login o mostrar un mensaje
            return redirect('usuarios:login') # Redirigir al login si no está autenticado

        form = ComentarioForm(request.POST)
        if form.is_valid():
            nuevo_comentario = form.save(commit=False)
            nuevo_comentario.receta = receta
            nuevo_comentario.autor = request.user
            nuevo_comentario.save()
            # Si es una respuesta, el campo 'respuesta_a' ya debería venir en el POST
            # Puedes añadir un mensaje de éxito aquí si lo deseas
            return redirect('recetas_app:detalle_receta', pk=receta.pk) # Redirigir para evitar reenvío del formulario
    else:
        form = ComentarioForm() # Formulario vacío para GET request

    # Verificar si la receta es favorita para el usuario actual (para el botón)
    es_favorita = False
    if request.user.is_authenticated:
        es_favorita = request.user.recetas_favoritas.filter(receta=receta).exists()

    context = {
        'receta': receta,
        'comentarios_principales': comentarios_principales,
        'form': form, # Pasar el formulario al contexto
        'es_favorita': es_favorita, # Pasar si es favorita para el template
    }
    return render(request, 'recetas_app/detalle_receta.html', context)

# Vista: Receta al azar (Descubre)
def recetas_aleatorias(request):
    # Obtener un ID de receta al azar
    recetas_ids = list(Receta.objects.values_list('id', flat=True))
    if recetas_ids:
        random_id = random.choice(recetas_ids)
        return redirect('recetas_app:detalle_receta', pk=random_id)
    else:
        return redirect('recetas_app:home') # O a una página de "no hay recetas"

# Vista para el formulario de búsqueda avanzada (placeholder)
def advanced_search_view(request):
    # Aquí irá el formulario de búsqueda avanzada
    return render(request, 'recetas_app/advanced_search.html', {})

# Vista para procesar los resultados de la búsqueda avanzada (placeholder)
def advanced_search_results_view(request):
    # Aquí irá la lógica para mostrar los resultados de la búsqueda avanzada
    return render(request, 'recetas_app/advanced_search_results.html', {})

# Vista para la búsqueda simple (desde la barra de navegación principal)
def simple_search_view(request):
    """
    Maneja la búsqueda simple desde la barra de navegación.
    Recupera el término de búsqueda y muestra una página de resultados.
    """
    query = request.GET.get('q', '').strip() # Obtiene el parámetro 'q' de la URL y limpia espacios
    
    results = []
    if query:
        # Se puede ajustar los campos a buscar según el modelo Receta.
        from django.db.models import Q
        results = Receta.objects.filter(
            Q(titulo__icontains=query) | Q(descripcion__icontains=query) | Q(ingredientes__icontains=query)
        ).distinct()

        if not results:
            # Si no se encuentran resultados reales, manejarlo aquí
            pass # No es necesario añadir un mensaje "No se encontraron resultados" aquí, el template lo manejará
                 # basándose en si 'results' está vacío.

    context = {
        'query': query,
        'results': results, # Pasa los resultados reales del ORM
        'search_type': 'simple'
    }
    return render(request, 'recetas_app/search_results.html', context)

# Vista para mostrar el formulario de búsqueda avanzada
def advanced_search_view(request):
    """
    Renderiza la página del formulario de búsqueda avanzada.
    """
    return render(request, 'recetas_app/advanced_search.html', {})

# Vista para procesar los resultados de la búsqueda avanzada
def advanced_search_results_view(request):
    """
    Procesa los parámetros del formulario de búsqueda avanzada y muestra los resultados.
    """
    exact_phrase = request.GET.get('exact_phrase', '').strip()
    similar_words = request.GET.get('similar_words', '').strip()
    ingredient = request.GET.get('ingredient', '').strip()
    recipe_type = request.GET.get('recipe_type', '').strip()

    # Imprimir los parámetros recibidos para depuración (se verán en la consola del servidor)
    print(f"Búsqueda Avanzada Recibida:")
    print(f"  Frase Exacta: '{exact_phrase}'")
    print(f"  Palabras Similares: '{similar_words}'")
    print(f"  Ingrediente: '{ingredient}'")
    print(f"  Tipo de Receta: '{recipe_type}'")

    # --- Lógica REAL para consultar la base de datos usando el ORM ---
    # Inicia con todas las recetas y aplica filtros condicionalmente
    queryset = Receta.objects.all()

    if exact_phrase:
        # Busca la frase exacta en el título o descripción
        queryset = queryset.filter(titulo__icontains=exact_phrase) 
        from django.db.models import Q
        queryset = queryset.filter(Q(titulo__icontains=exact_phrase) | Q(descripcion__icontains=exact_phrase))

    if similar_words:
        # Divide las palabras y busca cualquiera de ellas
        words = similar_words.split()
        q_objects = Q()
        for word in words:
            q_objects |= Q(titulo__icontains=word) 
            q_objects |= Q(descripcion__icontains=word)
            q_objects |= Q(ingredientes__icontains=word) 
        queryset = queryset.filter(q_objects)

    if ingredient:
        # Campo de ingredientes en modelo Receta
        queryset = queryset.filter(ingredientes__icontains=ingredient)
    
    if recipe_type:
        # Campo 'tipo' en modelo Receta
        queryset = queryset.filter(tipo=recipe_type) # Asume que el tipo se guarda tal cual en la DB

    results = queryset.distinct() # Asegura resultados únicos

    
    context = {
        'exact_phrase': exact_phrase,
        'similar_words': similar_words,
        'ingredient': ingredient,
        'recipe_type': recipe_type,
        'results': results, # Pasa los resultados reales del ORM
        'search_type': 'advanced'
    }
    return render(request, 'recetas_app/search_results.html', context)