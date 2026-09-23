import time
from django.test import TransactionTestCase
from django.utils import timezone
from monitoring.models import Lote
from classification.models import Clasificacion
from .models import EventoHardware, ConfiguracionSistema
from .services.arduino_service import get_arduino_service

class HardwareModelsTestCase(TransactionTestCase):
    def setUp(self):
        self.lote = Lote.objects.create(
            codigo="LOTE-TEST-003",
            nombre="Lote de Prueba Hardware"
        )
        self.clasificacion = Clasificacion.objects.create(
            lote=self.lote,
            secuencia=1,
            clase_predicha="INMADURO",
            confianza=0.88,
            probabilidad_maduro=0.12,
            probabilidad_inmaduro=0.88,
            estado="CLASIFICADO"
        )
        self.evento = EventoHardware.objects.create(
            clasificacion=self.clasificacion,
            comando="SORT:IMMATURE",
            respuesta="ACK:IMMATURE",
            confirmado=True
        )
        # Forzar configuración en modo simulado para pruebas
        self.config = ConfiguracionSistema.objects.create(
            umbral_confianza=0.80,
            puerto_serial="COM3",
            baudrate=9600,
            modo_simulado=True
        )

    def test_evento_hardware_creation(self):
        self.assertEqual(self.evento.comando, "SORT:IMMATURE")
        self.assertEqual(self.evento.respuesta, "ACK:IMMATURE")
        self.assertTrue(self.evento.confirmado)
        self.assertEqual(str(self.evento), "Comando SORT:IMMATURE - Estado: Confirmado")

    def test_configuracion_singleton(self):
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)
        config2 = ConfiguracionSistema(umbral_confianza=0.75, puerto_serial="COM9")
        config2.save()
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)
        
        config_db = ConfiguracionSistema.objects.first()
        self.assertEqual(config_db.umbral_confianza, 0.75)
        self.assertEqual(config_db.puerto_serial, "COM9")

    def test_arduino_service_sort_command_simulated(self):
        service = get_arduino_service()
        # Forzar configuración simulada en el servicio
        service.serial_manager.configure(
            port_name="COM3",
            baudrate=9600,
            timeout=2.0,
            simulated=True
        )
        service.serial_manager.start()
        
        # Enviar comando
        exito = service.send_sort_command('MATURE', self.clasificacion.id)
        self.assertTrue(exito)
        
        # En modo de prueba unitaria se ejecuta síncronamente, por lo que el evento
        # ya debe estar confirmado en la base de datos de inmediato.
        evento = EventoHardware.objects.filter(comando="SORT:MATURE").order_by('-fecha_envio').first()
        self.assertIsNotNone(evento)
        self.assertTrue(evento.confirmado)
        self.assertEqual(evento.respuesta, "ACK:MATURE")
        self.assertGreater(evento.tiempo_respuesta_ms, 0)
        
        # Apagar lector
        service.serial_manager.stop()

