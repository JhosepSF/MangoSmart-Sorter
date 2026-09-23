import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from monitoring.models import Lote, Dispositivo
from classification.models import Clasificacion
from hardware.models import ConfiguracionSistema, EventoHardware

class LotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.codigo_lote = self.scope['url_route']['kwargs']['codigo_lote']
        self.room_group_name = f'lot_{self.codigo_lote}'
        
        # Obtener el tipo de dispositivo desde los parámetros de consulta (?device=mobile/dashboard)
        query_params = self.scope.get('query_string', b'').decode('utf-8')
        params = dict(qc.split('=') for qc in query_params.split('&') if '=' in qc)
        self.device_type = params.get('device', 'unknown').upper()
        self.device_id = f"{self.device_type}_{self.channel_name[-8:]}"

        # Verificar si el lote existe en la base de datos
        lote_exists = await self.check_lote_exists(self.codigo_lote)
        if not lote_exists:
            await self.close()
            return

        # Registrar dispositivo como conectado en la BD
        await self.update_device_status(self.codigo_lote, self.device_type, self.device_id, conectado=True)

        # Unirse al grupo del lote y al grupo global (para eventos de hardware)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_add(
            'global',
            self.channel_name
        )
        await self.accept()

        # Notificar al grupo que un nuevo dispositivo se ha conectado
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'device_status_event',
                'device': self.device_type,
                'connected': True
            }
        )
        
        # Enviar estados de los demás dispositivos conectados para sincronización inicial
        active_devices = await self.get_active_devices(self.codigo_lote)
        for dev in active_devices:
            if dev['tipo'] != self.device_type:
                await self.send(text_data=json.dumps({
                    'type': 'device_status',
                    'device': dev['tipo'].lower(),
                    'connected': dev['conectado']
                }))

    async def disconnect(self, close_code):
        # Desregistrar dispositivo en la BD
        await self.update_device_status(self.codigo_lote, self.device_type, self.device_id, conectado=False)

        # Notificar al grupo que el dispositivo se ha desconectado
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'device_status_event',
                'device': self.device_type,
                'connected': False
            }
        )

        # Salir de los grupos del lote y global
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            'global',
            self.channel_name
        )

    # Recibir mensajes desde el WebSocket del cliente
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'request_manual_capture':
                # Crear un registro PENDIENTE en el backend para asignarle un sequence_id
                classification_id, seq = await self.create_pending_classification(self.codigo_lote)
                
                # Enviar orden de captura al grupo (el celular la recibirá)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'capture_request_event',
                        'classification_id': classification_id,
                        'lot_code': self.codigo_lote,
                        'sequence': seq
                    }
                )

            elif action == 'test_servo_command':
                target = data.get('target') # 'mature', 'immature', 'neutral'
                # Disparar comando al ArduinoService (Fase 6)
                await self.trigger_servo_command(target)
                
                # Notificar a los supervisores
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'hardware_status_event',
                        'command': f"SORT:{target.upper()}",
                        'acknowledged': True
                    }
                )
                
            elif action == 'pause_conveyor':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'conveyor_status_event',
                        'status': 'PAUSED'
                    }
                )
                
            elif action == 'resume_conveyor':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'conveyor_status_event',
                        'status': 'ACTIVE'
                    }
                )

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    # Eventos del canal (Channel layer handlers)

    async def device_status_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'device_status',
            'device': event['device'].lower(),
            'connected': event['connected']
        }))

    async def capture_request_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'capture_request',
            'classification_id': event['classification_id'],
            'lot_code': event['lot_code'],
            'sequence': event['sequence']
        }))

    async def classification_result_event(self, event):
        # Envía el resultado al cliente
        await self.send(text_data=json.dumps(event['data']))

    async def hardware_status_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'hardware_status',
            'command': event['command'],
            'acknowledged': event['acknowledged']
        }))

    async def conveyor_status_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'conveyor_status',
            'status': event['status']
        }))


    # Métodos síncronos envueltos en database_sync_to_async

    @database_sync_to_async
    def check_lote_exists(self, lot_code):
        return Lote.objects.filter(codigo=lot_code).exists()

    @database_sync_to_async
    def update_device_status(self, lot_code, device_type, device_id, conectado):
        try:
            lote = Lote.objects.get(codigo=lot_code)
            # Buscar dispositivo del mismo tipo en este lote, o crearlo
            device, created = Dispositivo.objects.get_or_create(
                lote=lote,
                tipo=device_type,
                defaults={
                    'identificador': device_id,
                    'nombre': f"{device_type.capitalize()} de Lote {lot_code}"
                }
            )
            device.conectado = conectado
            device.ultima_conexion = timezone.now()
            device.save()
        except Exception as e:
            print("Error actualizando estado del dispositivo en DB:", e)

    @database_sync_to_async
    def get_active_devices(self, lot_code):
        lote = Lote.objects.get(codigo=lot_code)
        devices = Dispositivo.objects.filter(lote=lote)
        return [{'tipo': dev.tipo, 'conectado': dev.conectado} for dev in devices]

    @database_sync_to_async
    def create_pending_classification(self, lot_code):
        lote = Lote.objects.get(codigo=lot_code)
        seq = lote.clasificaciones.count() + 1
        clasificacion = Clasificacion.objects.create(
            lote=lote,
            secuencia=seq,
            estado='PENDIENTE'
        )
        return clasificacion.id, seq

    @database_sync_to_async
    def trigger_servo_command(self, target):
        # Guardar evento de hardware en la base de datos
        # Esto disparará el desvío serial si el servicio está activo
        try:
            from hardware.services.arduino_service import get_arduino_service
            arduino_service = get_arduino_service()
            arduino_service.send_sort_command(target.upper())
        except Exception as e:
            print("Error disparando comando servo desde WebSocket:", e)
