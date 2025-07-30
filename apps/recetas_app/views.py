from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
from django.db import transaction
from django.urls import reverse_lazy
from django.db.models import Q
import random
from django.utils.text import slugify
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils import timezone


# Importaciones consolidadas de modelos y formularios
from .models import Receta, Ingrediente, Paso, Comentario, Categoria
# Importamos los Formsets y formularios directamente, ya que los definimos en forms.py
from .forms import ComentarioForm, ComentarioEditForm, RecetaForm, IngredienteFormSet, PasoFormSet, CategoriaForm


# Función para verificar si el usuario es administrador (is_staff)
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Vista para la página de inicio (Home)
def home(request):
    recetas = Receta.objects.all()
    categorias = Categoria.objects.all()

    filtro_categoria_aplicado = False
    categoria_encontrada = True
    categoria_nombre = None

    categoria_slug = request.GET.get('categoria')
    if categoria_slug:
        filtro_categoria_aplicado = True
        try:
            categoria_seleccionada = Categoria.objects.get(slug=categoria_slug)
            recetas = recetas.filter(categoria=categoria_seleccionada)
            categoria_nombre = categoria_seleccionada.nombre
        except Categoria.DoesNotExist:
            recetas = Receta.objects.none()
            categoria_encontrada = False

    # --- Lógica de Ordenamiento ---
    order_by = request.GET.get('order_by', 'fecha_publicacion') # Por defecto, ordenar por fecha de publicación
    direction = request.GET.get('direction', 'desc') # Por defecto, descendente

    if order_by == 'fecha_publicacion':
        if direction == 'asc':
            recetas = recetas.order_by('fecha_publicacion')
        else: # 'desc'
            recetas = recetas.order_by('-fecha_publicacion')
    elif order_by == 'titulo':
        if direction == 'asc':
            recetas = recetas.order_by('titulo')
        else: # 'desc'
            recetas = recetas.order_by('-titulo')

    # --- Obtener la Receta de la Semana (NUEVO) ---
    # Intenta obtener la receta más reciente marcada como destacada
    receta_de_la_semana = Receta.objects.filter(is_featured=True).order_by('-fecha_publicacion').first()

    context = {
        'recetas': recetas,
        'categorias': categorias,
        'filtro_categoria_aplicado': filtro_categoria_aplicado,
        'categoria_encontrada': categoria_encontrada,
        'categoria_nombre': categoria_nombre,
        'current_order_by': order_by,
        'current_direction': direction,
        'receta_de_la_semana': receta_de_la_semana, # Pasar la receta destacada al template
    }
    return render(request, 'recetas_app/home.html', context)

# Vista para el detalle de una receta específica
def detalle_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)

    # --- INICIO DE CÓDIGO DE DEPURACIÓN ---
    print(f"\n--- Depuración para Receta ID: {receta.pk} ---")
    print(f"Título de la receta: {receta.titulo}")
    print(f"Número de ingredientes relacionados: {receta.ingredientes.count()}")
    for i, ingrediente in enumerate(receta.ingredientes.all()):
        print(f"    Ingrediente {i+1}: {ingrediente.cantidad} {ingrediente.unidad} de {ingrediente.nombre}")

    print(f"Número de pasos relacionados: {receta.pasos.count()}")
    for i, paso in enumerate(receta.pasos.all()):
        print(f"    Paso {i+1}: Título: {paso.titulo}, Descripción: {paso.descripcion[:30]}...")
    print("---------------------------------------\n")
    # --- FIN DE CÓDIGO DE DEPURACIÓN ---

    comentarios_principales = Comentario.objects.filter(
        receta=receta,
        respuesta_a__isnull=True
    ).order_by('fecha_creacion')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para dejar un comentario.')
            return redirect('usuarios:login')

        form = ComentarioForm(request.POST)
        if form.is_valid():
            nuevo_comentario = form.save(commit=False)
            nuevo_comentario.receta = receta
            nuevo_comentario.autor = request.user
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
        messages.info(request, 'No hay recetas disponibles para descubrir.')
        return redirect('recetas_app:home')

