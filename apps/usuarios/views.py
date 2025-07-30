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

from .forms import UserUpdateForm, PerfilUpdateForm, SeguridadPerfilForm, CategoriaFavoritaForm, MensajeForm
from .models import Perfil, CategoriaFavorita, Mensaje
from apps.recetas_app.models import Receta, Comentario, RecetaFavorita

def registro(request):
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

        if 'change_password_submit' in request.POST:
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                # Recordarme: Añadir un mensaje de éxito
                return redirect('usuarios:seguridad_perfil')
            
        if 'seguridad_settings_submit' in request.POST:
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
    # Corregido: 'user' a 'usuario'
    recetas_favoritas = RecetaFavorita.objects.filter(usuario=request.user).order_by('-fecha_agregado')
    # Corregido: 'user' a 'usuario'
    categorias_favoritas = CategoriaFavorita.objects.filter(usuario=request.user).order_by('nombre')

    if request.method == 'POST':
        categoria_form = CategoriaFavoritaForm(request.POST)
        if categoria_form.is_valid():
            nueva_categoria = categoria_form.save(commit=False)
            # Corregido: 'user' a 'usuario'
            nueva_categoria.usuario = request.user
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
    # Obtener el perfil del usuario actual
    perfil = request.user.perfil

    # Obtener las recetas favoritas del usuario
    recetas_favoritas = RecetaFavorita.objects.filter(usuario=request.user).order_by('-fecha_agregado')
    
    # Obtener los comentarios más recientes del usuario (ej. los últimos 5)
    ultimos_comentarios = Comentario.objects.filter(autor=request.user).order_by('-fecha_creacion')[:5]

    # Agrupar recetas favoritas por categoría
    favoritos_por_categoria = {}
    for fav in recetas_favoritas:
        categoria_nombre = fav.categoria.nombre if fav.categoria else "Sin Categoría"
        if categoria_nombre not in favoritos_por_categoria:
            favoritos_por_categoria[categoria_nombre] = []
        favoritos_por_categoria[categoria_nombre].append(fav)

    context = {
        'perfil': perfil,
        'recetas_favoritas': recetas_favoritas, # Todas las favoritas
        'ultimos_comentarios': ultimos_comentarios,
        'favoritos_por_categoria': favoritos_por_categoria, # Favoritas agrupadas por categoría
        'user': request.user, # El objeto User también está disponible
    }
    return render(request, 'usuarios/ver_perfil.html', context)

#Listar mensajes privados
@login_required
def mensajes_privados(request):
    # Obtener mensajes recibidos por el usuario actual
    mensajes_recibidos = Mensaje.objects.filter(destinatario=request.user).order_by('-fecha_envio')
    
    # Obtener mensajes enviados por el usuario actual
    mensajes_enviados = Mensaje.objects.filter(remitente=request.user).order_by('-fecha_envio')

    # Contar mensajes no leídos (para el badge en la barra de navegación)
    # Esta lógica se moverá a un context processor para ser más eficiente globalmente
    unread_messages_count = Mensaje.objects.filter(destinatario=request.user, leido=False).count()

    context = {
        'mensajes_recibidos': mensajes_recibidos,
        'mensajes_enviados': mensajes_enviados,
        'unread_messages_count': unread_messages_count, # Se pasará al template
        'user': request.user,
    }
    return render(request, 'usuarios/mensajes_privados.html', context)

#Enviar un mensaje privado
@login_required
def enviar_mensaje(request, destinatario_id=None):
    destinatario_obj = None
    if destinatario_id:
        destinatario_obj = get_object_or_404(User, pk=destinatario_id)

    if request.method == 'POST':
        # Pasar el usuario remitente al formulario para excluirlo del queryset de destinatarios
        form = MensajeForm(request.POST, sender_user=request.user)
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.remitente = request.user
            # El destinatario ya viene del formulario
            mensaje.save()
            # Añadir un mensaje de éxito aquí (opcional)
            return redirect('usuarios:mensajes_privados') # Redirigir a la bandeja de entrada
    else:
        # Si se pasa un destinatario_id, preseleccionar el destinatario en el formulario
        initial_data = {}
        if destinatario_obj:
            initial_data['destinatario'] = destinatario_obj
        form = MensajeForm(initial=initial_data, sender_user=request.user)

    context = {
        'form': form,
        'destinatario_obj': destinatario_obj, # Para mostrar "Enviar a: [nombre de usuario]"
    }
    return render(request, 'usuarios/enviar_mensaje.html', context)

#Ver un Mensaje Específico y Marcarlo como Leído
@login_required
def detalle_mensaje(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje, pk=mensaje_id, destinatario=request.user)
    
    # Marcar el mensaje como leído si el usuario actual es el destinatario y no está leído
    if not mensaje.leido:
        mensaje.leido = True
        mensaje.save()

    # Formulario para responder al mensaje (pre-rellena el destinatario y el asunto)
    initial_data = {
        'destinatario': mensaje.remitente, # El remitente del mensaje actual es el destinatario de la respuesta
        'asunto': f"Re: {mensaje.asunto}", # Asunto con "Re:"
    }
    # Pasar el usuario remitente al formulario para excluirlo de la lista de destinatarios
    reply_form = MensajeForm(initial=initial_data, sender_user=request.user)

    context = {
        'mensaje': mensaje,
        'reply_form': reply_form,
    }
    return render(request, 'usuarios/detalle_mensaje.html', context)

#Marcar un mensaje como leído (útil para AJAX o botones específicos)
@login_required
def marcar_como_leido(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje, pk=mensaje_id, destinatario=request.user)
    mensaje.leido = True
    mensaje.save()
    return redirect('usuarios:mensajes_privados')

@login_required
def toggle_favorito(request, receta_pk):
    receta = get_object_or_404(Receta, pk=receta_pk)
    # Corregido: 'user' a 'usuario'
    favorito_existente = RecetaFavorita.objects.filter(usuario=request.user, receta=receta)

    if favorito_existente.exists():
        favorito_existente.delete()
        # Recordarme: Añadir mensaje de éxito/eliminación
        es_favorito = False
    else:
        # Corregido: 'user' a 'usuario'
        RecetaFavorita.objects.create(usuario=request.user, receta=receta)
        # Recordarme: Añadir mensaje de éxito/adición
        es_favorito = True
    
    return redirect('recetas_app:detalle_receta', pk=receta_pk)

@login_required
def add_to_category(request, receta_pk):
    receta = get_object_or_404(Receta, pk=receta_pk)
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria_id')
        if categoria_id:
            # Corregido: 'user' a 'usuario'
            categoria = get_object_or_404(CategoriaFavorita, pk=categoria_id, usuario=request.user)
            # Corregido: 'user' a 'usuario'
            receta_favorita, created = RecetaFavorita.objects.get_or_create(usuario=request.user, receta=receta)
            receta_favorita.categoria = categoria
            receta_favorita.save()
            # Recordarme: Añadir mensaje de éxito
    return redirect('recetas_app:detalle_receta', pk=receta_pk)
