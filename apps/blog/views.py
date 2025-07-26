from django.shortcuts import render, get_object_or_404
from .models import Receta
import random

#request 'es un diccionario que continuamente se va pasando entre el navegador y el servidor'
# Home: muestra receta del día aleatoria
def home(request):
	recetas = Receta.objects.all()
	receta_del_dia = random.choice(recetas) if recetas else None
	return render(request, 't_home.html', {'receta_del_dia': receta_del_dia})

# Página de nosotros
def Nosotros(request):
	return render(request, 't_nosotros.html')

# Detalle de receta
def detalle_receta(request, receta_id):
    receta = get_object_or_404(Receta, id=receta_id)
    return render(request, 't_detalle_receta.html', {'receta': receta})
