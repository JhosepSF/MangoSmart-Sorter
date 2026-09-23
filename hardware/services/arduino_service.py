import logging
from django.utils import timezone
from django.conf import settings
from .serial_manager import SerialManager

logger = logging.getLogger(__name__)

class ArduinoService:
    _instance = None
    serial_manager = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ArduinoService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def initialize(self):
        """Inicializa la configuración y arranca el hilo del lector serial."""
        if self.serial_manager is None:
            self.serial_manager = SerialManager.get_instance()

        try:
            # Importación local para evitar AppRegistryNotReady en Django ready()
            from hardware.models import ConfiguracionSistema
            config, created = ConfiguracionSistema.objects.get_or_create(id=1)
            
            # Cargar variables de entorno configuradas desde .env
            port_name = getattr(settings, 'ARDUINO_PORT', 'COM3')
            baudrate = getattr(settings, 'ARDUINO_BAUDRATE', 9600)
            modo_simulado = getattr(settings, 'ARDUINO_MODE', 'mock').lower() == 'mock'
            
            # Sincronizar la fila de la BBDD con las variables de entorno de .env
            if created or config.puerto_serial != port_name or config.baudrate != baudrate or config.modo_simulado != modo_simulado:
                config.puerto_serial = port_name
                config.baudrate = baudrate
                config.modo_simulado = modo_simulado
                config.save()
                logger.info(f"Configuración de hardware sincronizada con el archivo .env: Puerto={port_name}, Simulado={modo_simulado}")

            self.serial_manager.configure(
                port_name=config.puerto_serial,
                baudrate=config.baudrate,
                timeout=2.0,
                simulated=modo_simulado
            )
            self.serial_manager.start()
            logger.info("ArduinoService inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar ArduinoService: {e}")

    def send_sort_command(self, target, classification_id=None):
        """Envía el comando de desvío al Arduino y registra el evento de hardware en la BD."""
        self.initialize()
        
        target = target.upper()
        # Mapear target en el protocolo
        if target in ['RESET', 'PING']:
            cmd = target
        else:
            cmd = f"SORT:{target}"

        
        # Importaciones locales para evitar AppRegistryNotReady
        from hardware.models import EventoHardware
        from classification.models import Clasificacion

        clasificacion_obj = None
        if classification_id:
            try:
                clasificacion_obj = Clasificacion.objects.get(id=classification_id)
            except Clasificacion.DoesNotExist:
                pass

        # Crear registro de evento en BBDD
        evento = EventoHardware.objects.create(
            clasificacion=clasificacion_obj,
            comando=cmd,
            fecha_envio=timezone.now(),
            confirmado=False
        )

        # Enviar vía serial
        exito = self.serial_manager.write(cmd)
        
        if not exito:
            evento.mensaje_error = "Error al escribir en el puerto serial."
            evento.save()
            logger.error(f"Fallo al enviar comando serial {cmd}.")
        
        return exito

    def simulate_mango_detection(self):
        """Simula físicamente la señal de DETECTED recibida del sensor infrarrojo."""
        self.initialize()
        logger.info("Simulando trigger de detección de mango infrarrojo.")
        self.serial_manager._trigger_automatic_capture()

def get_arduino_service():
    service = ArduinoService()
    return service
