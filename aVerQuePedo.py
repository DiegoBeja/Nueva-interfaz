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
DATA_INTERVAL = 15  # Intervalo de actualización en milisegundos
DATA_POINTS = 2000  # Puntos máximos a graficar

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

        self.lazoAbiertoButton = tk.Button(root, text="Lazo abierto", command=self.lazo_abierto)
        self.lazoAbiertoButton.place(x=225, y=400)

        self.lazoCerrado = tk.Button(root, text="Lazo cerrado", command=self.lazo_cerrado)
        self.lazoCerrado.place(x=125, y=400)

        self.validador_angulo = tk.Label(root, text="Ángulo inválido", fg="red")

        self.kpInput = tk.Entry(root)
        self.kpInput.place(x=400, y=150)
        self.kpInput.insert(0, "0.6")

        self.kiInput = tk.Entry(root)
        self.kiInput.place(x=400, y=200)
        self.kiInput.insert(0, "0.003")

        self.kdInput = tk.Entry(root)
        self.kdInput.place(x=400, y=250)
        self.kdInput.insert(0, "0.8")

        self.resetPID = tk.Button(root, text="Reset PID", command=self.reset_pid)
        self.resetPID.place(x=400, y=300)

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
        kp = self.kpInput.get()
        ki = self.kiInput.get()
        kd = self.kdInput.get()

        try:
            angulo_float = float(angulo)
            kp_float = float(kp)
            ki_float = float(ki)
            kd_float = float(kd)

            if angulo_float < 0 or angulo_float > 360:
                self.validador_angulo.place(x=170, y=170)
            else:
                self.validador_angulo.place_forget()
                if self.serial_port:
                    # Enviar los datos formateados como: ángulo, P, I, D
                    data = f"{angulo_float},{kp_float},{ki_float},{kd_float}\n"
                    self.serial_port.write(data.encode())
        except ValueError:
            self.validador_angulo.place(x=170, y=170)


    def lazo_abierto(self):
        print("Lazo abierto")

    def lazo_cerrado(self):
        print("Lazo cerrado")

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
        self.ax.set_xlabel("Tiempo")
        self.ax.set_ylabel("Ángulo")
        self.line, = self.ax.plot([], [], lw=2, label="Ángulo")

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().place(x=570, y=50, width=450, height=400)
        self.canvas.draw()

        self.ani = FuncAnimation(self.fig, self.update_chart, interval=DATA_INTERVAL)

    def reset_pid(self):
        self.kpInput.delete(0, tk.END)
        self.kpInput.insert(0, "0.6")
        self.kiInput.delete(0, tk.END)
        self.kiInput.insert(0, "0.003")
        self.kdInput.delete(0, tk.END)
        self.kdInput.insert(0, "0.8")

    def update_chart(self, frame):
        if len(self.times) > 1:
            self.line.set_data(self.times, self.angles)
            self.ax.set_xlim(min(self.times), max(self.times))
            self.ax.set_ylim(0, 360)  # Rango del eje Y (ángulo)

            self.ax.set_yticks(range(20, 361, 20))

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
