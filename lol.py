import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import time

# Configuración del puerto serial
PORT = 'COM3'  # Cambia esto al puerto donde está conectado tu Arduino
BAUD_RATE = 9600
DATA_POINTS = 1000 # Número de puntos a graficar

# Inicializar puerto serial
ser = serial.Serial(PORT, BAUD_RATE, timeout=1)

# Esperar a que Arduino se reinicie
time.sleep(2)

# Enviar un número para que el Arduino comience a enviar datos
ser.write(b'1\n')

# Cola para almacenar datos
angles = deque([0] * DATA_POINTS, maxlen=DATA_POINTS)
times = deque([0] * DATA_POINTS, maxlen=DATA_POINTS)

# Función para leer datos del puerto serial
def read_serial_data():
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            return float(line)  # Convertir el dato a float
    except Exception as e:
        print(f"Error leyendo datos: {e}")
    return None

# Función para actualizar la gráfica
def update(frame):
    data = read_serial_data()
    if data is not None:
        angles.append(data)
        current_time = frame * 0.05  # Tiempo en segundos, ajusta el intervalo
        times.append(current_time)
    line.set_ydata(angles)
    line.set_xdata(times)  # Establecer los tiempos en el eje X
    return line,

# Configuración de la gráfica
fig, ax = plt.subplots()
line, = ax.plot(range(DATA_POINTS), [0] * DATA_POINTS, label="Ángulo Actual")
ax.set_ylim(-360, 360)
ax.set_xlim(0, DATA_POINTS)  # Inicialmente limitado a 100 puntos
ax.set_title("Gráfica en Tiempo Real del Ángulo Actual")
ax.set_xlabel("Tiempo (segundos)")
ax.set_ylabel("Ángulo (grados)")
ax.legend()

# Animación de la gráfica
ani = FuncAnimation(fig, update, interval=50)

# Mostrar la gráfica
plt.show()

# Cerrar el puerto serial al terminar
ser.close()
