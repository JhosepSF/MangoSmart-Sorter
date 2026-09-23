from django.test import TestCase
from .models import Lote, Dispositivo

class MonitoringModelsTestCase(TestCase):
    def setUp(self):
        self.lote = Lote.objects.create(
            codigo="LOTE-TEST-001",
            nombre="Lote de Prueba"
        )
        self.dispositivo = Dispositivo.objects.create(
            lote=self.lote,
            tipo="CELULAR",
            identificador="CEL-01",
            nombre="Celular de Captura"
        )

    def test_lote_creation(self):
        self.assertEqual(self.lote.codigo, "LOTE-TEST-001")
        self.assertEqual(self.lote.estado, "CONFIGURADO")
        self.assertEqual(str(self.lote), "Lote de Prueba (LOTE-TEST-001) - CONFIGURADO")

    def test_dispositivo_creation(self):
        self.assertEqual(self.dispositivo.identificador, "CEL-01")
        self.assertFalse(self.dispositivo.conectado)
        self.assertEqual(str(self.dispositivo), "Celular de Captura [CELULAR] - Desconectado")
