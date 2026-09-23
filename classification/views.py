import os
import uuid
import time
import logging
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from monitoring.models import Lote
from hardware.models import ConfiguracionSistema, EventoHardware
from .models import Clasificacion
from .serializers import ClasificacionSerializer
from .services.inference_service import InferenceService

logger = logging.getLogger(__name__)

class ClassificationCaptureAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # 1. Obtener parámetros
        imagen_file = request.FILES.get('imagen')
        lot_code = request.data.get('lot_code')
        classification_id = request.data.get('classification_id')

        # 2. Validaciones iniciales
        if not imagen_file:
            return Response({'error': 'La imagen es requerida.'}, status=status.HTTP_400_BAD_REQUEST)
        if not lot_code:
            return Response({'error': 'El código de lote es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Validar existencia del lote
        lote = get_object_or_404(Lote, codigo=lot_code)

        # 4. Validar formato y tamaño de la imagen
        ext = os.path.splitext(imagen_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            return Response({'error': 'Formato de imagen no permitido. Use JPEG, PNG o WebP.'}, status=status.HTTP_400_BAD_REQUEST)

        max_size_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if imagen_file.size > max_size_bytes:
            return Response({'error': f'El tamaño de la imagen supera el límite de {settings.MAX_IMAGE_SIZE_MB}MB.'}, status=status.HTTP_400_BAD_REQUEST)

        # 5. Generar nombre de archivo seguro y único
        unique_filename = f"{lote.codigo}_{uuid.uuid4().hex}{ext}"
        imagen_file.name = unique_filename

        # Recordar el tiempo de inicio para calcular latencia total del request
        request_start_time = time.time()

        # 6. Determinar el número de secuencia
        total_classifications = lote.clasificaciones.count()
        sequence = total_classifications + 1

        # 7. Crear o recuperar el registro
        if classification_id:
            try:
                clasificacion = Clasificacion.objects.get(id=classification_id, lote=lote)
                clasificacion.imagen_original = imagen_file
                clasificacion.estado = 'PROCESANDO'
            except Clasificacion.DoesNotExist:
                clasificacion = Clasificacion.objects.create(
                    lote=lote,
                    secuencia=sequence,
                    imagen_original=imagen_file,
                    estado='PROCESANDO'
                )
        else:
            clasificacion = Clasificacion.objects.create(
                lote=lote,
                secuencia=sequence,
                imagen_original=imagen_file,
                estado='PROCESANDO'
            )

        # Guardar para almacenar el archivo físico
        clasificacion.save()

        # 8. Ejecutar inferencia real o mock
        try:
            inference_service = InferenceService()
            result = inference_service.predict(clasificacion.imagen_original.path)
            
            clase_predicha = result['clase_predicha']
            confianza = result['confianza']
            prob_maduro = result['probabilidad_maduro']
            prob_inmaduro = result['probabilidad_inmaduro']
            preprocess_time_ms = result['tiempo_preprocesamiento_ms']
            inference_time_ms = result['tiempo_inferencia_ms']
        except Exception as e:
            logger.error(f"Error llamando al servicio de inferencia: {e}")
            clase_predicha = 'REVISION'
            confianza = 0.0
            prob_maduro = 0.0
            prob_inmaduro = 0.0
            preprocess_time_ms = 0.0
            inference_time_ms = 0.0

        # 9. Lógica de umbral y validación de clasificación
        config = ConfiguracionSistema.objects.first()
        threshold = config.umbral_confianza if config else 0.80

        # Si el modelo tiene baja confianza, se clasifica forzadamente como REVISION / RECHAZADO
        if confianza < threshold:
            clasificacion.clase_predicha = 'REVISION'
            clasificacion.estado = 'RECHAZADO'
        else:
            clasificacion.clase_predicha = clase_predicha
            clasificacion.estado = 'CLASIFICADO'

        # Calcular latencia total de la operación en backend
        latencia_total_ms = (time.time() - request_start_time) * 1000

        clasificacion.confianza = confianza
        clasificacion.probabilidad_maduro = prob_maduro
        clasificacion.probabilidad_inmaduro = prob_inmaduro
        clasificacion.tiempo_preprocesamiento_ms = preprocess_time_ms
        clasificacion.tiempo_inferencia_ms = inference_time_ms
        clasificacion.latencia_total_ms = latencia_total_ms
        clasificacion.save()

        # 10. Notificar vía WebSockets si está habilitado en los siguientes pasos (Fase 5)
        # Esto enviará la clasificación al canal del lote en tiempo real.
        # Haremos una llamada segura para evitar errores si Channels no está completamente enlazado.
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                # Obtener estadísticas actualizadas del lote
                maduros = lote.clasificaciones.filter(clase_predicha='MADURO', estado='CLASIFICADO').count()
                inmaduros = lote.clasificaciones.filter(clase_predicha='INMADURO', estado='CLASIFICADO').count()
                revision = lote.clasificaciones.filter(clase_predicha='REVISION').count() + \
                           lote.clasificaciones.filter(estado='RECHAZADO').count()
                total = lote.clasificaciones.count()
                
                async_to_sync(channel_layer.group_send)(
                    f'lot_{lote.codigo}',
                    {
                        'type': 'classification_result_event',
                        'data': {
                            'type': 'classification_result',
                            'classification_id': clasificacion.id,
                            'class_name': clasificacion.clase_predicha,
                            'confidence': clasificacion.confianza,
                            'probabilities': {
                                'Maduro': clasificacion.probabilidad_maduro,
                                'Inmaduro': clasificacion.probabilidad_inmaduro
                            },
                            'inference_ms': round(clasificacion.tiempo_inferencia_ms, 1),
                            'preprocess_ms': round(clasificacion.tiempo_preprocesamiento_ms, 1),
                            'total_ms': round(clasificacion.latencia_total_ms, 1),
                            'image_url': clasificacion.imagen_original.url,
                            'sequence': clasificacion.secuencia,
                            'total_mature': maduros,
                            'total_immature': inmaduros,
                            'total_review': revision,
                            'total_processed': total
                        }
                    }
                )
        except Exception as ws_err:
            logger.warning(f"No se pudo enviar notificación por WebSocket: {ws_err}")

        # 11. Disparar comando físico de desvío automático de compuerta si está en modo clasificado (Fase 6/7)
        # Esto enviará un comando al ArduinoService en el flujo integrado.
        if clasificacion.estado == 'CLASIFICADO':
            try:
                from hardware.services.arduino_service import get_arduino_service
                arduino_service = get_arduino_service()
                # El comando depende del resultado
                command_target = 'MATURE' if clasificacion.clase_predicha == 'MADURO' else 'IMMATURE'
                # Disparar asíncronamente
                arduino_service.send_sort_command(command_target, clasificacion.id)
            except Exception as hw_err:
                logger.warning(f"No se pudo enviar comando al Arduino: {hw_err}")
        elif clasificacion.estado == 'RECHAZADO':
            try:
                from hardware.services.arduino_service import get_arduino_service
                arduino_service = get_arduino_service()
                arduino_service.send_sort_command('REVIEW', clasificacion.id)
            except Exception as hw_err:
                logger.warning(f"No se pudo enviar comando de revisión al Arduino: {hw_err}")

        serializer = ClasificacionSerializer(clasificacion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClassificationDetailAPIView(APIView):
    def get(self, request, pk):
        clasificacion = get_object_or_404(Clasificacion, pk=pk)
        serializer = ClasificacionSerializer(clasificacion)
        return Response(serializer.data)
