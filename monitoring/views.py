from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import Http404
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count

from .models import Lote, Dispositivo
from .serializers import LoteSerializer
from classification.models import Clasificacion
from django.conf import settings

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class DashboardView(View):
    def get(self, request, codigo_lote):
        lote = get_object_or_404(Lote, codigo=codigo_lote)
        return render(request, 'dashboard.html', {'codigo_lote': lote.codigo})

class CameraView(View):
    def get(self, request, codigo_lote):
        lote = get_object_or_404(Lote, codigo=codigo_lote)
        return render(request, 'camera.html', {'codigo_lote': lote.codigo})

class HistoryView(View):
    def get(self, request, codigo_lote):
        lote = get_object_or_404(Lote, codigo=codigo_lote)
        return render(request, 'history.html', {'codigo_lote': lote.codigo})

class SettingsView(View):
    def get(self, request):
        return render(request, 'settings.html')

# API Views

class LoteListCreateAPIView(generics.ListCreateAPIView):
    queryset = Lote.objects.all().order_by('-creado_en')
    serializer_class = LoteSerializer

class LoteDetailAPIView(APIView):
    def get(self, request, codigo):
        lote = get_object_or_404(Lote, codigo=codigo)
        serializer = LoteSerializer(lote)
        # Incluir clasificaciones en el detalle del lote
        clasificaciones = lote.clasificaciones.all().order_by('-fecha_hora')[:10]
        from classification.serializers import ClasificacionSerializer
        clasificaciones_serialized = ClasificacionSerializer(clasificaciones, many=True).data
        
        data = serializer.data
        data['clasificaciones_recientes'] = clasificaciones_serialized
        return Response(data)

class LoteStatisticsAPIView(APIView):
    def get(self, request, codigo):
        lote = get_object_or_404(Lote, codigo=codigo)
        
        # Contadores de clasificaciones
        maduros = lote.clasificaciones.filter(clase_predicha='MADURO', estado='CLASIFICADO').count()
        inmaduros = lote.clasificaciones.filter(clase_predicha='INMADURO', estado='CLASIFICADO').count()
        
        # En revisión son los rechazados por baja confianza o marcados explícitamente como REVISION
        revision = lote.clasificaciones.filter(clase_predicha='REVISION').count() + \
                   lote.clasificaciones.filter(estado='RECHAZADO').count()
        
        total = lote.clasificaciones.count()
        
        return Response({
            'lote_codigo': lote.codigo,
            'total_mature': maduros,
            'total_immature': inmaduros,
            'total_review': revision,
            'total_processed': total
        })
