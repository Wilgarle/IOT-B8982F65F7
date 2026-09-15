# Interpretación de la asignación

### 1. Situación en el contexto asignado
La situación que se observa en el contexto asignado es como una especie de monitoreo del peso de una estación de empaque.

### 2. Uso y propósito
El principal uso que le veo o que se le puede aplicar es para este proyecto es el de contro de contenido por peso de gramos o abastecimiento de insumos, el cual avisa por medio del buzzer cuando el contenido del contenedor esta llegando a su minimo o esta por debajo de los 2kg para hcaer un reabastecimiento del mismo o tambien De pronto puede ayudar o dar solución a un problema que tenemos en el empaquetado de algún producto para estar seguros de que cumple con alguna medición, en este caso que nos llegue a ser menor de 2 kg o 2000 g.

### 3. Entradas, decisiones y salidas
* **Entrada:** Sería la bascula.
* **Decisión:** Esta va a tener una lógica para que al momento de pesarlo, determine si el valor pesado es por debajo de lo que tenemos principalmente, que en este caso es 2000.
* **Salida:** Vamos a hacer sonar una alarma y que nos muestre en la pantalla este mínimo de peso.

### 4. Regla individual y estado seguro
Para la regla individual de pronto tenemos de tener en cuenta que vamos a tomar dos lecturas bajas para estar seguros de que el peso sí esté por debajo del margen y no sea la primera lectura de pronto un error. Y para asegurarnos de que sea en el rango vamos a colocar 12 g adicional de rango estipulado para que ese margen esté dentro de lo de nuestra asignación.

### 5. Supuestos y limitaciones
* **Supuesto:** Las cajas se van a poner en el centro, lo cual va a generar un supuesto bien o mal uso del dispositivo. Había que agregar como instrucciones para eso. 
* **Limitación 1:** Los datos por ahora no se están guardando en internet.
* **Limitación 2:** No hay como otra instrucción u otro dispositivo agregado a este que nos ayude de pronto con más análisis de los datos que nos entrega este.