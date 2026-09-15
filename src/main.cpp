// --- LIBRERÍAS ---
#include <Arduino.h>
#include "HX711.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h" 

// --- CONFIGURACIÓN DE PANTALLA Y BÁSCULA ---
Adafruit_SSD1306 pantalla(128, 64, &Wire, -1);
HX711 bascula;

// --- PINES DE CONEXIÓN ---
const int buzzer = 12;
const int loadcellDT = 19;
const int loadcellSCK = 18;

// --- CONSTANTES Y PARÁMETROS DEL SISTEMA (PDF 2.3) ---
const int umbral = 2000;
const int margen = 12;
int contador = 0;
int pesoActual = 0;

// --- CONTROL DE TEMPORIZADORES (millis) ---
unsigned long tiempoAnteriorMuestreo = 0;
const unsigned long intervaloMuestreo = 900; 

unsigned long tiempoAnteriorPublicacion = 0;
const unsigned long periodoPublicacion = 21000; 

unsigned long tiempoAnteriorReconexion = 0;
const unsigned long intervaloReconexion = 3000; 

// --- ESTADOS DEL SISTEMA ---
String modoActual = "AUTO"; 
bool alarmaActiva = false; 

// --- CONFIGURACIÓN MQTT ---
WiFiClient espClient;
PubSubClient mqttClient(espClient);

const char* device_ID = "IOT-B8982F65F7";
const char* topic_telemetria = "iot/b8982f65f7/telemetry";
const char* topic_comando = "iot/b8982f65f7/command";

int secuenciaJSON = 1;

// --- DECLARACIÓN DE FUNCIONES ---
void reconnectMQTT_WiFi();
void publishMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int len);

// --- SETUP ---
void setup() {
  Serial.begin(115200);
  Serial.println("Iniciando sistema...");
  
  pinMode(buzzer, OUTPUT); 
  digitalWrite(buzzer, LOW); // Estado seguro al arrancar

  bascula.begin(loadcellDT, loadcellSCK); 
  bascula.set_scale(0.42);

  pantalla.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  pantalla.clearDisplay();
  pantalla.setTextSize(1);
  pantalla.setTextColor(WHITE);
  pantalla.setCursor(34, 25); 
  pantalla.print("BIENVENIDO");
  pantalla.display();
  delay(2000); 

  // Iniciar configuración MQTT apuntando a HiveMQ
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  pantalla.clearDisplay();
  pantalla.setCursor(5, 25);
  pantalla.print("SISTEMA LISTO");
  pantalla.display();
  delay(1000);
}

// --- LOOP PRINCIPAL ---
void loop() {
  unsigned long tiempoActual = millis();

  // 1. TAREA DE RED: Reconexión no bloqueante
  if (!mqttClient.connected()) {
    if (tiempoActual - tiempoAnteriorReconexion >= intervaloReconexion) {
      tiempoAnteriorReconexion = tiempoActual;
      reconnectMQTT_WiFi();
    }
  } else {
    mqttClient.loop(); // Mantiene vivo el hilo MQTT para recibir comandos
  }

  // 2. TAREA LOCAL: Muestreo del Sensor
  if (tiempoActual - tiempoAnteriorMuestreo >= intervaloMuestreo) {
    tiempoAnteriorMuestreo = tiempoActual; 

    int lecturaBascula = bascula.get_units();

    // Validación de dato inválido
    if (lecturaBascula < -500 || lecturaBascula > 6000) {
      Serial.println("Error: Lectura fuera de rango admisible.");
      return; 
    }
    pesoActual = lecturaBascula; 

    // Interfaz gráfica
    pantalla.clearDisplay();
    pantalla.setTextColor(WHITE);
    pantalla.setTextSize(1);
    pantalla.setCursor(19, 5);
    pantalla.print("Peso Detectado:");
    pantalla.setTextSize(2);
    pantalla.setCursor(28, 25);
    pantalla.print(pesoActual);
    pantalla.print(" g.");

    // Lógica de histéresis
    if (pesoActual <= umbral) {
      contador = contador + 1;
    } else if (pesoActual >= umbral + margen) { 
      contador = 0;
    }

    // Modo y Estado Seguro
    if (modoActual == "AUTO") {
      if (contador >= 2) { 
        alarmaActiva = true;
        digitalWrite(buzzer, HIGH);
        pantalla.setTextSize(1);
        pantalla.setCursor(16, 50); 
        pantalla.print("PESO BAJO!");
      } 
      else {
        alarmaActiva = false;
        digitalWrite(buzzer, LOW);
      }
    } 
    else if (modoActual == "SILENCIAR") {
      digitalWrite(buzzer, LOW);
      alarmaActiva = false;
    }
    else if (modoActual == "ARMAR") {
      // Si está en ARMAR, la alarma suena sin importar el peso
      alarmaActiva = true;
      digitalWrite(buzzer, HIGH);
      pantalla.setTextSize(1);
      pantalla.setCursor(30, 50); 
      pantalla.print("ARMADO!");
    }

    pantalla.display();
  }

  // 3. TAREA DE TELEMETRÍA
  if (mqttClient.connected() && (tiempoActual - tiempoAnteriorPublicacion >= periodoPublicacion)) {
    tiempoAnteriorPublicacion = tiempoActual;
    publishMQTT();
  }
}

// --- DEFINICIÓN DE FUNCIONES ---

void reconnectMQTT_WiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Conectando a WiFi...");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    return; 
  }

  if (WiFi.status() == WL_CONNECTED && !mqttClient.connected()) {
    Serial.print("Intentando conexion a HiveMQ...");
    
    // Conexión sin credenciales para broker público
    if (mqttClient.connect(device_ID)) {
      Serial.println("¡Conectado!");
      mqttClient.subscribe(topic_comando); // Restauramos la suscripción
    } else {
      Serial.print("Fallo, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" -> Reintentando en 3s");
    }
  }
}

void publishMQTT() {
  JsonDocument doc; 
  
  // Estructura JSON requerida 
  doc["device_id"] = device_ID;
  doc["variable"] = "peso disponible";
  doc["value"] = pesoActual;
  doc["unit"] = "g";
  doc["mode"] = modoActual;
  doc["alarm"] = alarmaActiva;
  doc["sequence"] = secuenciaJSON;

  String payload;
  serializeJson(doc, payload);

  if (mqttClient.publish(topic_telemetria, payload.c_str())) {
    Serial.print("-> Publicado Seq[");
    Serial.print(secuenciaJSON);
    Serial.println("]: " + payload);
    secuenciaJSON++;
  } else {
    Serial.println("Error al publicar en MQTT");
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int len) {
  String msg = "";
  for (unsigned int i = 0; i < len; i++) {
    msg += (char)payload[i];
  }
  msg.trim();
  
  Serial.print("<- Comando recibido en ");
  Serial.print(topic);
  Serial.println(": " + msg);

  // Manejo estricto de comandos (Regla 2.5)
  if (msg == "AUTO" || msg == "ARMAR" || msg == "SILENCIAR") {
    modoActual = msg;
    Serial.println("Modo actualizado a: " + modoActual);
  } else {
    Serial.println("COMANDO_DESCONOCIDO");
  }
}