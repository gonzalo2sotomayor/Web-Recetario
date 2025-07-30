from django.urls import path
from . import views

app_name = 'recetas_app'

urlpatterns = [
    # Rutas de Recetas
    path('', views.home, name='home'),
    path('receta/<int:pk>/', views.detalle_receta, name='detalle_receta'),
    path('receta/<int:pk>/editar/', views.editar_receta, name='editar_receta'),
    path('receta/<int:pk>/eliminar/', views.eliminar_receta, name='eliminar_receta'),
    path('crear/', views.crear_receta, name='crear_receta'),
    path('previsualizar/', views.previsualizar_receta, name='previsualizar_receta'),
    path('descubre/', views.recetas_aleatorias, name='recetas_aleatorias'),
    path('categoria/<slug:categoria_slug>/', views.recetas_por_categoria, name='recetas_por_categoria'),

    # Rutas de Comentarios (NUEVAS)
    path('comentario/<int:pk>/editar/', views.editar_comentario, name='editar_comentario'),
    path('comentario/<int:pk>/eliminar/', views.eliminar_comentario, name='eliminar_comentario'),

    # Rutas de Búsqueda
    path('buscar/', views.simple_search_view, name='simple_search'),
    path('buscar/avanzada/', views.advanced_search_view, name='advanced_search'),
    path('buscar/avanzada/resultados/', views.advanced_search_results_view, name='advanced_search_results'),

    # Rutas para la gestión de Categorías
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<slug:slug>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<slug:slug>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),

    # Ruta para las opciones de administración
    path('admin-options/', views.admin_options_view, name='admin_options'),
]