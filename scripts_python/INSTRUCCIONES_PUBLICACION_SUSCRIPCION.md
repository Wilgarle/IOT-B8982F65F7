# Instrucciones de publicación y suscripción MQTT

Esta guía explica cómo utilizar los archivos Python de la actividad de la
clase 6:

- `publicacion.py`: publica comandos para el ESP32.
- `suscripcion.py`: recibe telemetría y estados del ESP32.

Los dos programas son clientes MQTT. El broker distribuye los mensajes, pero
no procesa la lógica del dispositivo.

## 1. Requisitos

Se necesita:

- Python 3 instalado.
- Acceso a Internet.
- Un broker MQTT accesible.
- El ESP32 conectado al mismo broker y usando los mismos temas.

El ejemplo utiliza estos valores:

| Elemento            | Valor del ejemplo                 |
| ------------------- | --------------------------------- |
| Broker              | `broker.hivemq.com`             |
| Puerto              | `1883`                          |
| Tema de telemetría | `iot/clase6/ejemplo/telemetria` |
| Tema de estado      | `iot/clase6/ejemplo/estado`     |
| Tema de comandos    | `iot/clase6/ejemplo/comando`    |

El broker es público y sirve para demostraciones. No se deben enviar datos
privados ni credenciales reales a través de este ejemplo.

## 2. Instalar Paho MQTT

Abra una terminal en la carpeta `python clase 6` y ejecute:

```bash
python -m pip install paho-mqtt
```

Se recomienda usar un entorno virtual para no mezclar las dependencias de
esta actividad con las de otros proyectos:

```bash
python -m venv .venv
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install paho-mqtt
```

En Linux o macOS:

```bash
source .venv/bin/activate
python -m pip install paho-mqtt
```

## 3. Iniciar la suscripción

El suscriptor debe iniciarse antes de enviar comandos para observar todos los
mensajes desde el comienzo.

Desde la carpeta `python clase 6`:

```bash
python suscripcion.py
```

También se puede ejecutar desde la carpeta padre:

```bash
python "python clase 6/suscripcion.py"
```

Cuando la conexión sea correcta se mostrará algo parecido a:

```text
MQTT conectado
Telemetria: iot/clase6/ejemplo/telemetria
Estado: iot/clase6/ejemplo/estado
Escuchando mensajes. Presione Ctrl+C para salir.
```

El programa permanece activo y procesa mensajes hasta que se presiona
`Ctrl+C`.

## 4. Publicar un comando

Abra una segunda terminal, active el mismo entorno virtual si se está usando y
ejecute el publicador sin argumentos para abrir el menú interactivo:

```bash
python publicacion.py
```

El menú muestra las siguientes opciones:

```text
=== Publicador MQTT - Clase 6 ===
1. AUTO
2. ENCENDER
3. APAGAR
4. REINICIAR (no permitido)
0. Salir
Seleccione una opcion:
```

También se puede enviar un comando directamente, sin abrir el menú:

```bash
python publicacion.py ENCENDER
python publicacion.py APAGAR
python publicacion.py AUTO
```

La opción `0` cierra el programa sin publicar ningún mensaje.

El menú permanece abierto después de cada selección y permite enviar varios
comandos consecutivos. La opción `4` usa `REINICIAR` para demostrar la
validación de comandos. En este caso Python muestra una advertencia, pero sí
publica el mensaje para que el ESP32 lo reciba y decida si debe aceptarlo o
rechazarlo.

Desde la carpeta padre se puede usar:

```bash
python "python clase 6/publicacion.py" ENCENDER
```

El publicador informa que el comando fue enviado, pero eso no significa que el
ESP32 ya lo haya ejecutado. La confirmación debe llegar posteriormente por el
tema de estado y aparecerá en `suscripcion.py`.

## 5. Flujo completo de la actividad

El flujo esperado es:

```text
ESP32 -- telemetria --> broker MQTT --> suscripcion.py
ESP32 <-- comando ---- broker MQTT <-- publicacion.py
ESP32 -- estado ------> broker MQTT --> suscripcion.py
```

El orden recomendado es:

1. Encender o iniciar el ESP32.
2. Ejecutar `suscripcion.py`.
3. Verificar que aparecen mensajes de telemetría.
4. Ejecutar `publicacion.py ENCENDER`.
5. Revisar en el suscriptor el estado confirmado.
6. Repetir con `APAGAR` y `AUTO`.

Si el ESP32 todavía no está publicando telemetría, el suscriptor puede
conectarse correctamente, pero no mostrará mediciones.

## 6. Formato de la telemetría

El suscriptor espera un objeto JSON con estos campos obligatorios:

```json
{
  "device_id": "esp32-clase6-demo",
  "variable": "temperatura",
  "value": 24.5,
  "unit": "C",
  "mode": "AUTO",
  "alarm": false,
  "sequence": 1
}
```

