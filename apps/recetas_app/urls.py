from django.urls import path
from . import views

app_name = 'recetas_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('receta/<int:pk>/', views.detalle_receta, name='detalle_receta'),
    path('buscar/', views.simple_search_view, name='simple_search'), # Vista para la búsqueda simple
    path('buscar/avanzada/', views.advanced_search_view, name='advanced_search'), # Nueva vista para el formulario
    path('buscar/avanzada/resultados/', views.advanced_search_results_view, name='advanced_search_results'), # Vista para procesar el formulario
    path('descubre/', views.recetas_aleatorias, name='recetas_aleatorias'),
]