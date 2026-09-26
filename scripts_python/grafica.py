import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import paho.mqtt.client as mqtt
from collections import deque

# Configuración (Usa la IP local del boker MQTT)
MQTT_HOST = "192.168.229.1" 
TOPIC_TELEMETRIA = "iot/b8982f65f7/telemetry"

# Memoria (elimina los datos viejos cuando llega a 50)
x_data = deque(maxlen=50)
y_data = deque(maxlen=50)
contador = 0

def on_message(client, userdata, message):
    global contador
    try:
        # Decodificamos el JSON que envía el ESP32
        payload = message.payload.decode("utf-8")
        datos = json.loads(payload)
        
        # Extraemos el peso
        peso = datos["value"]
        
        # Agregamos los nuevos puntos a las listas
        x_data.append(contador)
        y_data.append(peso)
        contador += 1
    except Exception as e:
        print("Error procesando mensaje:", e)

# Configuración del cliente MQTT en segundo plano
cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.on_message = on_message
cliente.connect(MQTT_HOST, 1883)
cliente.subscribe(TOPIC_TELEMETRIA)
cliente.loop_start() # loop_start corre en un hilo separado para no bloquear la gráfica

# Configuración estética de la gráfica
fig, ax = plt.subplots(figsize=(8, 5))
fig.canvas.manager.set_window_title('Panel de Control - Estación de Empaque')
ax.set_title("Monitoreo de Peso en Tiempo Real", fontsize=14)
ax.set_ylabel("Peso (g)", fontsize=12)
ax.set_xlabel("Nº de Lecturas", fontsize=12)
ax.grid(True, linestyle='--', alpha=0.7)

# Línea principal (empieza vacía)
linea, = ax.plot([], [], color='#0078D7', linewidth=2.5, marker='o', markersize=4)

# Función que redibuja la gráfica cada segundo
def actualizar_grafica(frame):
    if len(x_data) > 0:
        linea.set_data(x_data, y_data)
        ax.relim()
        ax.autoscale_view()
        
        # Resalta en rojo si cae por debajo de tu umbral
        if y_data[-1] <= 2000:
            linea.set_color('#D13438')
        else:
            linea.set_color('#0078D7')
            
    return linea,

# Animación (interval=1000 significa que se refresca cada 1000 ms)
ani = animation.FuncAnimation(fig, actualizar_grafica, interval=1000, cache_frame_data=False)

print("Iniciando gráfica en tiempo real. Cierra la ventana para salir.")
plt.tight_layout()
plt.show()