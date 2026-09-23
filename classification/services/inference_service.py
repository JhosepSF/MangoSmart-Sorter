import os
import time
import logging
from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

class InferenceService:
    _instance = None
    model = None
    config = None
    mode = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(InferenceService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def initialize(self):
        """Inicializa el modelo de forma perezosa una sola vez."""
        if self.model is not None:
            return

        self.mode = getattr(settings, 'ML_MODEL_MODE', 'mock').lower()
        
        if self.mode == 'real':
            model_path = getattr(settings, 'ML_MODEL_PATH', 'ml_models/ConvNeXtTiny_madurez_mango_final.keras')
            config_path = getattr(settings, 'ML_CONFIG_PATH', 'ml_models/ConvNeXtTiny_madurez_mango.config.json')
            
            logger.info(f"Cargando modelo real Keras desde: {model_path}")
            
            # Validar que los archivos existan
            if not os.path.exists(model_path):
                logger.error(f"Archivo de modelo no encontrado en {model_path}. Cambiando a modo SIMULADO.")
                self.mode = 'mock'
                return

            try:
                import tensorflow as tf
                # Cargar modelo Keras
                self.model = tf.keras.models.load_model(model_path, compile=False)
                
                # Cargar configuración si existe
                if os.path.exists(config_path):
                    import json
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self.config = json.load(f)
                else:
                    self.config = {
                        "class_names": ["Inmaduro", "Maduro"],
                        "image_size": 224
                    }
                logger.info("Modelo ConvNeXt-Tiny Keras cargado exitosamente.")
            except Exception as e:
                logger.error(f"Error cargando modelo TensorFlow/Keras: {e}. Cambiando a modo SIMULADO.")
                self.mode = 'mock'

    def predict(self, image_path):
        """Ejecuta la predicción sobre la imagen proporcionada."""
        self.initialize()
        
        start_time = time.time()
        
        if self.mode == 'mock':
            # Simulación de Inferencia
            preprocess_time_ms = 10.0
            time.sleep(0.12) # Simular latencia de inferencia de 120ms
            inference_time_ms = 120.0
            
            import random
            # Alternar o predecir con confianza aleatoria
            clase_predicha = random.choice(['MADURO', 'INMADURO'])
            confianza = round(random.uniform(0.75, 0.98), 3)
            
            prob_maduro = confidence_val = confianza if clase_predicha == 'MADURO' else round(1.0 - confianza, 3)
            prob_inmaduro = confidence_val if clase_predicha == 'INMADURO' else round(1.0 - confianza, 3)
            latencia_total_ms = (time.time() - start_time) * 1000

            return {
                'clase_predicha': clase_predicha,
                'confianza': confianza,
                'probabilidad_maduro': prob_maduro,
                'probabilidad_inmaduro': prob_inmaduro,
                'tiempo_preprocesamiento_ms': preprocess_time_ms,
                'tiempo_inferencia_ms': inference_time_ms,
                'latencia_total_ms': latencia_total_ms
            }

        else:
            # Inferencia Real usando TensorFlow
            try:
                import tensorflow as tf
                
                # 1. Preprocesamiento exactamente igual al Jupyter Notebook
                # Cargar imagen y decodificarla como RGB
                preprocess_start = time.time()
                imagen_raw = tf.io.read_file(image_path)
                imagen = tf.io.decode_image(imagen_raw, channels=3, expand_animations=False)
                imagen.set_shape([None, None, 3])
                # Redimensionar usando interpolación bilineal a 224x224
                imagen = tf.image.resize(imagen, (224, 224), method="bilinear")
                imagen = tf.cast(imagen, tf.float32)
                # Expandir dimensiones para formar el batch de tamaño 1
                imagen = tf.expand_dims(imagen, 0)
                preprocess_time_ms = (time.time() - preprocess_start) * 1000
                
                # 2. Inferencia
                inference_start = time.time()
                # Usar llamada directa al modelo (training=False) en lugar de predict()
                # para evitar impresiones progresivas en consola y overhead de tracking
                pred = self.model(imagen, training=False)
                inference_time_ms = (time.time() - inference_start) * 1000
                
                # Extraer probabilidad binaria (Sigmoid)
                prob_maduro = float(pred[0][0])
                prob_inmaduro = 1.0 - prob_maduro
                
                # Determinar clase y confianza
                # 0 = Inmaduro, 1 = Maduro
                if prob_maduro >= 0.5:
                    clase_predicha = 'MADURO'
                    confianza = prob_maduro
                else:
                    clase_predicha = 'INMADURO'
                    confianza = prob_inmaduro
                    
                latencia_total_ms = (time.time() - start_time) * 1000
                
                return {
                    'clase_predicha': clase_predicha,
                    'confianza': round(confianza, 4),
                    'probabilidad_maduro': round(prob_maduro, 4),
                    'probabilidad_inmaduro': round(prob_inmaduro, 4),
                    'tiempo_preprocesamiento_ms': round(preprocess_time_ms, 2),
                    'tiempo_inferencia_ms': round(inference_time_ms, 2),
                    'latencia_total_ms': round(latencia_total_ms, 2)
                }
            except Exception as e:
                logger.error(f"Error durante inferencia real TensorFlow: {e}. Reintentando con mock.")
                # Fallback de seguridad si algo falla
                preprocess_time_ms = 5.0
                inference_time_ms = 50.0
                latencia_total_ms = (time.time() - start_time) * 1000
                return {
                    'clase_predicha': 'REVISION',
                    'confianza': 0.0,
                    'probabilidad_maduro': 0.0,
                    'probabilidad_inmaduro': 0.0,
                    'tiempo_preprocesamiento_ms': preprocess_time_ms,
                    'tiempo_inferencia_ms': inference_time_ms,
                    'latencia_total_ms': latencia_total_ms,
                    'error': str(e)
                }
