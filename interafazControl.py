import serial
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import serial.tools.list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # Importar el canvas de Tkinter

MAX_DATA_POINTS = 100
angulos = []
tiempos = []

class Interfaz:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de posición")
        self.root.geometry("900x600")  # Aumentamos el tamaño de la ventana para acomodar la gráfica

        self.validador_angulo = tk.Label(root, text="Ángulo inválido", fg="red")
        self.validador_angulo.place(x=350, y=250)

        self.comboBox1 = ttk.Combobox(root, state="readonly")
        self.comboBox1.place(x=50, y=50)
        self.comboBox1.set("Seleccione puerto")
        self.comboBox1.bind("<<ComboboxSelected>>", self.on_combobox_select)

        self.conectarButton = tk.Button(root, text="Conectar", state="disabled", command=self.connect_serial)
        self.conectarButton.place(x=250, y=50)

        self.anguloInput = tk.Entry(root)
        self.anguloInput.place(x=50, y=100)

        self.enviarButton = tk.Button(root, text="Enviar", state="disabled", command=self.send_data)
        self.enviarButton.place(x=200, y=100)

        self.kpInput = tk.Entry(root)
        self.kpInput.place(x=50, y=150)
        self.kpInput.insert(0, "0.6")

        self.kiInput = tk.Entry(root)
        self.kiInput.place(x=50, y=200)
        self.kiInput.insert(0, "0.003")

        self.kdInput = tk.Entry(root)
        self.kdInput.place(x=50, y=250)
        self.kdInput.insert(0, "0.8")

        self.resetPID = tk.Button(root, text="Reset PID", command=self.reset_pid)
        self.resetPID.place(x=50, y=300)

        self.serial_port = None

        self.create_chart(root)  # Crear la gráfica dentro de la interfaz

        # Buscar y actualizar puertos seriales disponibles
        self.update_ports()

    def on_combobox_select(self, event):
        if self.comboBox1.get() != "Seleccione puerto":
            self.conectarButton.config(state="normal")
        else:
            self.conectarButton.config(state="disabled")

    def connect_serial(self):
        puerto_seleccionado = self.comboBox1.get()
        self.serial_port = serial.Serial(puerto_seleccionado, 9600, timeout=1)
        self.enviarButton.config(state="normal")

    def send_data(self):
        angulo = self.anguloInput.get()

        if angulo.isdigit() and int(angulo) >= 0:
            self.validador_angulo.place_forget()
            if self.serial_port:
                self.serial_port.write(angulo.encode())
        else:
            self.validador_angulo.place(x=350, y=250)

    def reset_pid(self):
        self.kpInput.delete(0, tk.END)
        self.kpInput.insert(0, "0.6")
        self.kiInput.delete(0, tk.END)
        self.kiInput.insert(0, "0.003")
        self.kdInput.delete(0, tk.END)
        self.kdInput.insert(0, "0.8")

    def create_chart(self, root):
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Valores de Ángulo en Tiempo Real")
        self.ax.set_xlabel("Tiempo (s)")
        self.ax.set_ylabel("Ángulo (°)")

        self.x_data = []
        self.y_data = []

        self.line, = self.ax.plot([], [], lw=2)

        # Crear el canvas de matplotlib y añadirlo al panel de Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().place(x=300, y=100, width=400, height=250)  # Colocar el canvas en el lugar deseado
        self.canvas.draw()

        ani = FuncAnimation(self.fig, self.update_chart, interval=100, blit = False)
        self.canvas.draw()  # Redibujar la gráfica para actualizarla

    def update_chart(self, frame):
        if self.serial_port and self.serial_port.in_waiting > 0:
            input_data = self.read_from_serial()

            try:
                angulo = float(input_data)
                tiempo = len(self.x_data)  # Tiempo basado en la cantidad de datos recibidos
                self.x_data.append(tiempo)
                self.y_data.append(angulo)


                if len(angulos) > MAX_DATA_POINTS:
                    angulos.pop(0)
                    tiempos.pop(0)

                self.x_data = np.array(tiempos)
                self.y_data = np.array(angulos)

                self.line.set_data(self.x_data, self.y_data)

            except ValueError:
                print(f"Error al convertir los datos: {input_data}")

        self.canvas.draw()
        return self.line,

    
    def read_from_serial(self):
        if self.serial_port:
            try:
                # Leer una línea del puerto serial
                data = self.serial_port.readline()  # Leer como bytes
                try:
                    # Intentar decodificar en UTF-8
                    decoded_data = float(data.decode('utf-8'))
                    if decoded_data and all(c in "0123456789.-" for c in decoded_data):  # Asegurarse de que es numérico
                        return decoded_data  # Solo devolver si es un número
                    else:
                        print(f"Dato no válido: {decoded_data}")
                        return ""  # Ignorar si no es un número
                except UnicodeDecodeError:
                    print(f"Error de decodificación en los datos: {data}")
                    return ""  # Ignorar si no se puede decodificar en UTF-8
            except Exception as e:
                print(f"Error al leer del puerto serial: {e}")
                return ""
        return ""



    def update_ports(self):
        """
        Busca puertos seriales disponibles y actualiza el ComboBox.
        """
        puertos_disponibles = [port.device for port in serial.tools.list_ports.comports()]
        if puertos_disponibles:
            self.comboBox1['values'] = puertos_disponibles
            self.comboBox1.set("Seleccione una opcion")  # Seleccionar el primer puerto disponible
        else:
            self.comboBox1.set("No hay puertos disponibles")
            self.comboBox1.config(state="disabled")


def main():
    root = tk.Tk()
    app = Interfaz(root)
    root.mainloop()


if __name__ == "__main__":
    main()
