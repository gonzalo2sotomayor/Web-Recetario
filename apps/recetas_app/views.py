# apps/recetas_app/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
from django.db import transaction
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 
import random
from django.utils.text import slugify
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils import timezone
from urllib.parse import urlencode 
from django.contrib.auth.models import User
from django.template.loader import render_to_string 

# Importaciones consolidadas de modelos y formularios
from .models import Receta, Ingrediente, Paso, Comentario, Categoria, RecetaFavorita 
# Importamos los Formsets y formularios 
from .forms import ComentarioForm, ComentarioEditForm, RecetaForm, IngredienteFormSet, PasoFormSet, CategoriaForm


# Función para verificar si el usuario es administrador (is_staff)
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Vista para la página de inicio (Home)
def home(request):
    """
    Vista de la página de inicio que muestra las últimas recetas.
    Permite filtrar por categoría y ordenar.
    """
    # Obtener todas las categorías para la sidebar
    categorias = Categoria.objects.all().order_by('nombre')

    # Filtrado por categoría
    filtro_categoria_aplicado = False
    categoria_encontrada = True
    categoria_nombre = None
    recetas_list = Receta.objects.all() # Inicializar con todas las recetas

    categoria_slug = request.GET.get('categoria')
    if categoria_slug:
        filtro_categoria_aplicado = True
        try:
            categoria_seleccionada = Categoria.objects.get(slug=categoria_slug)
            recetas_list = recetas_list.filter(categoria=categoria_seleccionada)
            categoria_nombre = categoria_seleccionada.nombre
        except Categoria.DoesNotExist:
            recetas_list = Receta.objects.none() # No hay recetas si la categoría no existe
            categoria_encontrada = False

    # --- Lógica de Ordenamiento ---
    order_by = request.GET.get('order_by', 'fecha_publicacion') # Por defecto, ordenar por fecha de publicación
    direction = request.GET.get('direction', 'desc') # Por defecto, descendente

    if order_by == 'fecha_publicacion':
        if direction == 'asc':
            recetas_list = recetas_list.order_by('fecha_publicacion')
        else: 
            recetas_list = recetas_list.order_by('-fecha_publicacion')
    elif order_by == 'titulo':
        if direction == 'asc':
            recetas_list = recetas_list.order_by('titulo')
        else: 
            recetas_list = recetas_list.order_by('-titulo')

    # --- Obtener la Receta de la Semana ---
    receta_de_la_semana = Receta.objects.order_by('?').first() # Receta aleatoria

    # --- Obtener Recetas Más Populares (para la sección de la página de inicio) ---
    recetas_populares_home = Receta.objects.annotate(
        num_favoritos=Count('recetafavorita')
    ).order_by('-num_favoritos')[:6] # Limitar a, por ejemplo, las 6 más populares para la home

    # --- Obtener los IDs de las recetas favoritas del usuario actual ---
    favoritas_ids = set()
    if request.user.is_authenticated:
        # Usamos .values_list('receta__pk', flat=True) para obtener una lista plana de IDs
        favoritas_ids = set(request.user.recetas_favoritas.values_list('receta__pk', flat=True))

    context = {
        'recetas': recetas_list,
        'categorias': categorias,
        'filtro_categoria_aplicado': filtro_categoria_aplicado,
        'categoria_encontrada': categoria_encontrada,
        'categoria_nombre': categoria_nombre,
        'current_order_by': order_by,
        'current_direction': direction,
        'receta_de_la_semana': receta_de_la_semana,
        'recetas_populares': recetas_populares_home, 
        'favoritas_ids': favoritas_ids, # ¡Pasamos los IDs de las recetas favoritas!
    }

    # Detectar si la petición es AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Si es AJAX, renderizar solo la cuadrícula de recetas
        html = render_to_string('recetas_app/partials/latest_recipes_grid.html', context, request=request)
        return JsonResponse({'html': html}) # Devolver JSON con el HTML parcial

    return render(request, 'recetas_app/home.html', context)


