import logging
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from monitoring.models import Lote
from .models import ConfiguracionSistema, EventoHardware

logger = logging.getLogger(__name__)

class HardwareStatusAPIView(APIView):
    def get(self, request):
        config = ConfiguracionSistema.objects.first()
        if not config:
            return Response({'error': 'Configuración del sistema no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({
            'puerto_serial': config.puerto_serial,
            'baudrate': config.baudrate,
            'modo_simulado': config.modo_simulado,
            'configuracion': {
                'angulo_neutral': config.angulo_neutral,
                'angulo_maduro': config.angulo_maduro,
                'angulo_inmaduro': config.angulo_inmaduro,
                'tiempo_compuerta_ms': config.tiempo_compuerta_ms,
            }
        })

class HardwareTestCommandAPIView(APIView):
    def post(self, request):
        action = request.data.get('action')
        
        if action == 'save_config':
            config_data = request.data.get('config', {})
            config, created = ConfiguracionSistema.objects.get_or_create(id=1)
            
            config.umbral_confianza = config_data.get('umbral_confianza', config.umbral_confianza)
            config.puerto_serial = config_data.get('puerto_serial', config.puerto_serial)
            config.baudrate = config_data.get('baudrate', config.baudrate)
            config.modo_simulado = config_data.get('modo_simulado', config.modo_simulado)
            config.angulo_neutral = config_data.get('angulo_neutral', config.angulo_neutral)
            config.angulo_maduro = config_data.get('angulo_maduro', config.angulo_maduro)
            config.angulo_inmaduro = config_data.get('angulo_inmaduro', config.angulo_inmaduro)
            config.tiempo_compuerta_ms = config_data.get('tiempo_compuerta_ms', config.tiempo_compuerta_ms)
            config.save()
            
            # Reiniciar ArduinoService para aplicar la nueva configuración (puerto, etc.)
            try:
                from hardware.services.arduino_service import get_arduino_service
                get_arduino_service().serial_manager.stop()
                get_arduino_service().initialize()
            except Exception as err:
                logger.warning(f"No se pudo re-inicializar el puerto serial tras guardar config: {err}")

            return Response({'status': 'success', 'message': 'Configuración guardada e interfaz serial reiniciada.'})
            
        elif action == 'test_servo':
            target = request.data.get('target') # 'mature', 'immature', 'neutral'
            
            # Traducir comandos para el protocolo del Arduino
            if target == 'neutral':
                cmd_target = 'RESET'
            elif target == 'immature':
                cmd_target = 'INMADURO'
            else:
                cmd_target = target.upper() # 'MATURE'
                
            # Enviar el comando real al puerto serial
            from hardware.services.arduino_service import get_arduino_service
            arduino_service = get_arduino_service()
            exito = arduino_service.send_sort_command(cmd_target)
            
            if exito:
                return Response({
                    'status': 'success', 
                    'message': f'Comando de prueba {cmd_target} enviado al Arduino.'
                })
            else:
                return Response({
                    'status': 'error', 
                    'message': 'El puerto serial del Arduino está desconectado o no disponible.'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        return Response({'error': 'Acción no válida'}, status=status.HTTP_400_BAD_REQUEST)

class ResetCountersAPIView(APIView):
    def post(self, request):
        # Restablece contadores borrando clasificaciones del lote
        lot_code = request.data.get('lot_code')
        if not lot_code:
            return Response({'error': 'Código de lote es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
            
        lote = get_object_or_404(Lote, codigo=lot_code)
        # Eliminar las clasificaciones del lote
        lote.clasificaciones.all().delete()
        
        return Response({'status': 'success', 'message': f'Contadores del lote {lot_code} restablecidos.'})