# Vista para la búsqueda simple
def simple_search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = Receta.objects.filter(
            Q(titulo__icontains=query) | Q(descripcion__icontains=query)
        ).distinct()
    
    # --- Lógica de Ordenamiento para búsqueda simple ---
    order_by = request.GET.get('order_by', 'fecha_publicacion')
    direction = request.GET.get('direction', 'desc')

    if order_by == 'fecha_publicacion':
        if direction == 'asc':
            results = results.order_by('fecha_publicacion')
        else: # 'desc'
            results = results.order_by('-fecha_publicacion')
    elif order_by == 'titulo':
        if direction == 'asc':
            results = results.order_by('titulo')
        else: # 'desc'
            results = results.order_by('-titulo')

    context = {
        'query': query,
        'results': results,
        'search_type': 'simple',
        'current_order_by': order_by,
        'current_direction': direction,
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
    category_slug = request.GET.get('category', '').strip()

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

    if category_slug:
        try:
            category_obj = Categoria.objects.get(slug=category_slug)
            queryset = queryset.filter(categoria=category_obj)
        except Categoria.DoesNotExist:
            pass

    results = queryset.distinct()

    # --- Lógica de Ordenamiento para búsqueda avanzada ---
    order_by = request.GET.get('order_by', 'fecha_publicacion')
    direction = request.GET.get('direction', 'desc')

    if order_by == 'fecha_publicacion':
        if direction == 'asc':
            results = results.order_by('fecha_publicacion')
        else: # 'desc'
            results = results.order_by('-fecha_publicacion')
    elif order_by == 'titulo':
        if direction == 'asc':
            results = results.order_by('titulo')
        else: # 'desc'
            results = results.order_by('-titulo')

    context = {
        'exact_phrase': exact_phrase,
        'similar_words': similar_words,
        'ingredient': ingredient,
        'recipe_type': recipe_type,
        'results': results,
        'search_type': 'advanced',
        'categories': Categoria.objects.all(),
        'selected_category': category_slug,
        'current_order_by': order_by,
        'current_direction': direction,
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

# --- INICIO DE DEPURACIÓN DE FORMSETS EN VIEWS.PY ---
        print("\n--- Depuración de Formsets en crear_receta (POST) ---")
        print(f"Receta Formulario es válido: {receta_form.is_valid()}")
        print(f"Ingrediente Formset es válido: {ingrediente_formset.is_valid()}")
        print(f"Paso Formset es válido: {paso_formset.is_valid()}")

        if not receta_form.is_valid():
            print("Errores en Receta Form:")
            print(receta_form.errors)

        if not ingrediente_formset.is_valid():
            print("Errores en Ingrediente Formset:")
            for i, form in enumerate(ingrediente_formset):
                if form.errors:
                    print(f"    Formulario Ingrediente {i}: {form.errors}")
        else:
            print("Ingrediente Formset - Cleaned Data:")
            for i, form in enumerate(ingrediente_formset):
                if form.cleaned_data:
                    print(f"    Formulario Ingrediente {i}: {form.cleaned_data}")

        if not paso_formset.is_valid():
            print("Errores en Paso Formset:")
            for i, form in enumerate(paso_formset):
                if form.errors:
                    print(f"    Formulario Paso {i}: {form.errors}")
        else:
            print("Paso Formset - Cleaned Data:")
            for i, form in enumerate(paso_formset):
                if form.cleaned_data:
                    # CAMBIO AQUÍ: 'orden' se cambia a 'titulo'
                    print(f"    Formulario Paso {i}: {{'titulo': {form.cleaned_data.get('titulo')}, 'descripcion': {form.cleaned_data.get('descripcion')}}}")
        print("---------------------------------------------------\n")
        # --- FIN DE DEPURACIÓN DE FORMSETS EN VIEWS.PY ---

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
                print(f"Error al crear receta: {e}")
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        receta_form = RecetaForm()
        ingrediente_formset = IngredienteFormSet(prefix='ingredientes')
        paso_formset = PasoFormSet(prefix='pasos')

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
    if receta.autor != request.user:
        messages.error(request, 'No tienes permiso para editar esta receta.')
        return redirect('recetas_app:detalle_receta', pk=receta.pk)

    if request.method == 'POST':
        receta_form = RecetaForm(request.POST, request.FILES, instance=receta)
        ingrediente_formset = IngredienteFormSet(request.POST, instance=receta, prefix='ingredientes')
        paso_formset = PasoFormSet(request.POST, instance=receta, prefix='pasos')

    # --- INICIO DE DEPURACIÓN DE FORMSETS EN VIEWS.PY (Editar) ---
        print("\n--- Depuración de Formsets en editar_receta (POST) ---")
        print(f"Receta Formulario es válido: {receta_form.is_valid()}")
        print(f"Ingrediente Formset es válido: {ingrediente_formset.is_valid()}")
        print(f"Paso Formset es válido: {paso_formset.is_valid()}")

        if not receta_form.is_valid():
            print("Errores en Receta Form (Editar):")
            print(receta_form.errors)

        if not ingrediente_formset.is_valid():
            print("Errores en Ingrediente Formset (Editar):")
            for i, form in enumerate(ingrediente_formset):
                if form.errors:
                    print(f"    Formulario Ingrediente {i}: {form.errors}")
        else:
            print("Ingrediente Formset - Cleaned Data (Editar):")
            for i, form in enumerate(ingrediente_formset):
                if form.cleaned_data:
                    print(f"    Formulario Ingrediente {i}: {form.cleaned_data}")

        if not paso_formset.is_valid():
            print("Errores en Paso Formset:")
            for i, form in enumerate(paso_formset):
                if form.errors:
                    print(f"    Formulario Paso {i}: {form.errors}")
        else:
            print("Paso Formset - Cleaned Data (Editar):")
            for i, form in enumerate(paso_formset):
                if form.cleaned_data:
                    # CAMBIO AQUÍ: 'orden' se cambia a 'titulo'
                    print(f"    Formulario Paso {i}: {{'titulo': {form.cleaned_data.get('titulo')}, 'descripcion': {form.cleaned_data.get('descripcion')}}}")
        print("---------------------------------------------------\n")
        # --- FIN DE DEPURACIÓN DE FORMSETS EN VIEWS.PY (Editar) ---

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
                print(f"Error al editar receta: {e}")
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
    if receta.autor != request.user:
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


#  Editar Comentario
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


#  Eliminar Comentario
@login_required
def eliminar_comentario(request, pk):
    comentario = get_object_or_404(Comentario, pk=pk)
    # Asegurarse de que solo el autor o un admin pueda eliminar su comentario
    # (La lógica de admin ya está en detalle_receta.html, aquí solo verificamos)
    if not (request.user == comentario.autor or request.user.is_staff):
        messages.error(request, 'No tienes permiso para eliminar este comentario.')
        return redirect('recetas_app:detalle_receta', pk=comentario.receta.pk)

    if request.method == 'POST':
        receta_pk = comentario.receta.pk # Guardamos la PK de la receta antes de eliminar el comentario
        comentario.delete()
        messages.success(request, 'Comentario eliminado exitosamente.')
        return redirect('recetas_app:detalle_receta', pk=receta_pk)
    
    context = {
        'comentario': comentario,
        'receta': comentario.receta, # Para poder volver a la receta
    }
    return render(request, 'recetas_app/eliminar_comentario_confirm.html', context)


# Vista lista de recetas por categoría
def recetas_por_categoria(request, categoria_slug):
    categoria = get_object_or_404(Categoria, slug=categoria_slug)
    recetas = Receta.objects.filter(categoria=categoria).order_by('-fecha_publicacion')
    categorias = Categoria.objects.all()
    context = {
        'categoria_actual': categoria,
        'recetas': recetas,
        'categorias': categorias,
    }
    return render(request, 'recetas_app/recetas_por_categoria.html', context)

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
            # El slug se genera automáticamente en el método save del modelo Categoria
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
            # Solo procesar formularios que no estén marcados para DELETE y que tengan algún valor
            if not form_ingrediente.cleaned_data.get('DELETE', False) and any(field.value() for field in form_ingrediente.fields.values()):
                if form_ingrediente.is_valid():
                    ingredientes_preview.append(form_ingrediente.cleaned_data)
                else:
                    # Incluir datos y errores para depuración en la previsualización
                    data_with_errors = {
                        'nombre': form_ingrediente.data.get(form_ingrediente.add_prefix('nombre'), ''),
                        'cantidad': form_ingrediente.data.get(form_ingrediente.add_prefix('cantidad'), ''),
                        'unidad': form_ingrediente.data.get(form_ingrediente.add_prefix('unidad'), ''),
                        'errors': form_ingrediente.errors
                    }
                    ingredientes_preview.append(data_with_errors)


        pasos_preview = []
        for form_paso in paso_formset:
            # Solo procesar formularios que no estén marcados para DELETE y que tengan algún valor
            if not form_paso.cleaned_data.get('DELETE', False) and any(field.value() for field in form_paso.fields.values()):
                if form_paso.is_valid():
                    pasos_preview.append(form_paso.cleaned_data)
                else:
                    # Incluir datos y errores para depuración en la previsualización
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
    return render(request, 'recetas_app/contacto.html')
