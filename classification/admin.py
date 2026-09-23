from django.contrib import admin
from .models import Clasificacion

@admin.register(Clasificacion)
class ClasificacionAdmin(admin.ModelAdmin):
    list_display = (
        'lote',
        'secuencia',
        'clase_predicha',
        'confianza',
        'tiempo_inferencia_ms',
        'latencia_total_ms',
        'estado',
        'fecha_hora'
    )
    list_filter = ('estado', 'clase_predicha', 'lote')
    search_fields = ('lote__codigo', 'lote__nombre', 'clase_predicha')
    readonly_fields = ('fecha_hora',)
    ordering = ('-fecha_hora',)
