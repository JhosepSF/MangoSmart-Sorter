import time
import logging
import threading
import serial
from django.conf import settings
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class SerialManager:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.serial_port = None
        self.port_name = None
        self.baudrate = 9600
        self.timeout = 2.0
        self.is_running = False
        self.read_thread = None
        self.simulated = True
        self.pending_event_id = None

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def configure(self, port_name, baudrate, timeout=2.0, simulated=True):
        self.port_name = port_name
        self.baudrate = baudrate
        self.timeout = timeout
        self.simulated = simulated
        logger.info(f"Configurando SerialManager: Puerto={port_name}, Baudrate={baudrate}, Simulado={simulated}")

    def start(self):
        with self._lock:
            if self.is_running:
                return
            
            self.is_running = True
            self.read_thread = threading.Thread(target=self._read_loop, name="ArduinoSerialReader", daemon=True)
            self.read_thread.start()
            logger.info("Hilo de lectura serial de Arduino iniciado.")

    def stop(self):
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception as e:
                logger.error(f"Error cerrando puerto serial: {e}")
        self.serial_port = None
        logger.info("Hilo de lectura serial de Arduino detenido.")

    def write(self, command):
        """Envía un comando al Arduino."""
        if not command.endswith('\n'):
            command += '\n'
            
        logger.info(f"Enviando comando serial: {command.strip()}")

        if self.simulated:
            import sys
            # En pruebas unitarias ejecutamos síncronamente para evitar bloqueos en SQLite
            if 'test' in sys.argv:
                self._simulate_ack(command.strip())
            else:
                # Simular respuesta en un hilo separado para no bloquear en ejecución real
                threading.Thread(target=self._simulate_ack, args=(command.strip(),), daemon=True).start()
            return True


        # Modo Real
        try:
            if not self.serial_port or not self.serial_port.is_open:
                self._connect()
                
            if self.serial_port and self.serial_port.is_open:
                with self._lock:
                    self.serial_port.write(command.encode('utf-8'))
                    self.serial_port.flush()
                return True
        except Exception as e:
            logger.error(f"Error escribiendo en puerto serial {self.port_name}: {e}")
            self.stop()
            
        return False

    def _connect(self):
        if self.simulated:
            return
            
        try:
            if self.serial_port and self.serial_port.is_open:
                return
                
            logger.info(f"Conectando al puerto serial {self.port_name}...")
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2) # Esperar a que Arduino se reinicie tras conectar
            logger.info(f"Conexión exitosa al puerto {self.port_name}.")
            # Notificar estado conectado
            self._broadcast_hardware_status(connected=True)
        except Exception as e:
            logger.error(f"Error conectando al puerto {self.port_name}: {e}")
            self.serial_port = None
            self._broadcast_hardware_status(connected=False)

    def _read_loop(self):
        while self.is_running:
            if self.simulated:
                # En modo simulado, el loop de lectura no hace nada continuo
                # Las simulaciones son disparadas por eventos o comandos
                time.sleep(1.0)
                continue

            # Modo Real
            try:
                if not self.serial_port or not self.serial_port.is_open:
                    self._connect()
                    if not self.serial_port:
                        time.sleep(5.0) # Esperar antes de intentar reconectar
                        continue

                # Leer línea
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line:
                        logger.info(f"Arduino dice: {line}")
                        self._handle_incoming_message(line)
            except Exception as e:
                logger.error(f"Error leyendo del puerto serial: {e}")
                self._broadcast_hardware_status(connected=False)
                self.serial_port = None
                time.sleep(2.0)

    def _handle_incoming_message(self, message):
        """Procesa mensajes entrantes desde Arduino."""
        if message == "READY":
            self._broadcast_hardware_status(connected=True)
            
        elif message == "DETECTED":
            # Detección de mango automática
            self._trigger_automatic_capture()
            
        elif message.startswith("ACK:"):
            # Confirmación de desvío
            ack_type = message.split(":")[1]
            self._confirm_pending_event(ack_type)
            
        elif message.startswith("ERROR:"):
            # Error de hardware
            logger.error(f"Arduino reportó error: {message}")

    def _trigger_automatic_capture(self):
        """Registra la detección e inicia la solicitud de captura en los clientes."""
        try:
            from monitoring.models import Lote
            from classification.models import Clasificacion
            
            # Buscar lote activo
            lote_activo = Lote.objects.filter(estado='ACTIVO').first()
            if not lote_activo:
                logger.warning("Mango detectado pero no hay ningún lote ACTIVO configurado.")
                return

            # Crear clasificación en base de datos
            seq = lote_activo.clasificaciones.count() + 1
            clasificacion = Clasificacion.objects.create(
                lote=lote_activo,
                secuencia=seq,
                estado='PENDIENTE'
            )

            # Enviar evento de captura por WebSocket
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'lot_{lote_activo.codigo}',
                    {
                        'type': 'capture_request_event',
                        'classification_id': clasificacion.id,
                        'lot_code': lote_activo.codigo,
                        'sequence': seq
                    }
                )
            logger.info(f"Detección física de mango registrada. Secuencia: #{seq}, Lote: {lote_activo.codigo}")
        except Exception as e:
            logger.error(f"Error al procesar la detección automática: {e}")

    def _confirm_pending_event(self, ack_type):
        """Busca el último evento de hardware pendiente y lo confirma en la base de datos."""
        try:
            from hardware.models import EventoHardware
            # Buscar el último evento no confirmado para comandos del tipo SORT
            evento = EventoHardware.objects.filter(confirmado=False).order_by('-fecha_envio').first()
            if evento:
                evento.respuesta = f"ACK:{ack_type}"
                evento.confirmado = True
                evento.fecha_respuesta = timezone.now()
                if evento.fecha_envio:
                    evento.tiempo_respuesta_ms = (evento.fecha_respuesta - evento.fecha_envio).total_seconds() * 1000
                evento.save()
                logger.info(f"Evento ID {evento.id} confirmado por Arduino con respuesta: ACK:{ack_type}")
                
                # Avisar al dashboard de la confirmación
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'lot_{evento.clasificacion.lote.codigo}' if evento.clasificacion else 'global',
                        {
                            'type': 'hardware_status_event',
                            'command': evento.comando,
                            'acknowledged': True
                        }
                    )
        except Exception as e:
            logger.error(f"Error confirmando evento de hardware: {e}")

    def _broadcast_hardware_status(self, connected):
        """Notifica por WebSocket del cambio de estado del Arduino."""
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'global', # O mandar a todos los grupos de lotes activos
                    {
                        'type': 'device_status_event',
                        'device': 'ARDUINO',
                        'connected': connected
                    }
                )
        except Exception as e:
            logger.warning(f"Error notificando estado de Arduino: {e}")

    # --- Métodos de Simulación ---

    def _simulate_ack(self, command):
        """Simula las respuestas del Arduino."""
        time.sleep(0.5) # Simular latencia de red serial
        
        if command == "PING":
            logger.info("Simulando Arduino respuesta: ACK:PING")
            self._confirm_pending_event("PING")
        elif command == "SORT:MATURE":
            logger.info("Simulando Arduino respuesta: ACK:MATURE")
            self._confirm_pending_event("MATURE")
        elif command == "SORT:INMADURO" or command == "SORT:IMMATURE":
            logger.info("Simulando Arduino respuesta: ACK:IMMATURE")
            self._confirm_pending_event("IMMATURE")
        elif command == "SORT:REVIEW":
            logger.info("Simulando Arduino respuesta: ACK:REVIEW")
            self._confirm_pending_event("REVIEW")
        elif command == "RESET":
            logger.info("Simulando Arduino respuesta: ACK:RESET")
            self._confirm_pending_event("RESET")
