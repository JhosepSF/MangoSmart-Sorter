from django.db import models
from classification.models import Clasificacion

class EventoHardware(models.Model):
    clasificacion = models.ForeignKey(
        Clasificacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_hardware'
    )
    comando = models.CharField(max_length=50)
    respuesta = models.CharField(max_length=50, null=True, blank=True)
    confirmado = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    tiempo_respuesta_ms = models.FloatField(default=0.0)
    mensaje_error = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Evento de Hardware"
        verbose_name_plural = "Eventos de Hardware"
        ordering = ['-fecha_envio']

    def __str__(self):
        status = "Confirmado" if self.confirmado else "Pendiente/Error"
        return f"Comando {self.comando} - Estado: {status}"


class ConfiguracionSistema(models.Model):
    umbral_confianza = models.FloatField(default=0.80)
    puerto_serial = models.CharField(max_length=50, default='COM3')
    baudrate = models.PositiveIntegerField(default=9600)
    modo_simulado = models.BooleanField(default=True)
    angulo_maduro = models.PositiveIntegerField(default=45)
    angulo_inmaduro = models.PositiveIntegerField(default=135)
    angulo_neutral = models.PositiveIntegerField(default=90)
    tiempo_compuerta_ms = models.PositiveIntegerField(default=2000)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"

    def __str__(self):
        return f"Configuración del Sistema (Simulado: {self.modo_simulado}, Umbral: {self.umbral_confianza})"

    def save(self, *args, **kwargs):
        # Asegurarse de que solo haya una fila de configuración (patrón Singleton simple)
        if not self.pk and ConfiguracionSistema.objects.exists():
            # Si ya existe, actualizar el primer registro en lugar de crear uno nuevo
            existing = ConfiguracionSistema.objects.first()
            self.pk = existing.pk
        return super().save(*args, **kwargs)
