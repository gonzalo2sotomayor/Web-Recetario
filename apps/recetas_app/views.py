from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
from django.db import transaction
from django.db.models import Q
import random
from django.utils.text import slugify
from django.contrib import messages

# Importaciones consolidadas de modelos y formularios
from .models import Receta, Ingrediente, Paso, Comentario, Categoria
from .forms import ComentarioForm, RecetaForm, IngredienteFormSet, PasoFormSet, CategoriaForm

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

    context = {
        'recetas': recetas,
        'categorias': categorias,
        'filtro_categoria_aplicado': filtro_categoria_aplicado,
        'categoria_encontrada': categoria_encontrada,
        'categoria_nombre': categoria_nombre,
    }
    return render(request, 'recetas_app/home.html', context)

# Vista para el detalle de una receta específica
def detalle_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)
    
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

    context = {
        'exact_phrase': exact_phrase,
        'similar_words': similar_words,
        'ingredient': ingredient,
        'recipe_type': recipe_type,
        'results': results,
        'search_type': 'advanced',
        'categories': Categoria.objects.all(), 
        'selected_category': category_slug, 
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

                    # Guardar ingredientes y asociarlos a la receta
                    for form_ingrediente in ingrediente_formset:
                        if form_ingrediente.cleaned_data and not form_ingrediente.cleaned_data.get('DELETE', False):
                            ingrediente = form_ingrediente.save(commit=False)
                            ingrediente.receta = receta
                            ingrediente.save()
                    
                    # Guardar pasos y asociarlos a la receta
                    for form_paso in paso_formset:
                        if form_paso.cleaned_data and not form_paso.cleaned_data.get('DELETE', False):
                            paso = form_paso.save(commit=False)
                            paso.receta = receta
                            paso.save()

                messages.success(request, '¡Receta creada exitosamente!')
                return redirect('recetas_app:detalle_receta', pk=receta.pk)

            except Exception as e:
                messages.error(request, f"Error al crear receta: {e}")
                print(f"Error al crear receta: {e}") # Para depuración en consola
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

        if receta_form.is_valid() and ingrediente_formset.is_valid() and paso_formset.is_valid():
            try:
                with transaction.atomic():
                    receta = receta_form.save()
                    ingrediente_formset.save() # Guarda los cambios, añade nuevos, elimina marcados
                    paso_formset.save() # Guarda los cambios, añade nuevos, elimina marcados

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
        return redirect('recetas_app:home') # Redirigir a la página principal o a una lista de recetas
    context = {
        'receta': receta
    }
    return render(request, 'recetas_app/receta_confirm_delete.html', context)

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
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.slug = slugify(categoria.nombre)
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
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.slug = slugify(categoria.nombre)
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
            'titulo': receta_form['titulo'].value(),
            'descripcion': receta_form['descripcion'].value(),
            'autor': request.user,
            'fecha_publicacion': 'Previsualización', # Indicador para la previsualización
        }

        # Manejo de la categoría
        categoria_id = receta_form['categoria'].value()
        if categoria_id:
            try:
                receta_data['categoria'] = Categoria.objects.get(pk=categoria_id)
            except Categoria.DoesNotExist:
                receta_data['categoria'] = None # Si la categoría no existe, se muestra como None

        # Manejo de la imagen: si es un archivo subido, pasamos el objeto.
        # La plantilla deberá manejar que no es una URL de imagen persistente.
        if 'imagen' in request.FILES:
            receta_data['imagen_file'] = request.FILES['imagen']
        else:
            receta_data['imagen_file'] = None
        
        # Procesar ingredientes y pasos del formset
        ingredientes_preview = []
        for i, form in enumerate(ingrediente_formset):
            # Solo procesar si el formulario no está marcado para eliminación
            if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                ingredientes_preview.append(form.cleaned_data)
            elif not form.is_valid() and any(form.errors):
                # Si el formulario tiene errores, lo incluimos con sus errores
                # para que el usuario pueda ver qué campos necesitan corrección.
                data_with_errors = form.data.copy()
                data_with_errors['errors'] = form.errors
                ingredientes_preview.append(data_with_errors)
            elif form.cleaned_data and form.cleaned_data.get('DELETE', False):
                # Si está marcado para eliminar, no lo incluimos en la previsualización
                pass
            elif any(field.value() for field in form.fields.values()):
                data_with_errors = form.data.copy()
                data_with_errors['errors'] = form.errors 
                ingredientes_preview.append(data_with_errors)


        pasos_preview = []
        for i, form in enumerate(paso_formset):
            if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                pasos_preview.append(form.cleaned_data)
            elif not form.is_valid() and any(form.errors):
                data_with_errors = form.data.copy()
                data_with_errors['errors'] = form.errors
                pasos_preview.append(data_with_errors)
            elif form.cleaned_data and form.cleaned_data.get('DELETE', False):
                pass
            elif any(field.value() for field in form.fields.values()):
                data_with_errors = form.data.copy()
                data_with_errors['errors'] = form.errors
                pasos_preview.append(data_with_errors)


        context = {
            'receta': receta_data,
            'ingredientes': ingredientes_preview,
            'pasos': pasos_preview,
            'is_preview': True, # Bandera para indicar que es una previsualización
            'receta_form': receta_form, # Pasar el formulario principal para errores
            'ingrediente_formset': ingrediente_formset, # Pasar los formsets para errores
            'paso_formset': paso_formset,
        }
        return render(request, 'recetas_app/previsualizar_receta.html', context)
    else:
        # Si se accede directamente sin POST, redirigir o mostrar un error
        messages.error(request, 'Acceso no válido para previsualizar receta. Por favor, crea una receta primero.')
        return redirect('recetas_app:crear_receta')

