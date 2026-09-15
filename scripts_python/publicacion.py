"""Publica comandos MQTT para la actividad de la clase 6.

Este programa es un cliente MQTT publicador: se conecta al broker, envia un
comando al ESP32 y termina. La confirmacion de la ejecucion se recibe en el
programa suscripcion.py, no en este proceso.
"""

import argparse  # Permite recibir el comando desde la terminal.
import os  # Permite configurar el programa con variables de entorno.
import threading  # Permite esperar la confirmacion del callback de conexion.
import uuid  # Genera un identificador unico para cada cliente MQTT.

import paho.mqtt.client as mqtt  # Libreria que implementa el cliente MQTT.


# El publicador solamente acepta comandos que el ESP32 sabe interpretar.
# Un conjunto (set) permite comprobar rapidamente si un comando es valido.
COMANDOS_PERMITIDOS = {"AUTO", "ARMAR", "SILENCIAR"}
COMANDO_NO_PERMITIDO = "REINICIAR"

# Valores del ejemplo de la clase. Cada grupo puede sobrescribirlos con
# variables de entorno para usar un broker o tema propio.
MQTT_HOST = os.getenv("MQTT_HOST", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_COMANDO = os.getenv(
    "MQTT_TOPIC_COMANDO", "iot/clase6/ejemplo/comando"
)


def argumentos_cli():
    """Lee los datos que el estudiante escribe en la terminal."""

    # argparse genera automaticamente la ayuda que aparece con --help y
    # comprueba que el comando pertenezca a COMANDOS_PERMITIDOS.
    parser = argparse.ArgumentParser(
        description="Publica un comando permitido en un broker MQTT."
    )
    parser.add_argument(
        "comando",
        choices=sorted(COMANDOS_PERMITIDOS),
        nargs="?",
        default=None,
        help="Comando que debe ejecutar el ESP32. Sin este argumento se muestra un menu.",
    )
    parser.add_argument("--host", default=MQTT_HOST, help="Direccion del broker.")
    parser.add_argument(
        "--port", type=int, default=MQTT_PORT, help="Puerto MQTT del broker."
    )
    parser.add_argument(
        "--topic", default=TOPIC_COMANDO, help="Tema MQTT de comandos."
    )
    return parser.parse_args()


def seleccionar_comando():
    """Muestra un menu y devuelve el comando elegido por el estudiante."""

    # Asociamos cada opcion visible con el texto que se enviara por MQTT.
    # Asi el usuario no necesita recordar la sintaxis de los comandos.
    opciones = {
        "1": "AUTO",
        "2": "ARMAR",
        "3": "SILENCIAR",
        "4": COMANDO_NO_PERMITIDO,
    }

    while True:
        print("\n=== Publicador MQTT - Proyecto IOT-B8982F65F7 ===")
        print("1. AUTO")
        print("2. ARMAR")
        print("3. SILENCIAR")
        print("4. REINICIAR (no permitido)")
        print("0. Salir")

        try:
            opcion = input("Seleccione una opcion: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Permite cerrar el programa con Ctrl+C o cuando no existe una
            # entrada interactiva, sin mostrar un error poco claro.
            print("\nOperacion cancelada.")
            return None

        if opcion == "0":
            print("Programa finalizado.")
            return None
        if opcion in opciones:
            return opciones[opcion]

        print("Opcion no valida. Escriba 1, 2, 3, 4 o 0.")


def publicar(comando, host, port, topic):
    """Conecta al broker, publica un comando y cierra la conexion."""

    # Los comandos normalmente validos aparecen en COMANDOS_PERMITIDOS, pero
    # el menu tambien ofrece REINICIAR para probar la validacion del ESP32.
    # Por eso Python avisa, pero no bloquea el envio: el dispositivo debe
    # recibir el mensaje y decidir si lo acepta o lo rechaza.
    if comando not in COMANDOS_PERMITIDOS:
        print(
            f"Aviso: {comando} no es un comando permitido. "
            "Se enviara para que el ESP32 lo valide."
        )

    # El callback on_connect se ejecuta en otro hilo, por eso usamos un
    # Event para que el programa principal pueda esperar de forma segura
    # hasta saber si la conexion fue aceptada.
    conectado = threading.Event()
    resultado_conexion = {"razon": None}

    def on_connect(client, userdata, flags, reason_code, properties):
        # reason_code igual a 0 significa que el broker acepto la conexion.
        # Guardamos el resultado porque el callback y publicar() son partes
        # distintas del flujo de ejecucion.
        resultado_conexion["razon"] = reason_code
        conectado.set()

    # VERSION2 utiliza la firma actual de callbacks de Paho MQTT.
    # client_id debe ser diferente para evitar que el broker desconecte a
    # otro cliente que tenga exactamente el mismo identificador.
    cliente = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"IOT-PUBLICADOR-{uuid.uuid4().hex[:8]}",
    )
    cliente.on_connect = on_connect

    # El ejemplo no necesita usuario ni contrasena. Estas variables permiten
    # conectarse despues a un broker privado sin escribir secretos en el
    # codigo fuente.
    usuario = os.getenv("MQTT_USER")
    contrasena = os.getenv("MQTT_PASSWORD")
    if usuario:
        cliente.username_pw_set(usuario, contrasena)

    try:
        # keepalive=60 indica al cliente que mantenga activa la sesion MQTT
        # y detecte una desconexion si no puede comunicarse con el broker.
        cliente.connect(host, port, keepalive=60)

        # Paho necesita un ciclo de red para enviar paquetes, recibir la
        # respuesta CONNACK y completar la publicacion. loop_start() crea
        # ese ciclo en segundo plano para que el programa pueda continuar.
        cliente.loop_start()

        # No publicamos inmediatamente: primero esperamos la confirmacion
        # de que el broker acepto la conexion.
        if not conectado.wait(timeout=3):
            raise TimeoutError("Tiempo agotado esperando la conexion MQTT")
        if resultado_conexion["razon"] != 0:
            raise ConnectionError(
                f"El broker rechazo la conexion: {resultado_conexion['razon']}"
            )

        # QoS 1 solicita al broker una entrega de tipo "al menos una vez".
        # Puede producir duplicados en una reconexion, pero es mas confiable
        # que QoS 0 para un comando de esta actividad.
        mensaje = cliente.publish(topic, comando, qos=1)
        if mensaje.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"No se pudo publicar el comando: {mensaje.rc}")

        # publish() inicia el envio, pero puede retornar antes de que el
        # paquete llegue al broker. Esperamos hasta diez segundos y despues
        # comprobamos que Paho marco el mensaje como publicado.
        mensaje.wait_for_publish(timeout=3)
        if not mensaje.is_published():
            raise TimeoutError("Tiempo agotado esperando la publicacion MQTT")
        print(f"Comando publicado: {comando}")
        print(f"Tema: {topic}")
        print("La ejecucion se confirma al recibir el estado del ESP32.")
        return True
    finally:
        # La desconexion ordenada libera la sesion y loop_stop() detiene el
        # hilo de red creado por loop_start(), incluso si ocurre un error.
        cliente.disconnect()
        cliente.loop_stop()


def main():
    # main separa la lectura de argumentos de la logica MQTT y permite que
    # el archivo se pueda importar en una prueba sin ejecutarse solo.
    args = argumentos_cli()

    # Si se escribe el comando en la terminal, se conserva el modo de
    # ejecucion directa y el programa termina despues de publicarlo.
    if args.comando is not None:
        publicar(args.comando, args.host, args.port, args.topic)
        return

    # Sin argumentos, el menu permanece abierto para enviar varios comandos
    # consecutivos. Solo seleccionar 0 o pulsar Ctrl+C termina el programa.
    while True:
        comando = seleccionar_comando()
        if comando is None:
            return

        try:
            publicar(comando, args.host, args.port, args.topic)
        except (ConnectionError, OSError, RuntimeError, TimeoutError) as error:
            # Un error de red no debe cerrar el menu: el estudiante puede
            # corregir la configuracion y volver a intentarlo.
            print(f"No se pudo enviar el comando: {error}")
        print("\nRegresando al menu...")


if __name__ == "__main__":
    main()
