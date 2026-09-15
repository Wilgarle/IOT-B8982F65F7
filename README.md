# Sistema de Control de Inventario por Peso — Estación de Empaque
### Código de Asignación: `IOT-B8982F65F7` | Versión: IOT-2026-B1-v1 | Actividad 2

**Autor:** William García Leonel  
**Plataforma:** ESP32 DevKit v4 — PlatformIO + Wokwi  
**Estado actual:** ✅ Actividad 2 implementada — Control local + Conectividad MQTT (HiveMQ)

---

## Tabla de Contenidos
1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Estructura del Repositorio](#estructura-del-repositorio)
3. [Hardware y Conexiones](#hardware-y-conexiones)
4. [Software — Arquitectura del Firmware](#software--arquitectura-del-firmware)
5. [Conectividad IoT (MQTT)](#conectividad-iot-mqtt)
6. [Puesta en Marcha](#puesta-en-marcha)

---

## Descripción del Proyecto

Sistema IoT embebido desarrollado sobre ESP32 para el monitoreo continuo del **peso disponible en una estación de empaque**. Detecta niveles críticos de inventario y genera alertas acústicas y visuales en tiempo real. En esta segunda fase, el dispositivo además publica telemetría en la nube y acepta comandos remotos vía protocolo MQTT.

### Características Implementadas

| Característica | Descripción |
| :--- | :--- |
| **Muestreo continuo** | Celda de carga HX711 (24 bits) leída cada 900 ms |
| **Filtro antirruido** | Requiere **2 lecturas consecutivas** bajo umbral para activar alarma |
| **Histéresis** | Retorno a normal solo cuando peso ≥ **2012 g** (umbral + 12 g de margen) |
| **Validación de dato** | Lecturas fuera de [-500, 6000] g se descartan sin alterar el estado |
| **HMI local** | Pantalla OLED SSD1306 128×64 con splash screen, peso en tiempo real y mensajes de alerta |
| **Alarma acústica** | Buzzer piezoeléctrico activo controlado por GPIO |
| **Temporización no bloqueante** | `millis()` para todas las tareas; el sistema **nunca se congela** aunque WiFi/MQTT caiga |
| **Conectividad MQTT** | Reconexión automática a WiFi y broker con intervalo de 3 s |
| **Telemetría en la nube** | Publicación JSON estructurada cada 21 s en `iot/b8982f65f7/telemetry` |
| **Comandos remotos** | Modos `AUTO`, `ARMAR` y `SILENCIAR` recibidos por suscripción MQTT |

---

## Estructura del Repositorio

```
IOT-B8982F65F7/
├── src/
│   └── main.cpp                        # Firmware principal (toda la lógica del sistema)
├── include/
│   ├── secrets.example.h               # Plantilla de credenciales (copiar como secrets.h)
│   └── secrets.h                       # ⚠ Credenciales reales — excluido de Git
├── Docs/
│   ├── Conexiones.md                   # Tabla de pines y justificación técnica de señales
│   ├── Diagrama de Flujo.pdf           # Flujo de control del sistema
│   ├── interpretacion_asignacion.md    # Análisis del escenario asignado (Actividad 1)
│   └── interpretacion_actividad_2.md   # Análisis de requisitos IoT (Actividad 2)
├── scripts_python/
│   ├── publicacion.py                  # Cliente MQTT de prueba para publicar mensajes
│   ├── suscripcion.py                  # Cliente MQTT de prueba para suscribirse y recibir
│   └── INSTRUCCIONES_PUBLICACION_SUSCRIPCION.md
├── insumos_generador/
│   ├── proyecto_iot-b8982f65f7.pdf     # Ficha oficial de asignación individual
│   └── Generador_de_proyectos_IoT.ipynb
├── .github/
│   └── instructions/
│       └── mermaid.instructions.md     # Directrices para generación de diagramas
├── diagram.json                        # Circuito del simulador Wokwi
├── platformio.ini                      # Configuración de compilación y dependencias
├── wokwi.toml                          # Enlace binario compilado ↔ simulador Wokwi
└── .gitignore                          # Excluye .pio/, credenciales y archivos de IDE
```

> **Nota sobre `secrets.h`:** Este archivo contiene las credenciales reales de WiFi y del broker MQTT. Está incluido en `.gitignore` y **nunca debe subirse a GitHub**. Para poner en marcha el proyecto, copia `include/secrets.example.h` como `include/secrets.h` y completa los valores.

---

## Hardware y Conexiones

### Componentes

| Componente | ID Wokwi | Función |
| :--- | :--- | :--- |
| ESP32 DevKit-C v4 | `board-esp32-devkit-c-v4` | Unidad de procesamiento central |
| Celda de carga + HX711 | `wokwi-hx711` | Sensor de peso (rango 5 kg, ADC 24 bits) |
| Pantalla OLED SSD1306 | `board-ssd1306` | Visualizador local 128×64 px |
| Buzzer piezoeléctrico | `wokwi-buzzer` | Alarma acústica |

### Mapa de Pines

| Componente | Pin Periférico | GPIO ESP32 | Tipo de Señal |
| :---: | :---: | :---: | :---: |
| HX711 | VCC | 5V | Alimentación |
| HX711 | GND | GND | Tierra |
| HX711 | DT | GPIO **19** | Datos serie (entrada) |
| HX711 | SCK | GPIO **18** | Reloj serie (salida) |
| SSD1306 | VCC | 3V3 | Alimentación |
| SSD1306 | GND | GND | Tierra |
| SSD1306 | SDA | GPIO **21** | I2C datos |
| SSD1306 | SCL | GPIO **22** | I2C reloj |
| Buzzer | + | GPIO **12** | Salida digital |
| Buzzer | − | GND | Tierra |

---

## Software — Arquitectura del Firmware

El firmware ([`src/main.cpp`](src/main.cpp)) sigue un modelo de **tareas concurrentes no bloqueantes** basadas en `millis()`, estructuradas en el ciclo `loop()`:

```
loop()
 ├── TAREA 1 — Red (cada T_RECONEXION = 3 s si desconectado)
 │     WiFi.begin() → mqttClient.connect() → subscribe(TOPIC_COMMAND)
 │     Si conectado: mqttClient.loop()  ← procesa comandos entrantes
 │
 ├── TAREA 2 — Local (cada T_MUESTREO = 900 ms)
 │     bascula.get_units()
 │     ├── Validación de rango [-500, 6000] g
 │     ├── Lógica de histéresis (contador / margen)
 │     ├── Gobierno de actuadores según modoActual
 │     │     AUTO     → buzzer según contador ≥ 2
 │     │     ARMAR    → buzzer siempre encendido
 │     │     SILENCIAR→ buzzer siempre apagado
 │     └── Render OLED
 │
 └── TAREA 3 — Telemetría (cada T_PUBLICACION = 21 s, solo si conectado)
       publishMQTT()  → JSON → TOPIC_TELEMETRY
```

### Lógica de Histéresis y Confirmaciones

```
Zona de alarma   : peso ≤ 2000 g → contador++
Zona segura      : peso ≥ 2012 g → contador = 0
Zona muerta      : 2001 – 2011 g → contador sin cambio
Activación alarma: contador ≥ 2 lecturas consecutivas (≈ 1.8 s)
```

---

## Conectividad IoT (MQTT)

### Tópicos Asignados

| Tópico | Dirección | Descripción |
| :--- | :---: | :--- |
| `iot/b8982f65f7/telemetry` | ESP32 → Nube | Payload JSON periódico (cada 21 s) |
| `iot/b8982f65f7/command` | Nube → ESP32 | Comandos: `AUTO`, `ARMAR`, `SILENCIAR` |

### Formato del Payload JSON

```json
{
  "device_id": "IOT-B8982F65F7",
  "variable":  "peso disponible",
  "value":     2045,
  "unit":      "g",
  "mode":      "AUTO",
  "alarm":     false,
  "sequence":  1
}
```

### Comandos Remotos

| Comando | Comportamiento |
| :--- | :--- |
| `AUTO` | Modo normal — alarma basada en peso y confirmaciones |
| `ARMAR` | Fuerza la alarma activa independientemente del peso |
| `SILENCIAR` | Apaga el buzzer y marca `alarm: false` en telemetría |
| Cualquier otro | Ignorado; imprime `COMANDO_DESCONOCIDO` en Serial |

---

## Puesta en Marcha

### Requisitos
- **VS Code** con extensiones [PlatformIO IDE](https://marketplace.visualstudio.com/items?itemName=platformio.platformio-ide) y [Wokwi Simulator](https://marketplace.visualstudio.com/items?itemName=Wokwi.wokwi-vscode)
- Cuenta gratuita en [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/) (o cualquier broker MQTT público/privado)

### Configuración de Credenciales

```bash
# 1. Copiar la plantilla
cp include/secrets.example.h include/secrets.h

# 2. Editar include/secrets.h con tus datos reales:
#    WIFI_SSID, WIFI_PASSWORD, MQTT_BROKER, MQTT_PORT
```

### Compilar y Simular (Wokwi)

```bash
# Compilar el firmware
platformio run

# El binario queda en: .pio/build/esp32dev/firmware.bin
# Abrir diagram.json en VS Code y ejecutar: Wokwi: Start Simulator
```

### Cargar a Placa Física

```bash
platformio run --target upload
platformio device monitor    # 115200 bps
```

---

## Información Académica

| | |
|---|---|
| **Universidad** | IU Digital de Antioquia |
| **Autor** | William García Leonel |
| **Año** | 2026 |
