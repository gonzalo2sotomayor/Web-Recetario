from django.shortcuts import render, get_object_or_404
from .models import Receta

def home(request):
    recetas = Receta.objects.all()
    return render(request, 'recetas_app/home.html', {'recetas': recetas})

def detalle_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)
    return render(request, 'recetas_app/detalle.html', {'receta': receta})