Significado de los campos:

| Campo         | Descripción                                      |
| ------------- | ------------------------------------------------- |
| `device_id` | Identificador del dispositivo que envía el dato. |
| `variable`  | Nombre de la medición.                           |
| `value`     | Valor numérico de la medición.                  |
| `unit`      | Unidad del valor, por ejemplo`C`.               |
| `mode`      | Modo actual del dispositivo.                      |
| `alarm`     | Indica si existe una alarma.                      |
| `sequence`  | Número consecutivo de la medición.              |

El programa verifica que el JSON sea válido, que no supere 4096 bytes, que
contenga todos los campos y que `value` y `sequence` tengan tipos adecuados.
Los mensajes inválidos se descartan sin detener el programa.

## 7. Formato del estado confirmado

El ESP32 puede publicar un estado como este:

```json
{
  "device_id": "esp32-clase6-demo",
  "command": "ENCENDER",
  "mode": "ENCENDER",
  "output": true,
  "confirmed": true,
  "status": "OK"
}
```

El estado confirmado representa lo que el ESP32 ejecutó realmente. No debe
confundirse con el comando solicitado por el publicador.

## 8. Cambiar broker o temas

Los valores predeterminados están definidos dentro de los scripts, pero se
pueden reemplazar sin editar el código.

En Windows PowerShell, antes de ejecutar los programas:

```powershell
$env:MQTT_HOST = "broker.hivemq.com"
$env:MQTT_PORT = "1883"
$env:MQTT_TOPIC_TELEMETRIA = "iot/clase6/grupo01/telemetria"
$env:MQTT_TOPIC_ESTADO = "iot/clase6/grupo01/estado"
$env:MQTT_TOPIC_COMANDO = "iot/clase6/grupo01/comando"
```

Después, se ejecutan normalmente:

```powershell
python suscripcion.py
python publicacion.py ENCENDER
```

El ESP32 debe utilizar exactamente los mismos tres temas. Cambiar solo el
tema de Python produce una conexión correcta, pero no habrá mensajes visibles.

También se pueden cambiar los valores desde la línea de comandos:

```bash
python suscripcion.py --host broker.hivemq.com --port 1883 \
  --telemetry-topic iot/clase6/grupo01/telemetria \
  --state-topic iot/clase6/grupo01/estado

python publicacion.py ENCENDER --host broker.hivemq.com --port 1883 \
  --topic iot/clase6/grupo01/comando
```

## 9. Opciones de ayuda

Para consultar las opciones disponibles:

```bash
python suscripcion.py --help
python publicacion.py --help
```

Las opciones principales son:

- `--host`: dirección del broker.
- `--port`: puerto MQTT.
- `--telemetry-topic`: tema de telemetría.
- `--state-topic`: tema de estado.
- `--topic`: tema de comandos del publicador.

## 10. Historial en memoria

`suscripcion.py` guarda las últimas 20 mediciones en `HISTORIAL` usando una
cola circular (`deque`). Cuando llega la medición número 21, se elimina la más
antigua.

Este historial no se escribe en un archivo ni en una base de datos. Se pierde
cuando se cierra el programa y sirve como base para agregar posteriormente una
interfaz gráfica o almacenamiento permanente.

## 11. Solución de problemas

**Error al importar `paho.mqtt.client`**

Instale la dependencia con `python -m pip install paho-mqtt` y compruebe que
la terminal está usando el mismo Python con el que se instaló.

**El programa no logra conectarse**

Compruebe la conexión a Internet, el nombre del broker, el puerto `1883` y
que el firewall no bloquee la conexión MQTT.

**El suscriptor se conecta, pero no recibe mensajes**

Verifique que el ESP32 y Python utilizan exactamente los mismos temas. Los
temas MQTT distinguen mayúsculas, minúsculas y cada `/`.

**La telemetría aparece como descartada**

Revise que el payload sea JSON válido y que incluya `device_id`, `variable`,
`value`, `unit`, `mode`, `alarm` y `sequence`.

**El publicador informa que envió el comando, pero el ESP32 no cambia**

El publicador solo envía el mensaje. Revise que el ESP32 esté conectado,
suscrito al tema de comandos y programado para aceptar `AUTO`, `ENCENDER` y
`APAGAR`. Para `REINICIAR`, el ESP32 debe publicar un estado de rechazo o
error, porque es el comando de prueba no permitido.

**Aparecen mensajes de otro grupo**

El broker del ejemplo es público y los temas son compartidos. Use un prefijo
propio, por ejemplo `iot/clase6/grupo01/`, en los tres temas.

## 12. Detener los programas

Para detener `suscripcion.py`, presione:

```text
Ctrl+C
```

`publicacion.py` termina automáticamente después de publicar el comando y
cerrar la conexión MQTT.
