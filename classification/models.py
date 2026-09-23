from django.db import models
from monitoring.models import Lote

class Clasificacion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'),
        ('CLASIFICADO', 'Clasificado'),
        ('RECHAZADO', 'Rechazado'),
        ('ERROR', 'Error'),
    ]

    CLASSES = [
        ('MADURO', 'Maduro'),
        ('INMADURO', 'Inmaduro'),
        ('REVISION', 'Revisión / Desconocido'),
    ]

    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='clasificaciones')
    secuencia = models.PositiveIntegerField(db_index=True)
    imagen_original = models.ImageField(upload_to='classifications/', null=True, blank=True)
    clase_predicha = models.CharField(max_length=20, choices=CLASSES, default='REVISION')
    confianza = models.FloatField(default=0.0)
    probabilidad_maduro = models.FloatField(default=0.0)
    probabilidad_inmaduro = models.FloatField(default=0.0)
    tiempo_preprocesamiento_ms = models.FloatField(default=0.0)
    tiempo_inferencia_ms = models.FloatField(default=0.0)
    latencia_total_ms = models.FloatField(default=0.0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Clasificación"
        verbose_name_plural = "Clasificaciones"
        ordering = ['lote', 'secuencia']
        unique_together = ('lote', 'secuencia')

    def __str__(self):
        return f"Lote {self.lote.codigo} - Sec. {self.secuencia}: {self.clase_predicha} ({self.confianza*100:.1f}%)"
