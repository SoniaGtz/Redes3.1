from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import render
from django.views.generic import View
from .models import Flow

from rest_framework.views import APIView
from rest_framework.response import Response

import AnalyzeJson as json

# Create your views here.

class HomeView(View):
    def get(self, request, *args, **kargs):
        return render(request, 'charts.html', {})

def cargar_json(request):
    filename = "flows.json"
    flows = json.cargar_json(filename)
    for flow in flows:
        f = Flow(fecha=flow[0], servicio=flow[1], size=flow[2], ip_origen=flow[3], ip_destino=flow[4])
        f.save()

    return render(request, 'charts.html', {})

def mostrarFlows(request, *args, **kwargs):
    ip_origen = request.POST['ip_source']
    flows = Flow.objects.filter(ip_origen=ip_origen)
    return render(request, 'charts.html', context={'flows': flows})
