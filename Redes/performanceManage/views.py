from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
import ConfigurationManagement as config
from django.views import generic
from .models import Estadistica

# Create your views here.

def nueva_estadistica(request, fecha, ip, tipo, valor):
    e = Estadistica(fecha=fecha, ip=ip, tipo=tipo, valor=valor)
    e.save()