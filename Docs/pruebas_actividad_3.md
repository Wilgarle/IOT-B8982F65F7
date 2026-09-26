# Plan y Registro de Pruebas — Actividad 3

Proyecto: IOT-B8982F65F7  
Dispositivo: ESP32 DevKit-C v4  
Escenario: Estacion de Empaque — Monitoreo de Inventario por Peso  
Autor: William Garcia  

En este documento se detallan las pruebas de verificacion del sistema integrado conforme a las condiciones de referencia (Seccion 3.6 de la asignacion).

---

## 1. Matriz de Casos de Prueba

| ID | Caso de Prueba | Entrada / Accion | Comportamiento Esperado | Resultado |
| :---: | :--- | :--- | :--- | :---: |
| PR-01 | Condicion A: Peso Normal | Carga sobre bascula > 2012 g (ej. 2500 g). | Contador de confirmaciones = 0. Alarma inactiva. Buzzer apagado (LOW). Pantalla OLED muestra peso actual sin mensaje de alerta. Telemetria reporta alarm: false. | Conforme |
| PR-02 | Condicion B: Peso Bajo | Carga <= 2000 g durante 2 ciclos consecutivos (1.8 s). | Al cumplir las 2 confirmaciones consecutivas: Alarma activa. Buzzer encendido (HIGH). OLED muestra "PESO BAJO!". Publicacion inmediata de alerta en topico iot/b8982f65f7/alert. | Conforme |
| PR-03 | Histeresis y Retorno | Incrementar peso a rango 2001 - 2011 g y luego >= 2012 g. | En rango intermedio (2001-2011 g): mantiene estado anterior sin conmutaciones indeseadas. Al superar 2012 g: contador = 0, buzzer se apaga y alarma se desactiva. | Conforme |
| PR-04 | Dato Invalido | Simular lectura fuera de [-500, 6000] g (ej. 8000 g o desconexion de celda). | El firmware descarta la lectura, imprime mensaje de error en Serial, no modifica contadores ni estado de la alarma y continua operando sin reiniciarse. | Conforme |
| PR-05 | Interrupcion de Red (20 s) | Suspender temporalmente el broker Mosquitto o desconectar Wi-Fi durante 20 s. | El ESP32 continua leyendo la celda cada 900 ms, actualizando pantalla y activando/desactivando el buzzer de forma local sin bloquearse. | Conforme |
| PR-06 | Reconexion Automatica | Restaurar conectividad tras la falla de red. | El dispositivo detecta la recuperacion mediante temporizador no bloqueante de 3 s, se reconecta a Mosquitto, se suscribe a comandos y publica su estado inicial. | Conforme |
| PR-07 | Comandos Remotos | Enviar comandos AUTO, ARMAR y SILENCIAR desde publicacion.py. | AUTO: opera con regla local. ARMAR: fuerza alarma activa y buzzer encendido. SILENCIAR: fuerza buzzer apagado. En cada cambio publica confirmacion en iot/b8982f65f7/status. | Conforme |
| PR-08 | Comando Desconocido | Enviar comando no asignado (ej. REINICIAR o TEST_ERROR). | El callback de suscripcion rechaza el comando, imprime COMANDO_DESCONOCIDO en Serial, mantiene el modo previo sin alterar el actuador y no reinicia el microcontrolador. | Conforme |
| PR-09 | Estado Seguro | Encendido e inicializacion del microcontrolador (setup). | Durante el arranque, el pin del buzzer se configura como salida y se establece forzosamente en nivel bajo (LOW), garantizando ausencia de falsos disparos. | Conforme |

---

## 2. Evidencias de Ejecucion

### 2.1. Validacion de Telemetria JSON
El suscriptor en Python valida que cada mensaje recibido en `iot/b8982f65f7/telemetry` contenga todos los campos obligatorios tipados correctamente:
- `device_id`: "IOT-B8982F65F7" (string)
- `variable`: "peso disponible" (string)
- `value`: entero o flotante finito (gramos)
- `unit`: "g" (string)
- `mode`: "AUTO" | "ARMAR" | "SILENCIAR" (string)
- `alarm`: booleano (bool)
- `sequence`: entero incremental (int)

### 2.2. Confirmacion Bidireccional
1. Publicador envia: `ARMAR` a `iot/b8982f65f7/command`.
2. ESP32 procesa callback, actualiza `modoActual = "ARMAR"` y acciona buzzer.
3. ESP32 publica paquete JSON al topico `iot/b8982f65f7/status`.
4. Suscriptor Python recibe: `ESTADO CONFIRMADO POR EL ESP32: {"device_id":"IOT-B8982F65F7", ... "mode":"ARMAR", "alarm":true}`.