# --- VISTA: Recetas Populares (Página dedicada con paginación) ---
def recetas_populares_page(request):
    # Obtener todas las recetas, anotarlas con el número de favoritos
    # y ordenarlas de forma descendente.
    all_recetas_populares = Receta.objects.annotate(
        num_favoritos=Count('recetafavorita')
    ).order_by('-num_favoritos')

    # Configurar la paginación
    paginator = Paginator(all_recetas_populares, 12) # Mostrar 12 recetas por página
    page_number = request.GET.get('page') # Obtener el número de página de la URL

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Si el parámetro de página no es un entero, entregar la primera página.
        page_obj = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango (ej. 9999), entregar la última página de resultados.
        page_obj = paginator.page(paginator.num_pages)

    # Obtener los IDs de las recetas favoritas del usuario actual para los iconos
    favoritas_ids = set()
    if request.user.is_authenticated:
        favoritas_ids = set(request.user.recetas_favoritas.values_list('receta__pk', flat=True))

    context = {
        'recetas_populares': page_obj, 
        'page_obj': page_obj, 
        'favoritas_ids': favoritas_ids, # Pasamos los IDs de las recetas favoritas
    }
    return render(request, 'recetas_app/recetas_populares.html', context)


# Vista para el detalle de una receta específica
def detalle_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)

    comentarios_principales = Comentario.objects.filter(
        receta=receta,
        respuesta_a__isnull=True
    ).order_by('fecha_creacion')

    if request.method == 'POST':
        # Manejar el envío del formulario de comentario
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para dejar un comentario.')
            # Redirige a la página de login, con 'next' para volver aquí después del login
            return redirect(f"{reverse_lazy('usuarios:login')}?next={request.path}")

        form = ComentarioForm(request.POST)
        if form.is_valid():
            nuevo_comentario = form.save(commit=False)
            nuevo_comentario.receta = receta
            nuevo_comentario.autor = request.user
            
            respuesta_a_id = request.POST.get('respuesta_a')
            if respuesta_a_id:
                try:
                    nuevo_comentario.respuesta_a = Comentario.objects.get(pk=respuesta_a_id)
                except Comentario.DoesNotExist:
                    messages.error(request, 'El comentario al que intentas responder no existe.')
                    return redirect('recetas_app:detalle_receta', pk=receta.pk)
            
            nuevo_comentario.save()
            messages.success(request, '¡Comentario publicado exitosamente!')
            return redirect('recetas_app:detalle_receta', pk=receta.pk)
        else:
            messages.error(request, 'Hubo un error al publicar tu comentario.')
    else:
        form = ComentarioForm()

    es_favorita = False
    if request.user.is_authenticated:
        es_favorita = request.user.recetas_favoritas.filter(receta=receta).exists()

    context = {
        'receta': receta,
        'comentarios_principales': comentarios_principales,
        'form': form,
        'es_favorita': es_favorita, # Pasamos esta variable al contexto
    }
    return render(request, 'recetas_app/detalle_receta.html', context)

# Vista: Receta al azar (Descubre)
def recetas_aleatorias(request):
    recetas_ids = list(Receta.objects.values_list('id', flat=True))
    if recetas_ids:
        random_id = random.choice(recetas_ids)
        return redirect('recetas_app:detalle_receta', pk=random_id)
    else:
        messages.info(request, 'No hay recetas disponibles para descubrir.')
        return redirect('recetas_app:home')

# Vista para la búsqueda simple
def simple_search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    # --- Construir base_query_params en la vista ---
    base_query_params = {}
    if query:
        results = Receta.objects.filter(
            Q(titulo__icontains=query) | Q(descripcion__icontains=query)
        ).distinct()
        base_query_params['q'] = query
    
    # Convertir el diccionario a una cadena de consulta URL-encoded
    base_query_string = urlencode(base_query_params)

    # --- Lógica de Ordenamiento ---
    order_by = request.GET.get('order_by', 'fecha_publicacion')
    direction = request.GET.get('direction', 'desc')

    if order_by == 'fecha_publicacion':
        if direction == 'asc':
            results = results.order_by('fecha_publicacion')
        else: 
            results = results.order_by('-fecha_publicacion')
    elif order_by == 'titulo':
        if direction == 'asc':
            results = results.order_by('titulo')
        else: 
            results = results.order_by('-titulo')
    
    # Obtener los IDs de las recetas favoritas del usuario actual para los iconos
    favoritas_ids = set()
    if request.user.is_authenticated:
        favoritas_ids = set(request.user.recetas_favoritas.values_list('receta__pk', flat=True))

    context = {
        'query': query,
        'results': results,
        'search_type': 'simple',
        'current_order_by': order_by,
        'current_direction': direction,
        'base_query_string': base_query_string, 
        'favoritas_ids': favoritas_ids, # Pasamos los IDs de las recetas favoritas
    }
    return render(request, 'recetas_app/search_results.html', context)


