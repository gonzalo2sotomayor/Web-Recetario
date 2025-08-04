# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q 
from django.contrib.auth.models import User 

from .forms import UserUpdateForm, PerfilUpdateForm, SeguridadPerfilForm, CategoriaFavoritaForm, MensajeForm, ComposeMessageForm
from .models import Perfil, CategoriaFavorita, Mensaje
from apps.recetas_app.models import Receta, Comentario, RecetaFavorita

def registro(request):
    """
    Vista para el registro de nuevos usuarios.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse_lazy('recetas_app:home'))
    else:
        form = UserCreationForm()
    return render(request, 'usuarios/registration/registro.html', {'form': form})

class CustomLoginView(LoginView):
    """
    Vista personalizada para el login.
    """
    template_name = 'usuarios/registration/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    """
    Vista personalizada para el logout.
    """
    next_page = reverse_lazy('recetas_app:home')

@login_required
def perfil_editar(request):
    """
    Vista para editar el perfil del usuario y sus datos de usuario.
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        perfil_form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user.perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            return redirect('usuarios:editar_perfil')
    else:
        user_form = UserUpdateForm(instance=request.user)
        perfil_form = PerfilUpdateForm(instance=request.user.perfil)

    return render(request, 'usuarios/perfil_editar.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'user': request.user
    })

@login_required
def perfil_seguridad(request):
    """
    Vista para cambiar la contraseña y otras configuraciones de seguridad.
    """
    if request.method == 'POST':
        password_form = PasswordChangeForm(user=request.user, data=request.POST)
        seguridad_form = SeguridadPerfilForm(request.POST, instance=request.user.perfil)

        if 'change_password_submit' in request.POST:
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                return redirect('usuarios:seguridad_perfil')
            
        if 'seguridad_settings_submit' in request.POST:
            if seguridad_form.is_valid():
                seguridad_form.save()
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
    """
    Vista para gestionar las recetas y categorías favoritas.
    """
    recetas_favoritas = RecetaFavorita.objects.filter(usuario=request.user).order_by('-fecha_agregado')
    categorias_favoritas = CategoriaFavorita.objects.filter(usuario=request.user).order_by('nombre')

    if request.method == 'POST':
        categoria_form = CategoriaFavoritaForm(request.POST)
        if categoria_form.is_valid():
            nueva_categoria = categoria_form.save(commit=False)
            nueva_categoria.usuario = request.user
            nueva_categoria.save()
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
    """
    Vista para ver los comentarios del usuario.
    """
    comentarios_principales = Comentario.objects.filter(
        autor=request.user,
        respuesta_a__isnull=True
    ).order_by('-fecha_creacion')

    return render(request, 'usuarios/perfil_mis_comentarios.html', {
        'comentarios_principales': comentarios_principales,
        'user': request.user
    })

@login_required
def ver_perfil(request):
    """
    Vista para ver el perfil público del usuario.
    """
    perfil = request.user.perfil
    recetas_favoritas = RecetaFavorita.objects.filter(usuario=request.user).order_by('-fecha_agregado')
    ultimos_comentarios = Comentario.objects.filter(autor=request.user).order_by('-fecha_creacion')[:5]

    favoritos_por_categoria = {}
    for fav in recetas_favoritas:
        categoria_nombre = fav.categoria.nombre if fav.categoria else "Sin Categoría"
        if categoria_nombre not in favoritos_por_categoria:
            favoritos_por_categoria[categoria_nombre] = []
        favoritos_por_categoria[categoria_nombre].append(fav)

    context = {
        'perfil': perfil,
        'recetas_favoritas': recetas_favoritas,
        'ultimos_comentarios': ultimos_comentarios,
        'favoritos_por_categoria': favoritos_por_categoria,
        'user': request.user,
    }
    return render(request, 'usuarios/ver_perfil.html', context)

# VISTAS DE MENSAJES PRIVADOS

@login_required
def inbox(request):
    """
    Vista para la bandeja de entrada de mensajes.
    Muestra una lista de conversaciones con el último mensaje.
    """
    mensajes = Mensaje.objects.filter(
        Q(remitente=request.user) | Q(destinatario=request.user)
    ).order_by('-fecha_envio')
    
    conversations = {}
    for mensaje in mensajes:
        other_user = mensaje.remitente if mensaje.destinatario == request.user else mensaje.destinatario
        if other_user.username not in conversations:
            conversations[other_user.username] = {
                'other_user': other_user,
                'last_message': mensaje,
                'unread_count': Mensaje.objects.filter(
                    remitente=other_user,
                    destinatario=request.user,
                    is_leido=False
                ).count()
            }
    
    conversation_list = list(conversations.values())
    
    return render(request, 'usuarios/inbox.html', {
        'conversations': conversation_list,
    })


