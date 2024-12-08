import serial
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import serial.tools.list_ports
import time
import threading

# Configuración global
MAX_DATA_POINTS = 100
DATA_INTERVAL = 100  # Intervalo de actualización en milisegundos
DATA_POINTS = 50  # Puntos máximos a graficar

class Interfaz:
    def __init__(self, root):   
        self.root = root
        self.root.title("Control de posición")
        self.root.geometry("1000x500")

        self.comboBox1 = ttk.Combobox(root, state="readonly")
        self.comboBox1.place(x=100, y=303)
        self.comboBox1.set("Seleccione puerto")
        self.comboBox1.bind("<<ComboboxSelected>>", self.on_combobox_select)

        self.conectarButton = tk.Button(root, text="Conectar", state="disabled", command=self.connect_serial)
        self.conectarButton.place(x=250, y=300)

        self.instrucciones = tk.Label(root, text="Ingrese un ángulo", font=(13))
        self.instrucciones.place(x=150, y=100)

        self.anguloInput = tk.Entry(root)
        self.anguloInput.place(x=150, y=150)

        self.enviarButton = tk.Button(root, text="Enviar", state="disabled", command=self.send_data)
        self.enviarButton.place(x=190, y=200)

        self.validador_angulo = tk.Label(root, text="Ángulo inválido", fg="red")

        # Inicializar serial y gráfica
        self.serial_port = None
        self.create_chart(root)
        self.update_ports()

        # Inicializar colas para datos
        self.angles = deque([0] * DATA_POINTS, maxlen=DATA_POINTS)
        self.times = deque([0] * DATA_POINTS, maxlen=DATA_POINTS)
        self.start_time = time.time()

        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)

    def send_data(self):
        angulo = self.anguloInput.get()
        try:
            angulo_float = float(angulo)
            if angulo_float < 0 or angulo_float > 360:
                self.validador_angulo.place(x=170, y=170)
            else:
                self.validador_angulo.place_forget()
                if self.serial_port:
                    self.serial_port.write(f"{angulo}\n".encode())
        except ValueError:
            self.validador_angulo.place(x=170, y=170)

    def on_combobox_select(self, event):
        if self.comboBox1.get() != "Seleccione puerto":
            self.conectarButton.config(state="normal")
        else:
            self.conectarButton.config(state="disabled")

    def connect_serial(self):
        puerto_seleccionado = self.comboBox1.get()
        try:
            self.serial_port = serial.Serial(puerto_seleccionado, 9600, timeout=1)
            self.enviarButton.config(state="normal")
            threading.Thread(target=self.read_from_serial, daemon=True).start()
        except serial.SerialException as e:
            print(f"Error al conectar con el puerto: {e}")
            self.serial_port = None

    def create_chart(self, root):
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Valores de Ángulo en Tiempo Real")
        self.ax.set_xlabel("Tiempo (s)")
        self.ax.set_ylabel("Ángulo (°)")
        self.line, = self.ax.plot([], [], lw=2, label="Ángulo")
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().place(x=600, y=50, width=400, height=400)
        self.canvas.draw()

        self.ani = FuncAnimation(self.fig, self.update_chart, interval=DATA_INTERVAL)

    def update_chart(self, frame):
        if len(self.times) > 1:
            self.line.set_data(self.times, self.angles)
            self.ax.set_xlim(min(self.times), max(self.times))
            self.ax.set_ylim(min(self.angles) - 10, max(self.angles) + 10)
            self.canvas.draw()
        return self.line

    def read_from_serial(self):
        while self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.readline().decode('utf-8').strip()
                if data:
                    angulo = float(data)
                    tiempo_actual = time.time() - self.start_time
                    self.times.append(tiempo_actual)
                    self.angles.append(angulo)
            except (ValueError, serial.SerialException):
                pass

    def update_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if ports:
            self.comboBox1['values'] = ports
            self.comboBox1.set("Seleccione una opción")
        else:
            self.comboBox1.set("No hay puertos disponibles")
            self.comboBox1.config(state="disabled")

    def cerrar_ventana(self):
        if self.serial_port:
            self.serial_port.close()
        self.root.quit()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = Interfaz(root)
    root.mainloop()

if __name__ == "__main__":
    main()
