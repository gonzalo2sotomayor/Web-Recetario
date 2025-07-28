from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse # Importar HttpResponse si se usa para depuración o respuestas simples
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
from django.db import transaction
from django.db.models import Q 
import random

# Importaciones consolidadas de modelos y formularios
from .models import Receta, Ingrediente, Paso, Comentario
from .forms import ComentarioForm, RecetaForm, IngredienteFormSet, PasoFormSet

# Función para verificar si el usuario es administrador (is_staff)
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Vista para la página de inicio (Home)
def home(request):
    recetas = Receta.objects.all()
    return render(request, 'recetas_app/home.html', {'recetas': recetas})

# Vista para el detalle de una receta específica
def detalle_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)
    
    comentarios_principales = Comentario.objects.filter(
        receta=receta,
        respuesta_a__isnull=True
    ).order_by('fecha_creacion')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('usuarios:login')

        form = ComentarioForm(request.POST)
        if form.is_valid():
            nuevo_comentario = form.save(commit=False)
            nuevo_comentario.receta = receta
            nuevo_comentario.autor = request.user
            nuevo_comentario.save()
            return redirect('recetas_app:detalle_receta', pk=receta.pk)
    else:
        form = ComentarioForm()

    es_favorita = False
    if request.user.is_authenticated:
        es_favorita = request.user.recetas_favoritas.filter(receta=receta).exists()

    context = {
        'receta': receta,
        'comentarios_principales': comentarios_principales,
        'form': form,
        'es_favorita': es_favorita,
    }
    return render(request, 'recetas_app/detalle_receta.html', context)

# Vista: Receta al azar (Descubre)
def recetas_aleatorias(request):
    recetas_ids = list(Receta.objects.values_list('id', flat=True))
    if recetas_ids:
        random_id = random.choice(recetas_ids)
        return redirect('recetas_app:detalle_receta', pk=random_id)
    else:
        return redirect('recetas_app:home')

# Vista para la búsqueda simple
def simple_search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = Receta.objects.filter(
            Q(titulo__icontains=query) | Q(descripcion__icontains=query)
        ).distinct()
    context = {
        'query': query,
        'results': results,
        'search_type': 'simple'
    }
    return render(request, 'recetas_app/search_results.html', context)

# Vista para el formulario de búsqueda avanzada
def advanced_search_view(request):
    return render(request, 'recetas_app/advanced_search.html', {})

# Vista para procesar los resultados de la búsqueda avanzada
def advanced_search_results_view(request):
    exact_phrase = request.GET.get('exact_phrase', '').strip()
    similar_words = request.GET.get('similar_words', '').strip()
    ingredient = request.GET.get('ingredient', '').strip()
    recipe_type = request.GET.get('recipe_type', '').strip()

    queryset = Receta.objects.all()

    if exact_phrase:
        queryset = queryset.filter(Q(titulo__icontains=exact_phrase) | Q(descripcion__icontains=exact_phrase))

    if similar_words:
        words = similar_words.split()
        q_objects = Q()
        for word in words:
            q_objects |= Q(titulo__icontains=word)
            q_objects |= Q(descripcion__icontains=word)
            q_objects |= Q(ingredientes__nombre__icontains=word)
        queryset = queryset.filter(q_objects)

    if ingredient:
        queryset = queryset.filter(ingredientes__nombre__icontains=ingredient)
    
    # if recipe_type:
    #     queryset = queryset.filter(tipo=recipe_type)

    results = queryset.distinct()

    context = {
        'exact_phrase': exact_phrase,
        'similar_words': similar_words,
        'ingredient': ingredient,
        # 'recipe_type': recipe_type,
        'results': results,
        'search_type': 'advanced'
    }
    return render(request, 'recetas_app/search_results.html', context)


# Vista: Crear Receta (solo para administradores/staff)
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def crear_receta(request):
    if request.method == 'POST':
        receta_form = RecetaForm(request.POST, request.FILES)
        ingrediente_formset = IngredienteFormSet(request.POST, prefix='ingredientes')
        paso_formset = PasoFormSet(request.POST, prefix='pasos')

        if receta_form.is_valid() and ingrediente_formset.is_valid() and paso_formset.is_valid():
            try:
                with transaction.atomic():
                    receta = receta_form.save(commit=False)
                    receta.autor = request.user
                    receta.save()

                    ingrediente_formset.instance = receta
                    ingrediente_formset.save()

                    paso_formset.instance = receta
                    paso_formset.save()

                return redirect('recetas_app:detalle_receta', pk=receta.pk)

            except Exception as e:
                print(f"Error al crear receta: {e}")
    else:
        receta_form = RecetaForm()
        ingrediente_formset = IngredienteFormSet(prefix='ingredientes')
        paso_formset = PasoFormSet(prefix='pasos')

    context = {
        'receta_form': receta_form,
        'ingrediente_formset': ingrediente_formset,
        'paso_formset': paso_formset,
    }
    return render(request, 'recetas_app/crear_receta.html', context)