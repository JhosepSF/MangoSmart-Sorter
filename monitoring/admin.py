from django.contrib import admin
from .models import Lote, Dispositivo

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'fecha_inicio', 'fecha_fin', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('codigo', 'nombre')
    date_hierarchy = 'creado_en'

@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'identificador', 'lote', 'conectado', 'ultima_conexion')
    list_filter = ('tipo', 'conectado', 'lote')
    search_fields = ('nombre', 'identificador')
