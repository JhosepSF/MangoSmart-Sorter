from django.contrib import admin
from .models import EventoHardware, ConfiguracionSistema

@admin.register(EventoHardware)
class EventoHardwareAdmin(admin.ModelAdmin):
    list_display = ('comando', 'respuesta', 'confirmado', 'fecha_envio', 'fecha_respuesta', 'tiempo_respuesta_ms')
    list_filter = ('confirmado', 'fecha_envio')
    search_fields = ('comando', 'respuesta')

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = (
        'umbral_confianza',
        'puerto_serial',
        'baudrate',
        'modo_simulado',
        'angulo_neutral',
        'tiempo_compuerta_ms'
    )
