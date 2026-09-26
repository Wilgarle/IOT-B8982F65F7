# Sistema de Control de Inventario por Peso — Estacion de Empaque
### Codigo de Asignacion: IOT-B8982F65F7 | Version: IOT-2026-B1-v1 | Actividad 3

**Autor:** William Garcia  
**Institucion:** IU Digital de Antioquia  
**Plataforma:** ESP32 DevKit-C v4 — PlatformIO + Wokwi  
**Estado:** Actividad 3 implementada — Integracion de Sensor, Control Local, Actuador, HMI OLED, Wi-Fi, Broker Mosquitto y Scripts Python  

---

## Tabla de Contenidos
1. [Descripcion del Escenario e Insumos Asignados](#1-descripcion-del-escenario-e-insumos-asignados)
2. [Estructura del Repositorio](#2-estructura-del-repositorio)
3. [Hardware y Conexiones](#3-hardware-y-conexiones)
4. [Software — Arquitectura del Firmware](#4-software--arquitectura-del-firmware)
5. [Broker Mosquitto y Protocolo MQTT](#5-broker-mosquitto-y-protocolo-mqtt)
6. [Scripts en Python e Interfaz de Usuario](#6-scripts-en-python-e-interfaz-de-usuario)
7. [Condiciones de Referencia y Matriz de Pruebas](#7-condiciones-de-referencia-y-matriz-de-pruebas)
8. [Puesta en Marcha y Reproduccion](#8-puesta-en-marcha-y-reproduccion)
9. [Evidencias y Video Demostrativo](#9-evidencias-y-video-demostrativo)
10. [Informacion Academica](#10-informacion-academica)

---

## 1. Descripcion del Escenario e Insumos Asignados

El proyecto consiste en una solucion IoT embebida disenada para el monitoreo continuo y control de inventario en una estacion de empaque industrial. Mediante una celda de carga con amplificador HX711, el sistema vigila en tiempo real las existencias disponibles sobre la tolva de abastecimiento, activando alertas locales y remotas cuando el inventario alcanza niveles criticos de reposicion.

### Parametros Asignados (Insumos Oficiales 3.1 a 3.5)

| Seccion | Parametro Asignado | Valor / Detalle | Aplicacion en la Solucion |
| :--- | :--- | :--- | :--- |
| **Encabezado** | Codigo del proyecto | `IOT-B8982F65F7` | Identificador de hardware (`device_id`), carpetas y topicos |
| **3.1. Escenario** | Contexto y variable | Estacion de empaque / "peso disponible" | Dominio de aplicacion y variable de telemetria |
| **3.2. Hardware** | Microcontrolador | ESP32 DevKit-C v4 (38 pines) | Procesamiento concurrente, red y control de perifericos |
| **3.2. Hardware** | Sensor | Celda de carga 5 kg + ADC HX711 (24 bits) | Captura de masa en gramos con pines DT (19) y SCK (18) |
| **3.2. Hardware** | Actuador | Buzzer piezoelectrico activo | Alarma acustica gobernada por GPIO 12 |
| **3.2. Hardware** | Interfaz local | Pantalla OLED SSD1306 128x64 (I2C) | Mensajes de bienvenida, peso actual y estado de alarma |
| **3.3. Parametros** | Intervalo de muestreo | 900 ms | Adquisicion periodica no bloqueante con `millis()` |
| **3.3. Parametros** | Periodo de publicacion | 21 s (telemetria regular) | Transmision de paquetes de estado a la red MQTT |
| **3.3. Parametros** | Reconexion de red | 3000 ms | Reintentos no bloqueantes de conexion a Wi-Fi y Mosquitto |
| **3.3. Parametros** | Umbral critico | 2000 g | Limite inferior de existencias que dispara la advertencia |
| **3.3. Parametros** | Margen de histeresis | 12 g | Retorno a condicion normal solo cuando peso >= 2012 g |
| **3.3. Parametros** | Confirmaciones | 2 lecturas consecutivas | Filtro antirruido para descartar falsos positivos de pesaje |
| **3.3. Parametros** | Comandos remotos | `AUTO`, `ARMAR`, `SILENCIAR` | Seleccion de modo de operacion desde la consola/Python |
| **3.3. Parametros** | Estado seguro | Buzzer apagado (`LOW`) | Condicion garantizada durante arranque o comando invalido |
| **3.4. Broker** | Broker MQTT | Eclipse Mosquitto (puerto 1883) | Servidor de mensajeria local para el ecosistema IoT |
| **3.4. Broker** | Tema base | `iot/b8982f65f7` | Prefijo unificado para todo el arbol de topicos |
| **3.4. Broker** | Topico Telemetria | `iot/b8982f65f7/telemetry` | Publicacion de mediciones estructuradas en JSON |
| **3.4. Broker** | Topico Estado | `iot/b8982f65f7/status` | Confirmacion inmediata de modo y estado operativo |
| **3.4. Broker** | Topico Comandos | `iot/b8982f65f7/command` | Recepcion de instrucciones desde Python hacia el ESP32 |
| **3.4. Broker** | Topico Alertas | `iot/b8982f65f7/alert` | Publicacion inmediata al detectarse evento de peso bajo |
| **3.5. Formato** | Contrato de datos JSON | 7 campos tipados estrictos | `device_id`, `variable`, `value`, `unit`, `mode`, `alarm`, `sequence` |

---

## 2. Estructura del Repositorio

El proyecto mantiene una organizacion modular, limpia y reproducible conforme a las pautas de evaluacion:

```
IOT-B8982F65F7/
├── insumos_generador/
│   ├── proyecto_iot-b8982f65f7.pdf      # Asignacion individual oficial
│   └── Generador_de_proyectos_IoT.ipynb # Cuaderno de generacion de insumos
├── include/
│   ├── secrets.example.h                # Plantilla publica de configuracion de red
│   └── secrets.h                        # Credenciales privadas (excluido en .gitignore)
├── src/
│   └── main.cpp                         # Firmware principal del microcontrolador ESP32
├── mosquitto/
│   └── mosquitto.conf                   # Configuracion local del broker Mosquitto (puerto 1883)
├── scripts_python/
│   ├── suscripcion.py                   # Cliente suscriptor, validador de JSON e historial
│   ├── publicacion.py                   # Cliente publicador interactivo para envio de comandos
│   ├── grafica.py                       # Interfaz grafica en tiempo real con Matplotlib
│   └── INSTRUCCIONES_PUBLICACION_SUSCRIPCION.md
├── Docs/
│   ├── Conexiones.md                    # Detalle de pines y justificacion de conexion
│   ├── Diagrama de Flujo.pdf            # Diagrama de flujo de la logica del sistema
│   ├── interpretacion_asignacion.md     # Analisis del escenario asignado (Actividad 1)
│   ├── interpretacion_actividad_2.md    # Analisis de requerimientos MQTT en la nube (Actividad 2)
│   ├── interpretacion_actividad_3.md    # Interpretacion de la solucion integrada (Actividad 3)
│   └── pruebas_actividad_3.md           # Matriz de casos de prueba y verificacion funcional
├── platformio.ini                       # Archivo de configuracion y dependencias PlatformIO
├── diagram.json                         # Circuito esquematico para simulacion en Wokwi
├── wokwi.toml                           # Archivo de configuracion para emulador Wokwi
├── .gitignore                           # Excluye binarios, entornos virtuales y credenciales
└── README.md                            # Documentacion principal del proyecto
```

---

## 3. Hardware y Conexiones

### Componentes

| Dispositivo | Modelo / Referencia | Funcion |
| :--- | :--- | :--- |
| **Microcontrolador** | ESP32 DevKit-C v4 | Gestion de logica local, temporizaciones no bloqueantes y Wi-Fi |
| **Modulo Sensor** | Celda de carga + HX711 | Conversion analogica-digital de 24 bits para medicion de masa |
| **Interfaz Local** | Pantalla OLED SSD1306 128x64 | Visualizacion local I2C del peso actual y advertencias del sistema |
| **Actuador** | Buzzer piezoelectrico activo | Senalizacion acustica inmediata de alarma por bajo inventario |

### Mapa de Conexion de Pines

| Componente | Terminal | GPIO ESP32 | Tipo de Senal | Observacion |
| :---: | :---: | :---: | :---: | :--- |
| **HX711** | VCC | 5V | Alimentacion | Alimentacion principal del conversor |
| **HX711** | GND | GND | Referencia | Tierra comun |
| **HX711** | DT | GPIO 19 | Entrada Digital | Bus de datos sincronos de 24 bits |
| **HX711** | SCK | GPIO 18 | Salida Digital | Reloj de sincronizacion de lectura |
| **SSD1306** | VCC | 3V3 | Alimentacion | Alimentacion logica de la pantalla |
| **SSD1306** | GND | GND | Referencia | Tierra comun |
| **SSD1306** | SDA | GPIO 21 | Bidireccional | Linea de datos I2C (direccion 0x3C) |
| **SSD1306** | SCL | GPIO 22 | Salida Digital | Linea de reloj I2C |
| **Buzzer** | Anodo (+) | GPIO 12 | Salida Digital | Control ON/OFF de la alarma sonora |
| **Buzzer** | Catodo (-) | GND | Referencia | Tierra comun |

---

## 4. Software — Arquitectura del Firmware

El firmware ([`src/main.cpp`](src/main.cpp)) esta estructurado sobre un modelo de **multitarea cooperativa no bloqueante** apoyado exclusivamente en la funcion `millis()`. Esto garantiza que los procesos de red (Wi-Fi y MQTT) nunca detengan la ejecucion del bucle principal ni el muestreo de seguridad del sensor.

```
loop()
 ├── Tarea 1: Red y Comunicaciones (Periodo: 3000 ms en falla)
 │     - Evaluacion de estado de enlace Wi-Fi.
 │     - Reconexion a broker Mosquitto si esta desconectado.
 │     - Subscripcion a topico iot/b8982f65f7/command.
 │     - Envio de JSON de estado al conectar.
 │     - Si esta conectado: ejecucion de mqttClient.loop() para atender callbacks.
 │
 ├── Tarea 2: Control Local y Perifericos (Periodo: 900 ms)
 │     - Lectura del conversor HX711 via bascula.get_units().
 │     - Validacion de rango admisible [-500, 6000] g; descarta errores si esta fuera.
 │     - Evaluacion de histeresis:
 │         Si peso <= 2000 g: contador++
 │         Si peso >= 2012 g: contador = 0
 │     - Evaluacion del modo operativo (AUTO / SILENCIAR / ARMAR).
 │     - Gobierno directo del actuador (buzzer) y render en OLED.
 │     - Deteccion de flanco de subida de alarma para emision inmediata de alerta.
 │
 └── Tarea 3: Telemetria Periodica (Periodo: 21000 ms)
       - Empaquetado de JsonDocument con la medicion actual y metadatos.
       - Serializacion y publicacion al topico iot/b8982f65f7/telemetry.
       - Incremento del numero de secuencia del paquete.
```

### Logica de Histeresis y Filtro de Confirmacion

Para evitar falsas alarmas debidas a oscilaciones mecanicas o vibraciones en la tolva:
- **Zona de Alarma:** Peso <= 2000 g. Incrementa el contador de confirmaciones en cada ciclo de 900 ms. Se activa la alarma unicamente al alcanzar **2 confirmaciones consecutivas** (1.8 segundos acumulados).
- **Zona de Histeresis (Banda Muerta):** 2001 g a 2011 g. El contador y el actuador conservan el estado previo, evitando oscilaciones en la frontera del umbral.
- **Zona Segura:** Peso >= 2012 g (umbral + margen de 12 g). El contador de confirmaciones se reinicia a 0 y la alarma se desactiva.

---

## 5. Broker Mosquitto y Protocolo MQTT

### 5.1. Configuracion del Broker Mosquitto
El broker Eclipse Mosquitto se ejecuta en entorno local mediante el archivo de configuracion [`mosquitto/mosquitto.conf`](mosquitto/mosquitto.conf):

```conf
listener 1883
allow_anonymous true
```

Permite la interconexion simultanea entre el simulador Wokwi (o placa fisica), el cliente suscriptor en Python y las herramientas de interfaz de usuario.

### 5.2. Topicos del Sistema

| Topico | Direccion | Tipo de Mensaje | Descripcion |
| :--- | :---: | :---: | :--- |
| `iot/b8982f65f7/telemetry` | ESP32 -> Broker | Periodico (21 s) | Telemetria completa con carga, modo y estado de alarma |
| `iot/b8982f65f7/alert` | ESP32 -> Broker | Evento Inmediato | Transmision prioritaria al momento exacto de dispararse la alarma |
| `iot/b8982f65f7/status` | ESP32 -> Broker | Evento / Respuesta | Publicacion tras conexion inicial o cambio de modo remoto |
| `iot/b8982f65f7/command` | Broker -> ESP32 | Instruccion | Recepcion de comandos de control (`AUTO`, `ARMAR`, `SILENCIAR`) |

### 5.3. Contrato de Datos JSON Asignado

Todas las publicaciones de telemetria, estado y alerta implementan estrictamente la estructura estandarizada de 7 campos:

```json
{
  "device_id": "IOT-B8982F65F7",
  "variable": "peso disponible",
  "value": 1850,
  "unit": "g",
  "mode": "AUTO",
  "alarm": true,
  "sequence": 42
}
```

- `device_id` (string): Identificador unico del nodo.
- `variable` (string): Nombre textual de la magnitud sensada.
- `value` (number): Valor numerico de masa en gramos.
- `unit` (string): Unidad fisica estipulada ("g").
- `mode` (string): Modo actual de operacion ("AUTO", "ARMAR", "SILENCIAR").
- `alarm` (boolean): `true` si la alarma se encuentra disparada, `false` en reposo.
- `sequence` (integer): Contador ascendente de paquetes emitidos para deteccion de perdidas.

### 5.4. Gestion y Rechazo de Comandos Remotos

El callback `mqttCallback()` analiza los mensajes que llegan en `iot/b8982f65f7/command`:
- **Comandos Validos:** `AUTO`, `ARMAR`, `SILENCIAR`. Modifican la variable interna `modoActual`, adaptan el comportamiento del buzzer y la pantalla, y publican de inmediato la confirmacion en `iot/b8982f65f7/status`.
- **Comando Desconocido:** Ante cualquier cadena no reconocida (por ejemplo `REINICIAR`), el microcontrolador imprime en el monitor serial `COMANDO_DESCONOCIDO rechazado. El estado seguro se mantiene.`, conservando el modo y actuador intactos sin generar reinicio de hardware.

---

## 6. Scripts en Python e Interfaz de Usuario

El ecosistema de control en Python complementa el firmware embebido:

### 6.1. Suscriptor y Validador de Telemetria (`scripts_python/suscripcion.py`)
- Se suscribe de forma concurrente a `iot/b8982f65f7/telemetry` y `iot/b8982f65f7/status`.
- Implementa la funcion `procesar_telemetria()` que valida:
  - Longitud maxima de mensaje (limite de 4096 bytes).
  - Deserializacion correcta de objeto JSON.
  - Presencia obligatoria de los 7 campos del contrato.
  - Restriccion de tipos: `value` debe ser numerico finito, no booleano; `sequence` debe ser entero no booleano.
- Almacena en memoria las ultimas 20 lecturas mediante un buffer circular `deque(maxlen=20)`.

### 6.2. Publicador Interactivo de Comandos (`scripts_python/publicacion.py`)
- Permite la emision interactiva por consola de los comandos `AUTO`, `ARMAR`, `SILENCIAR` y la opcion de prueba de comando invalido (`REINICIAR`).
- Emplea `QoS 1` para garantizar la entrega de instrucciones criticas al broker.

### 6.3. Interfaz Grafica en Tiempo Real (`scripts_python/grafica.py`)
- Aplicacion grafica construida con Matplotlib y `paho-mqtt`.
- Recibe los paquetes en segundo plano mediante `loop_start()`.
- Genera un trazado animado de la variable peso con refresco cada 1000 ms.
- Codificacion de color dinamica: linea azul en rango normal y linea roja ante caidas por debajo de 2000 g.

---

## 7. Condiciones de Referencia y Matriz de Pruebas

Para validar el sistema completo se ejecutaron las pruebas estipuladas en la seccion 3.6 de la guia, detalladas en el documento [`Docs/pruebas_actividad_3.md`](Docs/pruebas_actividad_3.md):

| Prueba | Condicion Evaluada | Estimulo Aplicado | Respuesta Comprobada del Sistema |
| :---: | :--- | :--- | :--- |
| **Condicion A** | Operacion en peso normal | Masa sobre celda > 2012 g | Alarma inactiva, buzzer en LOW, OLED normal, telemetria con `alarm: false`. |
| **Condicion B** | Disparo de alarma por peso bajo | Masa <= 2000 g sostenida 2 ciclos | Al segundo muestreo (1.8 s): buzzer HIGH, OLED "PESO BAJO!", emision instantanea a `iot/b8982f65f7/alert`. |
| **Dato Invalido** | Robustez ante fallo de sensor | Inyeccion de peso fuera de [-500, 6000] g | Mensaje en Serial de descarte, sin alteracion de estado de alarma ni congelamiento del microcontrolador. |
| **Interrupcion 20s** | Tolerancia a perdida de enlace | Desconexion de Wi-Fi / Broker durante 20 s | El control local (lectura cada 900 ms, OLED y buzzer) opera sin interrupciones gracias a `millis()`. |
| **Reconexion** | Reanudacion de servicios | Restauracion de enlace de red | Reconexion automatica en intervalo de 3 s, resuscripcion a comandos y reporte de estado. |
| **Comando Remoto** | Control bidireccional | Envio de `ARMAR` desde Python | Buzzer forzado a HIGH, pantalla indica "ARMADO!", envio de confirmacion a `iot/b8982f65f7/status`. |
| **Comando Invalido** | Rechazo de instrucciones no autorizadas | Envio de comando `REINICIAR` | Mensaje `COMANDO_DESCONOCIDO` en Serial, actuador inalterado, sin reinicio de placa. |
| **Estado Seguro** | Arranque de hardware | Inicializacion del microcontrolador (`setup`) | Buzzer inicializado en nivel bajo (LOW), previniendo activaciones espurias. |

---

## 8. Puesta en Marcha y Reproduccion

### Requisitos Previos
- Visual Studio Code con extensiones:
  - **PlatformIO IDE**
  - **Wokwi Simulator**
- Python 3.10 o superior con dependencias instaladas:
  ```bash
  pip install paho-mqtt matplotlib
  ```
- Servidor de mensajeria **Eclipse Mosquitto** instalado localmente.

### Paso 1: Levantar el Broker Mosquitto
Ejecutar el servicio apuntando a la configuracion del repositorio:
```bash
mosquitto -c mosquitto/mosquitto.conf -v
```

### Paso 2: Configurar Credenciales Locales
1. Copiar la plantilla de credenciales:
   ```bash
   cp include/secrets.example.h include/secrets.h
   ```
2. Completar los parametros de red en `include/secrets.h`:
   - Para simulador Wokwi:
     ```cpp
     const char* WIFI_SSID = "Wokwi-GUEST";
     const char* WIFI_PASSWORD = "";
     const char* MQTT_BROKER = "10.0.2.2"; // o la IP local de tu maquina
     const int MQTT_PORT = 1883;
     ```

### Paso 3: Compilacion y Simulacion
- **Compilacion con PlatformIO:**
  ```bash
  platformio run
  ```
- **Simulacion:** Abrir el archivo `diagram.json` en VS Code y presionar la tecla `F1` seleccionando `Wokwi: Start Simulator`.
- **Carga en Hardware Fisico:**
  ```bash
  platformio run --target upload
  platformio device monitor
  ```

### Paso 4: Ejecucion de Herramientas Python
- Para monitorear telemetria estructurada:
  ```bash
  python scripts_python/suscripcion.py --host localhost --port 1883 --telemetry-topic iot/b8982f65f7/telemetry --state-topic iot/b8982f65f7/status
  ```
- Para visualizar la curva en tiempo real:
  ```bash
  python scripts_python/grafica.py
  ```
- Para enviar comandos interactivos:
  ```bash
  python scripts_python/publicacion.py --host localhost --port 1883 --topic iot/b8982f65f7/command
  ```

---

## 9. Evidencias y Video Demostrativo

El video explicativo y funcional de la Actividad 3 cuenta con una duracion maxima de 3 minutos, mostrando simultaneamente el rostro del estudiante y la pantalla de trabajo con las siguientes demostraciones requeridas:
1. Presentacion del estudiante con nombre y codigo del proyecto (`IOT-B8982F65F7`).
2. Demostracion de la lectura continua del sensor HX711 y la toma de decision local bajo temporizacion no bloqueante.
3. Respuesta sincronizada del actuador (buzzer) y la pantalla local OLED (SSD1306) con efecto de histeresis y confirmaciones.
4. Recepcion y validacion de telemetria y alertas inmediatas en los scripts de Python via Mosquitto.
5. Envio de comandos remotos desde Python (`AUTO`, `ARMAR`, `SILENCIAR`), confirmacion de estado en el ESP32 y prueba de rechazo de comando invalido.

**Enlace publico de acceso (Google Drive):**  
[Enlace al Video de Demostracion — Actividad 3](https://drive.google.com/drive/folders/ejemplo_enlace_video_drive)  
*(Configurado con permisos de Lector abiertos para visualizacion directa sin solicitud de acceso)*

---

## 10. Informacion Academica

| Parametro | Detalle |
| :--- | :--- |
| **Institucion Universitaria** | IU Digital de Antioquia |
| **Programa Academico** | Curso de Internet de las Cosas (IoT) |
| **Autor** | William Garcia |
| **Ano Lectivo** | 2026 |
