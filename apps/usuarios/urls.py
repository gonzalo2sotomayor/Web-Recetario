from django.urls import path
from . import views
from apps.usuarios.views import CustomLoginView, CustomLogoutView

app_name = 'usuarios'

urlpatterns = [
    # URLs de autenticación
    path('registro/', views.registro, name='registro'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # URLs de perfil
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('perfil/editar/', views.perfil_editar, name='editar_perfil'),
    path('perfil/seguridad/', views.perfil_seguridad, name='seguridad_perfil'),
    path('perfil/favoritos/', views.perfil_favoritos, name='favoritos_perfil'),
    path('perfil/mis_comentarios/', views.perfil_mis_comentarios, name='mis_comentarios'),
    
    # URLs de Mensajes Privados
    path('mensajes/', views.inbox, name='inbox'),
    path('mensajes/<str:username>/', views.private_message, name='private_message'),

    # URLs para favoritos 
    path('toggle-favorito/<int:receta_pk>/', views.toggle_favorito, name='toggle_favorito'),
    path('add-to-category/<int:receta_pk>/', views.add_to_category, name='add_to_category'),
]