from django.apps import AppConfig


import os
import sys
import logging

logger = logging.getLogger(__name__)

class HardwareConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hardware'

    def ready(self):
        # Solo inicializar en el arranque del servidor, no durante migraciones o comandos
        if any(cmd in sys.argv for cmd in ['runserver', 'runsslserver']):
            # Django runserver arranca dos procesos: el padre (auto-reloader) y el hijo (ejecución real).
            # Para evitar abrir el puerto serial dos veces y generar 'Acceso denegado',
            # solo inicializamos en el proceso hijo (RUN_MAIN=true) o si se ejecuta con --noreload.
            if os.environ.get('RUN_MAIN') == 'true' or '--noreload' in sys.argv:
                try:
                    from .services.arduino_service import get_arduino_service
                    get_arduino_service().initialize()
                except Exception as e:
                    logger.warning(f"No se pudo inicializar ArduinoService al arranque: {e}")

