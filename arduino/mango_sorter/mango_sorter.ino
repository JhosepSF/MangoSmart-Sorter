/**
 * MangoSmart-Sorter Firmware
 * Control de compuerta por servomotor y detección por sensor infrarrojo.
 * Incluye diagnóstico visual mediante el LED integrado (Pin 13) del Arduino Uno.
 */

#include <Servo.h>

// Definición de pines
const int PIN_IR_SENSOR = 2; // Pin digital con soporte para interrupciones
const int PIN_SERVO = 9;
const int PIN_STATUS_LED = 13; // LED_BUILTIN en Arduino Uno

// Tiempos y umbrales
const unsigned long DEBOUNCE_TIME_MS = 2000; // Evitar disparos repetidos en menos de 2s
const unsigned long ACTION_DELAY_MS = 2000;   // Tiempo que permanece abierta la compuerta

// Posiciones del servomotor (ángulos)
const int ANGULO_NEUTRAL = 90;
const int ANGULO_MADURO = 45;
const int ANGULO_INMADURO = 135;

Servo gateServo;
volatile bool mangoDetected = false;
unsigned long lastDetectionTime = 0;

void setup() {
  Serial.begin(9600);
  
  // Configurar LED integrado para feedback visual de diagnóstico
  pinMode(PIN_STATUS_LED, OUTPUT);
  digitalWrite(PIN_STATUS_LED, LOW);
  
  // Destello rápido de inicio (3 parpadeos para indicar encendido)
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_STATUS_LED, HIGH);
    delay(100);
    digitalWrite(PIN_STATUS_LED, LOW);
    delay(100);
  }
  
  // Configurar sensor IR
  pinMode(PIN_IR_SENSOR, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_IR_SENSOR), handleDetection, FALLING);
  
  // Configurar Servomotor
  gateServo.attach(PIN_SERVO);
  gateServo.write(ANGULO_NEUTRAL);
  
  // Notificar al servidor que el hardware está listo
  Serial.println("READY");
}

void loop() {
  // Procesar detección asíncrona del sensor infrarrojo
  if (mangoDetected) {
    unsigned long currentTime = millis();
    if (currentTime - lastDetectionTime > DEBOUNCE_TIME_MS) {
      lastDetectionTime = currentTime;
      Serial.println("DETECTED");
      
      // Destellar LED para indicar detección física
      digitalWrite(PIN_STATUS_LED, HIGH);
      delay(200);
      digitalWrite(PIN_STATUS_LED, LOW);
    }
    mangoDetected = false; // Resetear bandera
  }
  
  // Procesar comandos seriales entrantes
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "PING") {
      Serial.println("ACK:PING");
      
      // Parpadeo rápido para el ping
      digitalWrite(PIN_STATUS_LED, HIGH);
      delay(150);
      digitalWrite(PIN_STATUS_LED, LOW);
    } 
    else if (command == "SORT:MATURE") {
      // 1. Activar Servo
      gateServo.write(ANGULO_MADURO);
      
      // 2. Feedback LED: Encendido fijo durante el desvío
      digitalWrite(PIN_STATUS_LED, HIGH);
      delay(ACTION_DELAY_MS);
      
      // 3. Retornar a neutral
      gateServo.write(ANGULO_NEUTRAL);
      digitalWrite(PIN_STATUS_LED, LOW);
      
      Serial.println("ACK:MATURE");
    } 
    else if (command == "SORT:INMADURO" || command == "SORT:IMMATURE") {
      // 1. Activar Servo
      gateServo.write(ANGULO_INMADURO);
      
      // 2. Feedback LED: Parpadeo constante durante el desvío
      unsigned long start = millis();
      while (millis() - start < ACTION_DELAY_MS) {
        digitalWrite(PIN_STATUS_LED, HIGH);
        delay(200);
        digitalWrite(PIN_STATUS_LED, LOW);
        delay(200);
      }
      
      // 3. Retornar a neutral
      gateServo.write(ANGULO_NEUTRAL);
      digitalWrite(PIN_STATUS_LED, LOW);
      
      Serial.println("ACK:IMMATURE");
    } 
    else if (command == "SORT:REVIEW") {
      gateServo.write(ANGULO_NEUTRAL);
      
      // Feedback LED: Parpadeo lento
      digitalWrite(PIN_STATUS_LED, HIGH);
      delay(ACTION_DELAY_MS / 2);
      digitalWrite(PIN_STATUS_LED, LOW);
      delay(ACTION_DELAY_MS / 2);
      
      Serial.println("ACK:REVIEW");
    } 
    else if (command == "RESET") {
      gateServo.write(ANGULO_NEUTRAL);
      digitalWrite(PIN_STATUS_LED, LOW);
      Serial.println("ACK:RESET");
    } 
    else {
      Serial.println("ERROR:UNKNOWN_COMMAND");
    }
  }
}

// Interrupción para detección de flanco de bajada (presencia de mango)
void handleDetection() {
  mangoDetected = true;
}
