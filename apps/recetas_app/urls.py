from django.urls import path
from . import views

app_name = 'recetas_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('receta/<int:pk>/', views.detalle_receta, name='detalle_receta'),
]