@login_required
def private_message(request, username):
    """
    Vista para ver una conversación privada con un usuario específico
    y enviar un nuevo mensaje.
    """
    other_user = get_object_or_404(User, username=username)
    
    messages = Mensaje.objects.filter(
        Q(remitente=request.user, destinatario=other_user) |
        Q(remitente=other_user, destinatario=request.user)
    ).order_by('fecha_envio')
    
    Mensaje.objects.filter(
        remitente=other_user, 
        destinatario=request.user, 
        is_leido=False
    ).update(is_leido=True)
    
    if request.method == 'POST':
        form = MensajeForm(request.POST)
        if form.is_valid():
            nuevo_mensaje = form.save(commit=False)
            nuevo_mensaje.remitente = request.user
            nuevo_mensaje.destinatario = other_user
            if not nuevo_mensaje.asunto:
                nuevo_mensaje.asunto = f"Re: Conversación con {other_user.username}"
            nuevo_mensaje.save()
            return redirect('usuarios:private_message', username=username)
    else:
        form = MensajeForm()
        
    return render(request, 'usuarios/private_message.html', {
        'messages': messages,
        'other_user': other_user,
        'form': form
    })

@login_required
def compose_new_message(request):
    """
    Vista para componer y enviar un nuevo mensaje a cualquier usuario.
    """
    if request.method == 'POST':
        form = ComposeMessageForm(request.POST, user=request.user)
        if form.is_valid():
            new_message = form.save(commit=False)
            new_message.remitente = request.user
            new_message.destinatario = form.cleaned_data['destinatario']
            new_message.save()
            return redirect('usuarios:private_message', username=new_message.destinatario.username)
    else:
        form = ComposeMessageForm(user=request.user)
    
    return render(request, 'usuarios/compose.html', {'form': form})


@login_required
def toggle_favorito(request, receta_pk):
    """
    Añade o quita una receta de favoritos.
    """
    receta = get_object_or_404(Receta, pk=receta_pk)
    favorito_existente = RecetaFavorita.objects.filter(usuario=request.user, receta=receta)

    if favorito_existente.exists():
        favorito_existente.delete()
        es_favorito = False
    else:
        RecetaFavorita.objects.create(usuario=request.user, receta=receta)
        es_favorito = True
    
    return redirect('recetas_app:detalle_receta', pk=receta_pk)

@login_required
def add_to_category(request, receta_pk):
    """
    Añade una receta favorita a una categoría específica.
    """
    receta = get_object_or_404(Receta, pk=receta_pk)
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria_id')
        if categoria_id:
            categoria = get_object_or_404(CategoriaFavorita, pk=categoria_id, usuario=request.user)
            receta_favorita, created = RecetaFavorita.objects.get_or_create(usuario=request.user, receta=receta)
            receta_favorita.categoria = categoria
            receta_favorita.save()
    return redirect('recetas_app:detalle_receta', pk=receta_pk)


@login_required
def toggle_favorito(request, receta_pk):
    """
    Añade o quita una receta de favoritos.
    """
    receta = get_object_or_404(Receta, pk=receta_pk)
    favorito_existente = RecetaFavorita.objects.filter(usuario=request.user, receta=receta)

    if favorito_existente.exists():
        favorito_existente.delete()
        es_favorito = False
    else:
        RecetaFavorita.objects.create(usuario=request.user, receta=receta)
        es_favorito = True
    
    return redirect('recetas_app:detalle_receta', pk=receta_pk)

@login_required
def add_to_category(request, receta_pk):
    """
    Añade una receta favorita a una categoría específica.
    """
    receta = get_object_or_404(Receta, pk=receta_pk)
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria_id')
        if categoria_id:
            categoria = get_object_or_404(CategoriaFavorita, pk=categoria_id, usuario=request.user)
            receta_favorita, created = RecetaFavorita.objects.get_or_create(usuario=request.user, receta=receta)
            receta_favorita.categoria = categoria
            receta_favorita.save()
    return redirect('recetas_app:detalle_receta', pk=receta_pk)