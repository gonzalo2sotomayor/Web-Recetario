# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from .forms import UserUpdateForm, PerfilUpdateForm, SeguridadPerfilForm, CategoriaFavoritaForm
from .models import Perfil, CategoriaFavorita, RecetaFavorita
from apps.recetas_app.models import Receta, Comentario

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse_lazy('recetas_app:home'))
    else:
        form = UserCreationForm()
    # Ruta de plantilla para registro
    return render(request, 'usuarios/registration/registro.html', {'form': form})

class CustomLoginView(LoginView):
    # Ruta de plantilla para login
    template_name = 'usuarios/registration/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('recetas_app:home')

@login_required
def perfil_editar(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        perfil_form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user.perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            # Recordarme: Añadir un mensaje de éxito si quiero
            return redirect('usuarios:editar_perfil')
    else:
        user_form = UserUpdateForm(instance=request.user)
        perfil_form = PerfilUpdateForm(instance=request.user.perfil)

    # Ruta de plantilla para editar perfil
    return render(request, 'usuarios/perfil_editar.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'user': request.user
    })

@login_required
def perfil_seguridad(request):
    if request.method == 'POST':
        password_form = PasswordChangeForm(user=request.user, data=request.POST)
        seguridad_form = SeguridadPerfilForm(request.POST, instance=request.user.perfil)

        if 'change_password_submit' in request.POST: # Botón de cambio de contraseña presionado
            if password_form.is_valid():
                password_form.save()
                # Importante: Actualizar la sesión para evitar que el usuario se desloguee
                update_session_auth_hash(request, password_form.user)
                # Recordarme: Añadir un mensaje de éxito
                return redirect('usuarios:seguridad_perfil')
        
        if 'seguridad_settings_submit' in request.POST: # Botón de seguridad/notificaciones presionado
            if seguridad_form.is_valid():
                seguridad_form.save()
                # Recordarme: Añadir un mensaje de éxito
                return redirect('usuarios:seguridad_perfil')
    else:
        password_form = PasswordChangeForm(user=request.user)
        seguridad_form = SeguridadPerfilForm(instance=request.user.perfil)

    return render(request, 'usuarios/perfil_seguridad.html', {
        'password_form': password_form,
        'seguridad_form': seguridad_form,
        'user': request.user
    })

@login_required
def perfil_favoritos(request):
    # Obtener las recetas favoritas del usuario
    recetas_favoritas = RecetaFavorita.objects.filter(user=request.user).order_by('-fecha_agregado')
    
    # Obtener las categorías de favoritos del usuario
    categorias_favoritas = CategoriaFavorita.objects.filter(user=request.user).order_by('nombre')

    if request.method == 'POST':
        categoria_form = CategoriaFavoritaForm(request.POST)
        if categoria_form.is_valid():
            nueva_categoria = categoria_form.save(commit=False)
            nueva_categoria.user = request.user
            nueva_categoria.save()
            # Recordarme: Añadir un mensaje de éxito
            return redirect('usuarios:favoritos_perfil')
    else:
        categoria_form = CategoriaFavoritaForm()

    return render(request, 'usuarios/perfil_favoritos.html', {
        'recetas_favoritas': recetas_favoritas,
        'categorias_favoritas': categorias_favoritas,
        'categoria_form': categoria_form,
        'user': request.user
    })

@login_required
def perfil_mis_comentarios(request):
    # Obtener los comentarios del usuario que no son respuestas a otros comentarios
    # (es decir, son comentarios de nivel superior)
    comentarios_principales = Comentario.objects.filter(
        autor=request.user,
        respuesta_a__isnull=True # Filtra solo los comentarios que no son respuestas
    ).order_by('-fecha_creacion')

    return render(request, 'usuarios/perfil_mis_comentarios.html', {
        'comentarios_principales': comentarios_principales,
        'user': request.user
    })

# Vista para añadir/eliminar una receta de favoritos (requerirá AJAX o un botón en la página de receta)
@login_required
def toggle_favorito(request, receta_pk):
    receta = get_object_or_404(Receta, pk=receta_pk)
    favorito_existente = RecetaFavorita.objects.filter(user=request.user, receta=receta)

    if favorito_existente.exists():
        favorito_existente.delete()
        # Recordarme: Añadir mensaje de éxito/eliminación
        es_favorito = False
    else:
        RecetaFavorita.objects.create(user=request.user, receta=receta)
        # Recordarme: Añadir mensaje de éxito/adición
        es_favorito = True
    
    # Esto podría ser una redirección o una respuesta JSON para AJAX
    # Por ahora, redirigimos a la página de la receta
    return redirect('recetas_app:detalle_receta', pk=receta_pk)

# Vista para añadir una receta a una categoría específica (requerirá un formulario en la página de receta)
@login_required
def add_to_category(request, receta_pk):
    receta = get_object_or_404(Receta, pk=receta_pk)
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria_id')
        if categoria_id:
            categoria = get_object_or_404(CategoriaFavorita, pk=categoria_id, user=request.user)
            receta_favorita, created = RecetaFavorita.objects.get_or_create(user=request.user, receta=receta)
            receta_favorita.categoria = categoria
            receta_favorita.save()
            # Recordarme: Añadir mensaje de éxito
    return redirect('recetas_app:detalle_receta', pk=receta_pk)

@login_required
def add_to_category(request, receta_pk):
    receta = get_object_or_404(Receta, pk=receta_pk)
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria_id')
        if categoria_id:
            categoria = get_object_or_404(CategoriaFavorita, pk=categoria_id, user=request.user)
            receta_favorita, created = RecetaFavorita.objects.get_or_create(user=request.user, receta=receta)
            receta_favorita.categoria = categoria
            receta_favorita.save()
            # Recordarme: Añadir mensaje de éxito
    return redirect('recetas_app:detalle_receta', pk=receta_pk)
