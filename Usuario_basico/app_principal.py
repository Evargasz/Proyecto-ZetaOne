import tkinter as tk
from tkinter import ttk, font
import threading
import time
import os
import json
from docx import Document

# Importamos la lógica de nuestros scripts existentes
from capturador_pantallas import (
    encontrar_ventana,
    agregar_a_word,
    capturar_y_guardar
)
from grabador_video import (
    iniciar_grabacion,
    detener_grabacion,
    grabar_frame,
    pausar_por_foco,
)

class ToolTip:
    """Crea un tooltip para un widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class AppPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- Configuración de la Ventana Principal ---
        self.title("Asistente de Captura y Grabación")
        self.geometry("500x400")
        self.resizable(False, False)

        # --- Archivo de Configuración ---
        self.config_file = "config.json"
        
        # --- Estilos y Fuentes ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # Un tema limpio
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        self.style.configure('TButton', font=('Segoe UI', 10))
        self.style.configure('Red.TButton', foreground='white', background='red')

        # --- Variables de Estado ---
        self.capturador_activo = False
        self.grabacion_activa = False
        self.hilo_capturador = None
        self.hilo_grabador = None
        self.video_writer_info = {}

        # --- Construcción de la UI ---
        self.crear_widgets()
        self.cargar_configuracion()

        # --- Manejo del Cierre de la Ventana ---
        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    def crear_widgets(self):
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Sección de Captura de Pantallas ---
        captura_frame = ttk.LabelFrame(main_frame, text="Capturador de Pantallas", padding="10")
        captura_frame.pack(fill=tk.X, pady=5)

        ttk.Label(captura_frame, text="Seleccionar objetivo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.captura_opcion = tk.StringVar(value="Cargando...")
        self.captura_combo = ttk.Combobox(captura_frame, textvariable=self.captura_opcion, state="readonly", width=30)
        self.captura_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.btn_activar_captura = ttk.Button(captura_frame, text="Activar Capturador (F8)", command=self.toggle_capturador)
        self.btn_activar_captura.grid(row=1, column=0, columnspan=2, pady=10)
        ToolTip(self.btn_activar_captura, "Prepara el sistema para tomar capturas con la tecla F8.\nPresiona Esc en la consola para desactivar.")

        # --- Sección de Grabación de Video ---
        video_frame = ttk.LabelFrame(main_frame, text="Grabador de Video", padding="10")
        video_frame.pack(fill=tk.X, pady=5)

        ttk.Label(video_frame, text="Seleccionar objetivo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.video_opcion = tk.StringVar(value="Cargando...")
        self.video_combo = ttk.Combobox(video_frame, textvariable=self.video_opcion, state="readonly", width=30)
        self.video_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.btn_grabar_video = ttk.Button(video_frame, text="Iniciar Grabación (F9)", command=self.toggle_grabacion)
        self.btn_grabar_video.grid(row=1, column=0, columnspan=2, pady=10)
        ToolTip(self.btn_grabar_video, "Inicia o detiene la grabación de video del objetivo seleccionado.")

        # --- Botones inferiores ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))

        self.btn_cerrar = ttk.Button(bottom_frame, text="Cerrar", command=self.al_cerrar)
        self.btn_cerrar.pack(side=tk.RIGHT)

        self.btn_editar_objetivos = ttk.Button(bottom_frame, text="Editar Objetivos", command=self.abrir_ventana_edicion)
        self.btn_editar_objetivos.pack(side=tk.RIGHT, padx=(0, 5))

        self.status_var = tk.StringVar()
        self.status_var.set("Listo. Seleccione una opción y presione un botón.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def actualizar_status(self, mensaje):
        self.status_var.set(mensaje)
        self.update_idletasks()

    def cargar_configuracion(self):
        """Carga los objetivos desde config.json y actualiza los menús."""
        objetivos = ["Sistema de Cartera", "C O B I S  Clientes"] # Default
        if not os.path.exists(self.config_file):
            print(f"No se encontró '{self.config_file}'. Creando uno por defecto.")
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({"objetivos": objetivos}, f, indent=4)
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                objetivos = config.get("objetivos", [])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error al leer el archivo de configuración: {e}. Usando valores por defecto.")
            self.actualizar_status("Error en config.json. Usando valores por defecto.")

        # Guardar los objetivos base para usarlos al reconstruir las listas
        self.objetivos_base = objetivos

        # Actualizar ComboBox de Captura
        opciones_captura = list(self.objetivos_base)
        if len(self.objetivos_base) >= 2:
            opciones_captura.append(f"{self.objetivos_base[0]} y {self.objetivos_base[1]}")
        opciones_captura.append("Todas (Pantalla Completa)")
        self.captura_combo['values'] = opciones_captura
        if opciones_captura: self.captura_combo.current(0)

        # Actualizar ComboBox de Video
        opciones_video = list(self.objetivos_base)
        if len(self.objetivos_base) >= 2:
            opciones_video.append("Ambas (Pantalla Completa)")
        self.video_combo['values'] = opciones_video
        if opciones_video: self.video_combo.current(0)

        self.actualizar_status("Configuración de objetivos cargada.")

    def abrir_ventana_edicion(self):
        EditorObjetivos(self)

    # --- Lógica del Capturador ---
    def toggle_capturador(self):
        if self.capturador_activo:
            return # Ya está activo, no hacer nada

        self.capturador_activo = True
        self.btn_activar_captura.config(state="disabled")
        self.actualizar_status("Capturador activado. Presione F8 para capturar. Cierre la consola para salir.")
        
        seleccion_texto = self.captura_opcion.get()
        # Mapear texto de vuelta a la clave si es necesario, o usar el texto
        seleccion = seleccion_texto
        if len(self.objetivos_base) >= 2 and seleccion_texto == f"{self.objetivos_base[0]} y {self.objetivos_base[1]}":
            seleccion = [self.objetivos_base[0], self.objetivos_base[1]]

        self.hilo_capturador = threading.Thread(target=self.escuchar_capturas, args=(seleccion,), daemon=True)
        self.hilo_capturador.start()

    def escuchar_capturas(self, seleccion):
        nombre_base = ("_y_".join(seleccion) if isinstance(seleccion, list) else seleccion).lower().replace(" ", "_").replace(".", "")
        carpeta_capturas = f"capturas_{nombre_base}"
        nombre_word = f"pantallazos_{nombre_base}.docx"
        os.makedirs(carpeta_capturas, exist_ok=True)

        if os.path.exists(nombre_word):
            doc = Document(nombre_word) # Usamos la clase importada directamente
            primera_captura = False
        else:
            doc = Document() # Usamos la clase importada directamente
            primera_captura = True
        
        contador = 1
        print("\n--- CAPTURADOR ACTIVADO ---")
        print("Presiona F8 para capturar. Presiona Esc para detener el listener.")

        while self.capturador_activo:
            try:
                if keyboard.is_pressed('f8'):
                    resultado = capturar_y_guardar(seleccion, carpeta_capturas, contador)
                    if resultado:
                        nombre_archivo, _ = resultado
                        self.actualizar_status(f"¡Captura {contador} guardada en {os.path.basename(nombre_archivo)}!")
                        agregar_a_word(doc, nombre_archivo, nombre_word, primera=primera_captura)
                        primera_captura = False
                        contador += 1
                    else:
                        self.actualizar_status("Error: No se pudo capturar. ¿La ventana está abierta?")
                    time.sleep(0.5) # Anti-rebote
                
                if keyboard.is_pressed('esc'):
                    self.capturador_activo = False

                time.sleep(0.1)
            except ImportError: # keyboard puede fallar si la consola pierde foco
                self.capturador_activo = False

        self.btn_activar_captura.config(state="normal")
        self.actualizar_status("Capturador desactivado. Listo.")
        print("--- CAPTURADOR DESACTIVADO ---")

    # --- Lógica del Grabador ---
    def toggle_grabacion(self):
        if self.grabacion_activa:
            self.detener_grabacion_thread()
        else:
            self.iniciar_grabacion_thread()

    def iniciar_grabacion_thread(self):
        self.grabacion_activa = True
        self.btn_grabar_video.config(text="Detener Grabación (F9)", style="Red.TButton")
        self.actualizar_status("Iniciando grabación...")

        seleccion_texto = self.video_opcion.get()
        seleccion = seleccion_texto
        if len(self.objetivos_base) >= 2 and seleccion_texto == "Ambas (Pantalla Completa)":
            seleccion = [self.objetivos_base[0], self.objetivos_base[1]]

        self.hilo_grabador = threading.Thread(target=self.bucle_de_grabacion, args=(seleccion,), daemon=True)
        self.hilo_grabador.start()

    def detener_grabacion_thread(self):
        if self.grabacion_activa:
            self.grabacion_activa = False # Señal para que el hilo termine
            # El hilo se encargará de liberar recursos y actualizar el estado

    def bucle_de_grabacion(self, seleccion):
        info = iniciar_grabacion(seleccion)
        if not info:
            self.actualizar_status("Error: No se encontró la ventana de destino.")
            self.grabacion_activa = False
            self.btn_grabar_video.config(text="Iniciar Grabación (F9)", style="TButton")
            return

        self.video_writer_info = info
        self.actualizar_status(f"Grabando... Presiona el botón o F9 para detener.")
        print("\n--- GRABACIÓN INICIADA ---")

        was_paused = False
        while self.grabacion_activa:
            try:
                if keyboard.is_pressed('f9'):
                    self.grabacion_activa = False
                    time.sleep(0.5) # Anti-rebote
                    continue

                # Pausar si la ventana no está en foco
                pausado_actual, was_paused = pausar_por_foco(info['target_pids'], was_paused)
                if pausado_actual:
                    self.actualizar_status("Grabación en pausa (ventana no activa)...")
                    time.sleep(0.5)
                    continue
                else:
                    self.actualizar_status("Grabando...")

                grabar_frame(info)
                time.sleep(1 / info['fps_captura'])

            except Exception as e:
                print(f"Error en bucle de grabación: {e}")
                self.grabacion_activa = False

        # --- Finalizar Grabación ---
        nombre_archivo = detener_grabacion(self.video_writer_info)
        self.btn_grabar_video.config(text="Iniciar Grabación (F9)", style="TButton")
        self.actualizar_status(f"Video guardado en {os.path.basename(nombre_archivo)}")
        self.video_writer_info = {}
        print("--- GRABACIÓN DETENIDA ---")

    def al_cerrar(self):
        """Maneja el cierre de la aplicación de forma segura."""
        self.grabacion_activa = False
        self.capturador_activo = False
        
        if self.video_writer_info.get('writer'):
            print("Cerrando... guardando video pendiente.")
            detener_grabacion(self.video_writer_info)
            time.sleep(1) # Dar tiempo a que se guarde

        self.destroy()

class EditorObjetivos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Editar Objetivos")
        self.geometry("450x380")
        self.resizable(False, False)

        # --- Widgets ---
        info_text = (
            "Añada o edite los títulos de las ventanas de sus aplicaciones objetivo, una por línea.\n"
            "El título debe ser lo más exacto posible para que el programa lo encuentre.\n\n"
            "Ejemplo:\n"
            "Sistema de Cartera\n"
            "C O B I S  Clientes\n"
            "Mi Aplicación Web - Google Chrome"
        )
        info_label = ttk.Label(self, text=info_text, justify=tk.LEFT, wraplength=430)
        info_label.pack(padx=10, pady=10, anchor="w")

        self.text_area = tk.Text(self, wrap="word", height=8, font=('Courier New', 10))
        self.text_area.pack(padx=10, pady=5, fill="both", expand=True)

        # Cargar objetivos actuales en el área de texto
        self.text_area.insert("1.0", "\n".join(self.parent.objetivos_base))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        save_btn = ttk.Button(btn_frame, text="Guardar y Recargar", command=self.guardar_y_cerrar)
        save_btn.pack()

        self.transient(parent)
        self.grab_set()

    def guardar_y_cerrar(self):
        nuevos_objetivos = self.text_area.get("1.0", tk.END).strip().split("\n")
        nuevos_objetivos = [line.strip() for line in nuevos_objetivos if line.strip()]

        with open(self.parent.config_file, 'w', encoding='utf-8') as f:
            json.dump({"objetivos": nuevos_objetivos}, f, indent=4)

        self.parent.cargar_configuracion()
        self.destroy()

if __name__ == "__main__":
    app = AppPrincipal()
    app.mainloop()