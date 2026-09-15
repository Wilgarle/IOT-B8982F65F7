### Tabla de Conexiones Físicas

La siguiente tabla describe la interconexión de periféricos, especificando los pines utilizados, el tipo de protocolo y la justificación técnica de la señal:

| Componente Físico | Pin Periférico | GPIO ESP32 | Tipo de Señal | Justificación Técnica |
| :--- | :---: | :---: | :---: | :--- |
| **Módulo HX711** | VCC / GND | 3V3 / GND | Alimentación | Energiza el amplificador a 3.3V asegurando compatibilidad lógica. |
| | DT (Datos) | 19 | Digital Serie | Recepción de la trama de datos del peso desde el ADC. |
| | SCK (Reloj) | 18 | Digital Reloj | Señal de sincronización emitida por el ESP32 para lectura. |
| **OLED SSD1306** | VCC / GND | 3V3 / GND | Alimentación | Proporciona voltaje operativo al panel visual. |
| | SDA (Datos) | 21 | Protocolo I2C | Línea estándar para la transmisión bidireccional de gráficos. |
| | SCL (Reloj) | 22 | Protocolo I2C | Señal de reloj para el bus de comunicación I2C. |
| **Buzzer Activo** | I/O (Señal) | 12 | Salida Digital | Pulso en estado HIGH/LOW para excitar la membrana sonora. |
| | GND | GND | Alimentación | Cierre del circuito hacia el plano de tierra del sistema. |