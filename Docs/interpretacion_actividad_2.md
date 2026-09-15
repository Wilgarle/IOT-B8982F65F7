# Interpretación de la Actividad 2

En este segundo avance, mi sistema de la estación de empaque seguirá funcionando localmente leyendo el peso de la celda de carga cada 900 ms. Mostrará los datos en la pantalla OLED y activará el buzzer de alerta si las existencias son bajas.

La alarma se activa únicamente cuando el peso es menor o igual al umbral de 2000 g durante 2 lecturas consecutivas (confirmaciones); esto evita falsos positivos por vibraciones en la banda. Para que el sistema regrese a su condición normal y la alarma se apague, el peso debe subir hasta los 2012 g. Este margen extra de 12 g (histéresis) es crucial para evitar que el buzzer se encienda y apague repetidamente si el peso oscila justo en el límite de los 2000 g.

A nivel de conectividad, el ESP32 se conectará a una plataforma en la nube vía Wi-Fi y MQTT. Cada 21 segundos enviaré un paquete de datos en formato JSON que incluirá el ID de mi dispositivo (IOT-B8982F65F7), el peso actual, si la alarma está activa y el modo de operación.

Identifico dos riesgos principales en esta etapa: el primero es lograr que las funciones de Wi-Fi y MQTT no bloqueen el microcontrolador; si se pierde la conexión, el control local de la báscula y la alarma deben seguir respondiendo sin interrupciones. El segundo riesgo es manejar correctamente la recepción de comandos remotos (AUTO, ARMAR, SILENCIAR) sin afectar el ciclo principal de lectura.