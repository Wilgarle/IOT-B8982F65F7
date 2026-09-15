"""Recibe, valida y muestra telemetria y estado mediante MQTT.

Este programa permanece ejecutandose como cliente MQTT suscriptor. Recibe
mensajes del ESP32 mediante callbacks, valida la telemetria y conserva las
ultimas mediciones en memoria para que puedan usarse en una interfaz.
"""

import argparse  # Permite cambiar broker y temas desde la terminal.
import json  # Convierte JSON recibido en diccionarios de Python.
import math  # Permite comprobar que los valores numericos sean finitos.
import os  # Lee configuracion y obtiene el identificador del proceso.
from collections import deque  # Guarda un historial con tamano limitado.
from datetime import datetime  # Agrega la hora local a cada salida.

import paho.mqtt.client as mqtt  # Libreria que implementa el cliente MQTT.


# Valores del ejemplo de la clase. Cada grupo puede sobrescribirlos con
# variables de entorno para usar un broker o tema propio.
MQTT_HOST = os.getenv("MQTT_HOST", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_TELEMETRIA = os.getenv(
    "MQTT_TOPIC_TELEMETRIA", "iot/clase6/ejemplo/telemetria"
)
TOPIC_ESTADO = os.getenv("MQTT_TOPIC_ESTADO", "iot/clase6/ejemplo/estado")
# Limitar el payload evita procesar mensajes exageradamente grandes.
MAX_PAYLOAD = 4096

# deque descarta automaticamente el registro mas antiguo cuando se alcanza
# el limite. El historial es basico y vive solamente mientras corre el
# programa; una aplicacion real podria guardarlo en una base de datos.
HISTORIAL = deque(maxlen=20)


def procesar_telemetria(payload):
    """Convierte y valida un mensaje JSON de telemetria.

    Separar esta tarea del callback permite probar la validacion sin
    conectarse al broker y evita mezclar comunicacion MQTT con reglas de
    negocio.
    """

    # El broker entrega bytes, pero on_message los convierte a texto antes
    # de llamar a esta funcion. Medimos bytes para aplicar el limite real del
    # mensaje codificado en UTF-8.
    if len(payload.encode("utf-8")) > MAX_PAYLOAD:
        raise ValueError("El mensaje supera el tamano permitido")

    try:
        # json.loads convierte, por ejemplo, el objeto JSON en un dict.
        datos = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError("El payload no contiene JSON valido") from error

    # Un JSON puede ser valido y aun asi no representar una telemetria: por
    # ejemplo, podria ser una lista o un numero. La aplicacion espera objeto.
    if not isinstance(datos, dict):
        raise ValueError("La telemetria debe ser un objeto JSON")

    # Estos campos forman el contrato entre el ESP32 y la aplicacion Python.
    # Si el ESP32 cambia un nombre, ambos programas deben actualizarse.
    campos_requeridos = {
        "device_id",
        "variable",
        "value",
        "unit",
        "mode",
        "alarm",
        "sequence",
    }
    faltantes = campos_requeridos.difference(datos)
    if faltantes:
        raise ValueError(f"Faltan campos: {', '.join(sorted(faltantes))}")

    # bool hereda de int en Python, por eso se excluye explicitamente. Asi,
    # value=true no se acepta por error como una medicion numerica.
    if not isinstance(datos["value"], (int, float)) or isinstance(
        datos["value"], bool
    ):
        raise ValueError("value debe ser numerico")

    # NaN e infinito son valores que pueden romper calculos o graficas aunque
    # json.loads los haya convertido a un tipo numerico.
    if not math.isfinite(datos["value"]):
        raise ValueError("value debe ser finito")

    # sequence permite ordenar las mediciones y detectar perdidas de mensajes.
    # Tambien excluimos bool por la misma razon explicada para value.
    if not isinstance(datos["sequence"], int) or isinstance(
        datos["sequence"], bool
    ):
        raise ValueError("sequence debe ser entero")

    return datos


def argumentos_cli():
    """Lee opciones para conectarse al broker y elegir los temas."""

    # Las opciones tienen como valor predeterminado la configuracion del
    # ejemplo. El estudiante puede reemplazarlas sin editar el codigo.
    parser = argparse.ArgumentParser(
        description="Se suscribe a telemetria y estado MQTT."
    )
    parser.add_argument("--host", default=MQTT_HOST, help="Direccion del broker.")
    parser.add_argument(
        "--port", type=int, default=MQTT_PORT, help="Puerto MQTT del broker."
    )
    parser.add_argument(
        "--telemetry-topic",
        default=TOPIC_TELEMETRIA,
        help="Tema MQTT de telemetria.",
    )
    parser.add_argument(
        "--state-topic", default=TOPIC_ESTADO, help="Tema MQTT de estado."
    )
    return parser.parse_args()


def mostrar_estado(payload):
    """Muestra estado JSON o texto sin detener el cliente.

    El estado puede ser JSON, pero se acepta texto para que el programa siga
    siendo util mientras el ESP32 se encuentra en una etapa inicial.
    """
    try:
        estado = json.loads(payload)
        # separators reduce espacios innecesarios en la salida de consola.
        contenido = json.dumps(estado, ensure_ascii=True, separators=(",", ":"))
    except json.JSONDecodeError:
        contenido = payload
    print(f"[{datetime.now().isoformat(timespec='seconds')}] Estado: {contenido}")


def suscribir(host, port, topic_telemetria, topic_estado):
    """Conecta, se suscribe y procesa mensajes hasta recibir Ctrl+C."""

    def on_connect(client, userdata, flags, reason_code, properties):
        # Este callback se ejecuta tanto en la conexion inicial como despues
        # de una reconexion. Por eso la suscripcion se realiza aqui y no solo
        # una vez antes de iniciar el ciclo de red.
        if reason_code != 0:
            print(f"Conexion rechazada: {reason_code}")
            return

        # Una lista permite suscribirse a los dos temas en una sola llamada.
        # QoS 1 solicita que los mensajes importantes se entreguen al menos
        # una vez.
        resultado, _ = client.subscribe(
            [(topic_telemetria, 1), (topic_estado, 1)]
        )
        if resultado != mqtt.MQTT_ERR_SUCCESS:
            print(f"No se pudo suscribir: {resultado}")
            return
        print("MQTT conectado")
        print(f"Telemetria: {topic_telemetria}")
        print(f"Estado: {topic_estado}")

    def on_message(client, userdata, message):
        # on_message es el punto de entrada para cada mensaje que coincide
        # con una suscripcion. Debe realizar trabajo breve para no bloquear
        # el ciclo de red de Paho.
        try:
            # MQTT transporta bytes. UTF-8 permite convertirlos a texto JSON.
            payload = message.payload.decode("utf-8")
        except UnicodeDecodeError:
            print("Mensaje descartado: no es texto UTF-8")
            return

        if message.topic == topic_telemetria:
            try:
                # La validacion ocurre antes de actualizar la interfaz o el
                # historial: datos incorrectos no contaminan la aplicacion.
                datos = procesar_telemetria(payload)
            except ValueError as error:
                print(f"Telemetria descartada: {error}")
                return

            # Guardamos el dato validado y mostramos una vista resumida para
            # que el estudiante pueda observar la llegada de mensajes.
            HISTORIAL.append(datos)
            print(
                f"[{datetime.now().isoformat(timespec='seconds')}] "
                f"{datos['variable']}={datos['value']} {datos['unit']} | "
                f"modo={datos['mode']} alarma={datos['alarm']} "
                f"secuencia={datos['sequence']}"
            )
            return

        if message.topic == topic_estado:
            # El estado confirma lo que realmente ejecuto el ESP32. Esto es
            # distinto del comando que Python solicito publicar.
            mostrar_estado(payload)

    # El client_id debe ser unico. El PID evita que dos procesos Python de la
    # misma maquina se expulsen mutuamente del broker.
    cliente = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"IOT-SUSCRIPTOR-{os.getpid()}",
    )
    cliente.on_connect = on_connect
    cliente.on_message = on_message

    # Las credenciales son opcionales para el broker publico del ejemplo.
    # Si se define MQTT_USER, tambien se toma MQTT_PASSWORD.
    usuario = os.getenv("MQTT_USER")
    contrasena = os.getenv("MQTT_PASSWORD")
    if usuario:
        cliente.username_pw_set(usuario, contrasena)

    # connect() prepara la conexion. loop_forever() se encargara de enviar
    # la solicitud y recibir callbacks, incluyendo reconexiones de Paho.
    cliente.connect(host, port, keepalive=60)
    print("Escuchando mensajes. Presione Ctrl+C para salir.")
    try:
        # Este ciclo bloquea el programa mientras atiende la red MQTT.
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("\nSuscripcion finalizada")
    finally:
        # Ctrl+C no debe dejar una conexion abierta en el broker.
        cliente.disconnect()


def main():
    # Punto de entrada del programa cuando se ejecuta desde la terminal.
    args = argumentos_cli()
    suscribir(args.host, args.port, args.telemetry_topic, args.state_topic)


if __name__ == "__main__":
    main()