# VISTA CORREGIDA Y CONSOLIDADA para la Búsqueda Avanzada
def advanced_search_view(request):
    """
    Vista unificada para mostrar el formulario de búsqueda avanzada y
    procesar los resultados en la misma página.
    """
    categorias = Categoria.objects.all()
    queryset = Receta.objects.all()
    
    # Obtener parámetros de la URL. Son los nombres de los campos del formulario.
    exact_phrase = request.GET.get('exact_phrase', '').strip()
    similar_words = request.GET.get('similar_words', '').strip()
    ingredient = request.GET.get('ingredient', '').strip()
    category_slug = request.GET.get('category', '').strip()
    
    # Iniciar Q-objects para combinar filtros de forma dinámica
    # con el operador OR (|).
    main_q_filter = Q()

    # 1. Búsqueda por palabras similares (en título, descripción o ingredientes)
    if similar_words:
        words = similar_words.split()
        for word in words:
            main_q_filter |= Q(titulo__icontains=word)
            main_q_filter |= Q(descripcion__icontains=word)
            # 'ingredientes' es la relación ManyToMany, el filtro funciona correctamente
            main_q_filter |= Q(ingredientes__nombre__icontains=word)
            
    # 2. Búsqueda por frase exacta
    if exact_phrase:
        # Se combina con el filtro anterior usando AND (&)
        exact_q_filter = Q(titulo__icontains=exact_phrase) | Q(descripcion__icontains=exact_phrase)
        if main_q_filter:
            queryset = queryset.filter(main_q_filter & exact_q_filter)
        else:
            queryset = queryset.filter(exact_q_filter)
    elif main_q_filter:
        queryset = queryset.filter(main_q_filter)
    
    # 3. Filtrado por ingrediente. Esto actúa como un filtro AND adicional.
    if ingredient:
        queryset = queryset.filter(ingredientes__nombre__icontains=ingredient)
        
    # 4. Filtrado por categoría. También es un filtro AND.
    selected_category_obj = None
    if category_slug:
        try:
            selected_category_obj = Categoria.objects.get(slug=category_slug)
            queryset = queryset.filter(categoria=selected_category_obj)
        except Categoria.DoesNotExist:
            pass # Si la categoría no existe, no se filtra

    # Eliminar duplicados si una receta coincide con varios criterios
    # y ordenar los resultados
    recetas = queryset.distinct().order_by('-fecha_publicacion')

    # Obtener los IDs de las recetas favoritas del usuario actual
    favoritas_ids = set()
    if request.user.is_authenticated:
        favoritas_ids = set(request.user.recetas_favoritas.values_list('receta__pk', flat=True))

    context = {
        'recetas': recetas,
        'categories': categorias,
        'selected_category': category_slug,
        'favoritas_ids': favoritas_ids,
        # Mantener los valores de los campos de búsqueda para que no se pierdan
        'exact_phrase': exact_phrase,
        'similar_words': similar_words,
        'ingredient': ingredient,
    }
    
    return render(request, 'recetas_app/advanced_search.html', context)

# Se elimina la vista 'advanced_search_results_view' ya que está consolidada en 'advanced_search_view'

# Vista: Crear Receta (solo para administradores/staff)
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def crear_receta(request):
    receta_form = RecetaForm()
    ingrediente_formset = IngredienteFormSet(prefix='ingredientes')
    paso_formset = PasoFormSet(prefix='pasos')

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

                messages.success(request, '¡Receta creada exitosamente!')
                return redirect('recetas_app:detalle_receta', pk=receta.pk)

            except Exception as e:
                messages.error(request, f"Error al crear receta: {e}")
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')

    context = {
        'form': receta_form,
        'formset_ingredientes': ingrediente_formset,
        'formset_pasos': paso_formset,
    }
    return render(request, 'recetas_app/crear_receta.html', context)


