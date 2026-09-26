#include <Arduino.h>
#include "HX711.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h" 

Adafruit_SSD1306 pantalla(128, 64, &Wire, -1);
HX711 bascula;

const int buzzer = 12;
const int loadcellDT = 19;
const int loadcellSCK = 18;

const int umbral = 2000;
const int margen = 12;
int contador = 0;
int pesoActual = 0;

unsigned long tiempoAnteriorMuestreo = 0;
const unsigned long intervaloMuestreo = 900; 

unsigned long tiempoAnteriorPublicacion = 0;
const unsigned long periodoPublicacion = 8000; 

unsigned long tiempoAnteriorReconexion = 0;
const unsigned long intervaloReconexion = 3000; 

String modoActual = "AUTO"; 
bool alarmaActiva = false; 
bool alarmaAnterior = false; // Para detectar el cambio instantaneo y enviar alerta

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Tópicos asignados para IOT-B8982F65F7
const char* device_ID = "IOT-B8982F65F7";
const char* topic_telemetria = "iot/b8982f65f7/telemetry";
const char* topic_estado = "iot/b8982f65f7/status";
const char* topic_comando = "iot/b8982f65f7/command";
const char* topic_alerta = "iot/b8982f65f7/alert";

int secuenciaJSON = 1;

void reconnectMQTT_WiFi();
void publishJSON(const char* topic);
void mqttCallback(char* topic, byte* payload, unsigned int len);

void setup() {
  Serial.begin(115200);
  Serial.println("Iniciando sistema...");
  
  pinMode(buzzer, OUTPUT); 
  digitalWrite(buzzer, LOW); 

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

  // Wi-Fi en segundo plano
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  pantalla.clearDisplay();
  pantalla.setCursor(5, 25);
  pantalla.print("SISTEMA LISTO");
  pantalla.display();
  delay(1000);
}

void loop() {
  unsigned long tiempoActual = millis();

  // 1. TAREA DE RED
  if (!mqttClient.connected()) {
    if (tiempoActual - tiempoAnteriorReconexion >= intervaloReconexion) {
      tiempoAnteriorReconexion = tiempoActual;
      reconnectMQTT_WiFi();
    }
  } else {
    mqttClient.loop(); 
  }

  // 2. TAREA LOCAL
  if (tiempoActual - tiempoAnteriorMuestreo >= intervaloMuestreo) {
    tiempoAnteriorMuestreo = tiempoActual; 

    int lecturaBascula = bascula.get_units();
    if (lecturaBascula < -500 || lecturaBascula > 6000) {
      Serial.println("Error: Lectura fuera de rango admisible.");
      return; 
    }
    pesoActual = lecturaBascula; 

    pantalla.clearDisplay();
    pantalla.setTextColor(WHITE);
    pantalla.setTextSize(1);
    pantalla.setCursor(19, 5);
    pantalla.print("Peso Detectado:");
    pantalla.setTextSize(2);
    pantalla.setCursor(28, 25);
    pantalla.print(pesoActual);
    pantalla.print(" g.");

    if (pesoActual <= umbral) {
      contador = contador + 1;
    } else if (pesoActual >= umbral + margen) { 
      contador = 0;
    }

    alarmaAnterior = alarmaActiva; // Guardamos el estado previo

    if (modoActual == "AUTO") {
      if (contador >= 2) { 
        alarmaActiva = true;
        digitalWrite(buzzer, HIGH);
        pantalla.setTextSize(1);
        pantalla.setCursor(16, 50); 
        pantalla.print("PESO BAJO!");
      } else {
        alarmaActiva = false;
        digitalWrite(buzzer, LOW);
      }
    } 
    else if (modoActual == "SILENCIAR") {
      digitalWrite(buzzer, LOW);
      alarmaActiva = false;
    }
    else if (modoActual == "ARMAR") {
      alarmaActiva = true;
      digitalWrite(buzzer, HIGH);
      pantalla.setTextSize(1);
      pantalla.setCursor(30, 50); 
      pantalla.print("ARMADO!");
    }
    pantalla.display();

    // 2.5 ALERTA INMEDIATA
    // Si la alarma se acaba de encender, enviamos un mensaje inmediato al tópico de alertas
    if (alarmaActiva == true && alarmaAnterior == false && mqttClient.connected()) {
        Serial.println("*** ALERTA INMEDIATA DISPARADA ***");
        publishJSON(topic_alerta);
    }
  }

  // 3. TAREA DE TELEMETRÍA (Periódica)
  if (mqttClient.connected() && (tiempoActual - tiempoAnteriorPublicacion >= periodoPublicacion)) {
    tiempoAnteriorPublicacion = tiempoActual;
    publishJSON(topic_telemetria);
  }
}

void reconnectMQTT_WiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    return; 
  }
  if (WiFi.status() == WL_CONNECTED && !mqttClient.connected()) {
    Serial.print("Intentando conexion a Mosquitto Local...");
    if (mqttClient.connect(device_ID)) {
      Serial.println("¡Conectado!");
      mqttClient.subscribe(topic_comando);
      // Enviamos el estado inicial al conectarnos
      publishJSON(topic_estado); 
    } else {
      Serial.print("Fallo, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" -> Reintentando en 3s");
    }
  }
}

// Función unificada para publicar JSON a cualquier tópico
void publishJSON(const char* topic) {
  JsonDocument doc; 
  
  // Estructura JSON 
  doc["device_id"] = device_ID;
  doc["variable"] = "peso disponible";
  doc["value"] = pesoActual;
  doc["unit"] = "g";
  doc["mode"] = modoActual;
  doc["alarm"] = alarmaActiva;
  doc["sequence"] = secuenciaJSON;

  String payload;
  serializeJson(doc, payload);

  if (mqttClient.publish(topic, payload.c_str())) {
    Serial.print("-> Publicado en ");
    Serial.print(topic);
    Serial.print(" Seq[");
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
  
  Serial.print("<- Comando recibido: ");
  Serial.println(msg);

  // Validación de comando (Rechazo seguro de mensajes inválidos)
  if (msg == "AUTO" || msg == "ARMAR" || msg == "SILENCIAR") {
    modoActual = msg;
    Serial.println("Modo actualizado a: " + modoActual);
    
    // Al cambiar de modo, confirmamos enviando el JSON al tópico de estado
    publishJSON(topic_estado);
  } else {
    Serial.println("COMANDO_DESCONOCIDO rechazado. El estado seguro se mantiene.");
  }
}