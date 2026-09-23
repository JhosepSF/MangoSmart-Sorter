from django.db import models
from django.utils import timezone

class Lote(models.Model):
    ESTADOS = [
        ('CONFIGURADO', 'Configurado'),
        ('ACTIVO', 'Activo'),
        ('PAUSADO', 'Pausado'),
        ('FINALIZADO', 'Finalizado'),
    ]

    codigo = models.CharField(max_length=50, unique=True, db_index=True)
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='CONFIGURADO')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.nombre} ({self.codigo}) - {self.estado}"


class Dispositivo(models.Model):
    TIPOS = [
        ('CELULAR', 'Celular'),
        ('DASHBOARD', 'Dashboard'),
        ('ARDUINO', 'Arduino'),
    ]

    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispositivos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    identificador = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100)
    conectado = models.BooleanField(default=False)
    ultima_conexion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"

    def __str__(self):
        return f"{self.nombre} [{self.tipo}] - {'Conectado' if self.conectado else 'Desconectado'}"