# Vista: Editar Receta (solo para administradores/staff)
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def editar_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)
    # Solo el autor o un superusuario puede editar la receta
    if not (request.user == receta.autor or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para editar esta receta.')
        return redirect('recetas_app:detalle_receta', pk=receta.pk)

    if request.method == 'POST':
        receta_form = RecetaForm(request.POST, request.FILES, instance=receta)
        ingrediente_formset = IngredienteFormSet(request.POST, instance=receta, prefix='ingredientes')
        paso_formset = PasoFormSet(request.POST, instance=receta, prefix='pasos')

        if receta_form.is_valid() and ingrediente_formset.is_valid() and paso_formset.is_valid():
            try:
                with transaction.atomic():
                    receta = receta_form.save()

                    ingrediente_formset.save()
                    paso_formset.save()

                messages.success(request, '¡Receta actualizada exitosamente!')
                return redirect('recetas_app:detalle_receta', pk=receta.pk)

            except Exception as e:
                messages.error(request, f"Error al editar receta: {e}")
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        receta_form = RecetaForm(instance=receta)
        ingrediente_formset = IngredienteFormSet(instance=receta, prefix='ingredientes')
        paso_formset = PasoFormSet(instance=receta, prefix='pasos')

    context = {
        'form': receta_form,
        'formset_ingredientes': ingrediente_formset,
        'formset_pasos': paso_formset,
        'receta': receta,
    }
    return render(request, 'recetas_app/editar_receta.html', context)


# Vista para eliminar una receta (solo para administradores/staff)
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def eliminar_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)
    # Solo el autor o un superusuario puede eliminar la receta
    if not (request.user == receta.autor or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para eliminar esta receta.')
        return redirect('recetas_app:detalle_receta', pk=receta.pk)

    if request.method == 'POST':
        receta.delete()
        messages.success(request, 'Receta eliminada exitosamente.')
        return redirect('recetas_app:home')
    context = {
        'receta': receta
    }
    return render(request, 'recetas_app/receta_confirm_delete.html', context)


#   Editar Comentario
@login_required
def editar_comentario(request, pk):
    comentario = get_object_or_404(Comentario, pk=pk)
    # Asegurarse de que solo el autor pueda editar su comentario
    if comentario.autor != request.user:
        messages.error(request, 'No tienes permiso para editar este comentario.')
        return redirect('recetas_app:detalle_receta', pk=comentario.receta.pk)

    if request.method == 'POST':
        form = ComentarioEditForm(request.POST, instance=comentario)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Comentario actualizado exitosamente!')
            return redirect('recetas_app:detalle_receta', pk=comentario.receta.pk)
        else:
            messages.error(request, 'Hubo un error al actualizar el comentario.')
    else:
        form = ComentarioEditForm(instance=comentario)

    context = {
        'form': form,
        'comentario': comentario,
        'receta': comentario.receta, # Para poder volver a la receta
    }
    return render(request, 'recetas_app/editar_comentario.html', context)


#   Eliminar Comentario
@login_required
def eliminar_comentario(request, pk):
    comentario = get_object_or_404(Comentario, pk=pk)
    # Solo el autor o un superusuario puede eliminar el comentario
    if not (request.user == comentario.autor or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para eliminar este comentario.')
        return redirect('recetas_app:detalle_receta', pk=comentario.receta.pk)

    if request.method == 'POST':
        receta_pk = comentario.receta.pk 
        comentario.delete()
        messages.success(request, 'Comentario eliminado exitosamente.')
        return redirect('recetas_app:detalle_receta', pk=receta_pk)
    
    context = {
        'comentario': comentario,
        'receta': comentario.receta, 
    }
    return render(request, 'recetas_app/eliminar_comentario_confirm.html', context)


# Vista lista de recetas por categoría
def recetas_por_categoria(request, categoria_slug):
    categoria = get_object_or_404(Categoria, slug=categoria_slug)
    recetas = Receta.objects.filter(categoria=categoria).order_by('-fecha_publicacion')
    categorias = Categoria.objects.all()

    # Obtener los IDs de las recetas favoritas del usuario actual para los iconos
    favoritas_ids = set()
    if request.user.is_authenticated:
        favoritas_ids = set(request.user.recetas_favoritas.values_list('receta__pk', flat=True))

    context = {
        'categoria_actual': categoria,
        'recetas': recetas,
        'categorias': categorias,
        'categoria_slug': categoria_slug, # Asegúrate de pasar el slug para mantener el filtro activo
        'filtro_categoria_aplicado': True,
        'categoria_nombre': categoria.nombre,
        'categoria_encontrada': True,
        'favoritas_ids': favoritas_ids, # Pasamos los IDs de las recetas favoritas
    }
    return render(request, 'recetas_app/home.html', context) # Reutilizamos home.html

# Vista para listar, crear, editar y eliminar categorías (solo para administradores)
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')
    context = {
        'categorias': categorias
    }
    return render(request, 'recetas_app/lista_categorias.html', context)

@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES)
        if form.is_valid():
            categoria = form.save(commit=False)
            # El slug se genera automáticamente en el método save del modelo Categoria
            categoria.save()
            messages.success(request, '¡Categoría creada exitosamente!')
            return redirect('recetas_app:lista_categorias')
        else:
            messages.error(request, 'Hubo un error al crear la categoría.')
    else:
        form = CategoriaForm()
    context = {
        'form': form,
        'accion': 'Crear'
    }
    return render(request, 'recetas_app/categoria_form.html', context)

@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def editar_categoria(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES, instance=categoria)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.save()
            messages.success(request, '¡Categoría actualizada exitosamente!')
            return redirect('recetas_app:lista_categorias')
        else:
            messages.error(request, 'Hubo un error al editar la categoría.')
    else:
        form = CategoriaForm(instance=categoria)
    context = {
        'form': form,
        'accion': 'Editar',
        'categoria': categoria,
    }
    return render(request, 'recetas_app/categoria_form.html', context)

@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def eliminar_categoria(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente.')
        return redirect('recetas_app:lista_categorias')
    context = {
        'categoria': categoria
    }
    return render(request, 'recetas_app/categoria_confirm_delete.html', context)

# Vista para las opciones de administración
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_options_view(request):
    return render(request, 'recetas_app/admin_options.html', {})

# Vista para previsualizar una receta antes de publicarla.
def previsualizar_receta(request):
    """
    Vista para previsualizar una receta antes de publicarla.
    Recibe los datos del formulario (POST) y los renderiza.
    """
    if request.method == 'POST':
        receta_form = RecetaForm(request.POST, request.FILES)
        ingrediente_formset = IngredienteFormSet(request.POST, prefix='ingredientes')
        paso_formset = PasoFormSet(request.POST, prefix='pasos')

        receta_data = {
            'titulo': receta_form['titulo'].value() if receta_form['titulo'].value() is not None else '',
            'descripcion': receta_form['descripcion'].value() if receta_form['descripcion'].value() is not None else '',
            'tiempo_preparacion': receta_form['tiempo_preparacion'].value() if receta_form['tiempo_preparacion'].value() is not None else None,
            'porciones': receta_form['porciones'].value() if receta_form['porciones'].value() is not None else None,
            'autor': request.user,
            'fecha_publicacion': timezone.now(),
        }

        categoria_id = receta_form['categoria'].value()
        if categoria_id:
            try:
                receta_data['categoria'] = Categoria.objects.get(pk=categoria_id)
            except Categoria.DoesNotExist:
                receta_data['categoria'] = None
        else:
            receta_data['categoria'] = None

        if 'imagen' in request.FILES:
            receta_data['imagen_file'] = request.FILES['imagen']
            receta_data['imagen'] = None
        else:
            receta_data['imagen_file'] = None
            receta_data['imagen'] = None

        ingredientes_preview = []
        for form_ingrediente in ingrediente_formset:
            if not form_ingrediente.cleaned_data.get('DELETE', False) and any(field.value() for field in form_ingrediente.fields.values()):
                if form_ingrediente.is_valid():
                    ingredientes_preview.append(form_ingrediente.cleaned_data)
                else:
                    data_with_errors = {
                        'nombre': form_ingrediente.data.get(form_ingrediente.add_prefix('nombre'), ''),
                        'cantidad': form_ingrediente.data.get(form_ingrediente.add_prefix('cantidad'), ''),
                        'unidad': form_ingrediente.data.get(form_ingrediente.add_prefix('unidad'), ''),
                        'errors': form_ingrediente.errors
                    }
                    ingredientes_preview.append(data_with_errors)


        pasos_preview = []
        for form_paso in paso_formset:
            if not form_paso.cleaned_data.get('DELETE', False) and any(field.value() for field in form_paso.fields.values()):
                if form_paso.is_valid():
                    pasos_preview.append(form_paso.cleaned_data)
                else:
                    data_with_errors = {
                        'titulo': form_paso.data.get(form_paso.add_prefix('titulo'), ''),
                        'descripcion': form_paso.data.get(form_paso.add_prefix('descripcion'), ''),
                        'errors': form_paso.errors
                    }
                    pasos_preview.append(data_with_errors)

        context = {
            'receta': receta_data,
            'ingredientes': ingredientes_preview,
            'pasos': pasos_preview,
            'is_preview': True,
            'form': receta_form,
            'formset_ingredientes': ingrediente_formset,
            'formset_pasos': paso_formset,
        }
        return render(request, 'recetas_app/previsualizar_receta.html', context)
    else:
        messages.error(request, 'Acceso no válido para previsualizar receta. Por favor, crea una receta primero.')
        return redirect('recetas_app:crear_receta')

# Acerca de y Contacto
def acerca_de(request):
    """
    Vista para la página "Acerca de".
    """
    return render(request, 'recetas_app/acerca_de.html')

def contacto(request):
    """
    Vista para la página de contacto.
    """
    # Añadir lógica para un formulario de contacto aquí si lo necesitamos
    from apps.usuarios.forms import ContactoForm # Importar aquí para evitar circular imports si es un problema
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            # Aquí puedes procesar el formulario, enviar un email, etc.
            # Por ahora, solo lo redirigimos a una página de éxito o al home
            messages.success(request, '¡Mensaje enviado con éxito! Nos pondremos en contacto contigo pronto.')
            return redirect(reverse_lazy('recetas_app:home')) # O una página de éxito
        else:
            messages.error(request, 'Hubo un error al enviar tu mensaje. Por favor, revisa los campos.')
    else:
        form = ContactoForm()
    return render(request, 'recetas_app/contacto.html', {'form': form})

# VISTAS PARA MENSAJES PRIVADOS 

@login_required
def inbox(request):
    """
    Muestra la bandeja de entrada del usuario. Lista a todos los usuarios con los que
    el usuario actual ha tenido una conversación.
    """
    # Importar Mensaje aquí para evitar circular imports si MensajeForm lo necesita
    from apps.usuarios.models import Mensaje 

    # Obtener IDs de usuarios con los que el usuario actual ha intercambiado mensajes
    user_ids = Mensaje.objects.filter(
        Q(remitente=request.user) | Q(destinatario=request.user)
    ).values_list('remitente__pk', 'destinatario__pk')
    
    unique_user_ids = set()
    for sender_id, recipient_id in user_ids:
        if sender_id != request.user.pk:
            unique_user_ids.add(sender_id)
        if recipient_id != request.user.pk:
            unique_user_ids.add(recipient_id)

    conversations = []
    for user_id in unique_user_ids:
        other_user = get_object_or_404(User, pk=user_id)
        # Obtener el último mensaje de la conversación para mostrarlo en la bandeja de entrada
        last_message = Mensaje.objects.filter(
            Q(remitente=request.user, destinatario=other_user) | Q(remitente=other_user, destinatario=request.user)
        ).order_by('-fecha_envio').first()
        conversations.append({
            'other_user': other_user,
            'last_message': last_message
        })

    # Ordenar las conversaciones por la fecha del último mensaje
    conversations.sort(key=lambda x: x['last_message'].fecha_envio, reverse=True)

    context = {
        'conversations': conversations,
    }
    return render(request, 'recetas_app/mensajes/inbox.html', context)


@login_required
def private_message(request, username):
    """
    Muestra la conversación completa con un usuario específico y permite enviar nuevos mensajes.
    """
    # Importar Mensaje aquí para evitar circular imports si MensajeForm lo necesita
    from apps.usuarios.models import Mensaje 
    from apps.usuarios.forms import MensajeForm 

    other_user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        form = MensajeForm(request.POST)
        if form.is_valid():
            # Crear y guardar el nuevo mensaje
            mensaje = Mensaje(
                remitente=request.user,
                destinatario=other_user,
                asunto=form.cleaned_data['asunto'],
                cuerpo=form.cleaned_data['cuerpo']
            )
            mensaje.save()
            # Redirigir de nuevo a la misma página para ver el mensaje enviado
            return redirect('recetas_app:private_message', username=username)
    else:
        form = MensajeForm()

    # Obtener todos los mensajes entre los dos usuarios
    messages = Mensaje.objects.filter(
        Q(remitente=request.user, destinatario=other_user) | Q(remitente=other_user, destinatario=request.user)
    ).order_by('fecha_envio')
    
    # Marcar como leídos todos los mensajes recibidos del otro usuario
    Mensaje.objects.filter(destinatario=request.user, remitente=other_user).update(is_leido=True)

    context = {
        'other_user': other_user,
        'messages': messages,
        'form': form,
    }
    return render(request, 'recetas_app/mensajes/private_message.html', context)
