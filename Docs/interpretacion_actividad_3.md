# Interpretación de la Actividad 3


En esta solución integrada, una medición nace en la celda de carga (HX711). El ESP32 la lee cada 900 ms, la valida y actualiza la pantalla local OLED. Cada 21 segundos, esta medición se empaqueta en JSON y se publica vía MQTT en el tema de telemetría hacia el broker local Mosquitto, donde el script de Python la recibe, valida y muestra en pantalla.

Por otro lado, cuando un usuario envía un comando (AUTO, ARMAR, SILENCIAR) desde Python al tema de comandos, el broker lo entrega al ESP32. El microcontrolador lo procesa, actualiza su estado interno y acciona inmediatamente el buzzer y la interfaz OLED.

Las decisiones críticas de negocio permanecen exclusivamente en el ESP32: la evaluación del umbral (2000 g), la histéresis (12 g), las dos confirmaciones consecutivas y el estado seguro (apagado). Esto es vital porque, al utilizar lógica no bloqueante con millis(), la estación de empaque mantiene su seguridad operativa y control local incluso si el broker Mosquitto o el Wi-Fi fallan.

Finalmente, Python actúa como panel de control central. Los tópicos asignados organizan el tráfico bidireccional, mientras que el JSON estandariza la comunicación, asegurando que cada paquete contenga la identidad del dispositivo, la variable medida, su modo y el estado de la alarma.