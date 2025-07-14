from django.urls import path
from . import views
from apps.usuarios.views import CustomLoginView, CustomLogoutView

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]