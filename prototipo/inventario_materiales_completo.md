# 📋 Catálogo Oficial de Componentes y Materiales: Prototipo MangoSmart-Sorter

Este catálogo contiene el desglose técnico oficial de los 17 componentes electromecánicos, ópticos y de control utilizados para la construcción del prototipo físico clasificador de mango Khirsapat, alineado con el archivo de especificaciones `componentes.xlsx`.

---

## 🛠️ Tabla de Componentes y Materiales del Prototipo

| N.° | Componente / Material | Especificación Técnica | Función dentro del prototipo |
| :---: | :--- | :--- | :--- |
| **1** | **Placa de desarrollo Arduino Uno R3** | Basada en microcontrolador ATmega328P de 8 bits (16 MHz) | Unidad principal de control encargada de recibir la señal del sensor y ejecutar las acciones de control del servomotor. |
| **2** | **Microservomotor SG90** | Servomotor de posición angular, alimentación nominal de 5 V | Accionamiento de la compuerta de clasificación para direccionar los frutos según la categoría determinada por el sistema. |
| **3** | **Sensor infrarrojo de detección de obstáculos FC-51** | Módulo sensor IR con salida digital y sensibilidad ajustable (LM393) | Detección de la presencia del fruto en la zona de captura y activación del proceso de adquisición de imagen. |
| **4** | **Motorreductor DC JGA25-370** | Motor DC con caja reductora, tensión nominal de 12 V | Generación del movimiento necesario para el desplazamiento de la banda transportadora. |
| **5** | **Fuente de alimentación de 12 V DC / 2 A** | Salida de 12 V, corriente máxima de 2 A | Alimentación eléctrica del motorreductor de la banda transportadora. |
| **6** | **Fuente de alimentación de 5 V DC / 2 A** | Salida de 5 V, corriente máxima de 2 A | Alimentación independiente de los componentes que requieren 5 V, principalmente el servomotor, reduciendo la carga sobre la placa Arduino. |
| **7** | **Interruptor basculante redondo (Round Rocker Switch)** | Interruptor eléctrico ON/OFF | Control manual de encendido y apagado de la alimentación del sistema de transporte. |
| **8** | **Protoboard de 830 puntos** | Placa de pruebas sin soldadura | Interconexión y distribución temporal de las señales y alimentación de los componentes electrónicos. |
| **9** | **Cables puente Dupont macho–macho** | Conductores para prototipado electrónico | Interconexión entre la placa Arduino, protoboard y otros módulos electrónicos. |
| **10** | **Cables puente Dupont hembra–macho** | Conductores para prototipado electrónico | Conexión entre módulos con terminales macho y la placa/protoboard. |
| **11** | **Banda transportadora elástica** | Ancho aproximado: 10 cm (Negro mate antirreflejo) | Superficie de transporte sobre la cual se desplazan los frutos durante el proceso de clasificación. |
| **12** | **Sistema de transmisión síncrona GT2-6** | Juego de poleas y correa dentada GT2, ancho de correa de 6 mm | Transmisión del movimiento generado por el motorreductor hacia el mecanismo de la banda transportadora. |
| **13** | **Rodillo guía con recubrimiento de polímero y rodamiento integrado** | Rodillo de soporte y guiado | Guiado, soporte y reducción de la fricción durante el desplazamiento de la banda. |
| **14** | **Rueda guía metálica para riel con rodamiento** | Rueda metálica con rodamiento integrado | Soporte mecánico, alineamiento y desplazamiento de los elementos móviles del sistema. |
| **15** | **Perfil Tee Principal CKM T417** | Longitud aproximada: 1 m | Elemento estructural utilizado para el soporte y montaje del prototipo. |
| **16** | **Lámina de policarbonato** | Área aproximada utilizada: 2 m² | Construcción de superficies, soportes, protecciones y elementos estructurales del prototipo (túnel difusor y gabinete). |
| **17** | **Lámpara LED compacta con tecnología COB** | Fuente de iluminación LED de alta densidad lumínica (6 500 K) | Iluminación controlada de la zona de captura para mejorar las condiciones visuales durante la adquisición de imágenes del fruto. |
