import tkinter as tk
from tkinter import ttk
import threading
import time

class SemaforoGrabacion:
    def __init__(self):
        self.ventana = None
        self.estado = "inactivo"  # inactivo, grabando, pausado
        self.tiempo_inicio = 0
        self.tiempo_transcurrido = 0
        self.hilo_actualizacion = None
        self.activo = False
        
    def mostrar(self):
        """Muestra el semáforo flotante"""
        if self.ventana:
            return
            
        self.ventana = tk.Toplevel()
        self.ventana.title("Grabación")
        self.ventana.geometry("200x75")
        self.ventana.resizable(False, False)
        
        # Posicionar en esquina superior derecha
        self.ventana.update_idletasks()
        screen_width = self.ventana.winfo_screenwidth()
        x = screen_width - 220  # 200px ancho + 20px margen
        y = 10
        self.ventana.geometry(f"200x75+{x}+{y}")
        
        # Asegurar posición en esquina superior derecha al mostrar
        self.ventana.after(100, lambda: self.ventana.geometry(f"200x75+{x}+{y}"))
        
        # Configurar ventana flotante
        self.ventana.attributes("-topmost", True)
        # REMOVIDO: -toolwindow (deshabilitaba la X)
        
        # Bloquear minimizar durante grabación o pausa
        def bloquear_minimizar(event=None):
            if self.estado in ["grabando", "pausado"]:
                print(f"\n⚠️ NO SE PUEDE MINIMIZAR: Estado {self.estado.upper()}")
                self.ventana.deiconify()  # Restaurar si se minimizó
                return "break"
        
        self.ventana.bind("<Unmap>", bloquear_minimizar)
        
        # Configurar cierre con X
        def intentar_cerrar():
            if self.estado in ["grabando", "pausado"]:
                print(f"\n⚠️ NO SE PUEDE CERRAR: Estado {self.estado.upper()}")
                return  # Bloquear cierre durante grabación o pausa
            else:
                print("\n🔥 X DETECTADA - CERRANDO SEMÁFORO Y GRABADOR")
                self.cerrar_con_x()
        
        self.ventana.protocol("WM_DELETE_WINDOW", intentar_cerrar)
        
        # Frame principal
        frame = tk.Frame(self.ventana, bg="#2c3e50", padx=8, pady=6)
        frame.pack(fill="both", expand=True)
        
        # Indicador circular
        self.canvas = tk.Canvas(frame, width=30, height=30, bg="#2c3e50", highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 10))
        
        # Crear círculo
        self.circulo = self.canvas.create_oval(5, 5, 25, 25, fill="#95a5a6", outline="#7f8c8d", width=2)
        
        # Frame para texto
        texto_frame = tk.Frame(frame, bg="#2c3e50")
        texto_frame.pack(side="left", fill="both", expand=True)
        
        # Etiquetas
        self.label_estado = tk.Label(texto_frame, text="LISTO", font=("Arial", 10, "bold"), 
                                   fg="#ecf0f1", bg="#2c3e50")
        self.label_estado.pack(anchor="w")
        
        self.label_tiempo = tk.Label(texto_frame, text="00:00", font=("Arial", 9), 
                                   fg="#bdc3c7", bg="#2c3e50")
        self.label_tiempo.pack(anchor="w")
        
        # Ayuda F9
        self.label_ayuda = tk.Label(texto_frame, text="F9: Iniciar/Detener", font=("Arial", 7), 
                                  fg="#95a5a6", bg="#2c3e50")
        self.label_ayuda.pack(anchor="w")
        
        self.activo = True
        self.iniciar_actualizacion()
        
        print(f"\n✓ Semáforo mostrado en posición: {x}, {y}")
        print("\n🔴 PRUEBA: Haz clic en la X de la barra de título del semáforo")
        
    def ocultar(self):
        """Oculta el semáforo"""
        self.activo = False
        if self.ventana:
            try:
                self.ventana.destroy()
                self.ventana = None
            except:
                pass
    
    def cerrar_con_x(self):
        """Cierra el semáforo y finaliza el grabador"""
        print("\n❌ CERRANDO SEMÁFORO Y FINALIZANDO GRABADOR...")
        
        # Enviar ESC para finalizar grabador completamente
        try:
            import keyboard
            keyboard.press_and_release('esc')
            print("✓ ESC enviado - Finalizando grabador")
        except Exception as e:
            print(f"⚠️ Error enviando ESC: {e}")
        
        # Cerrar semáforo inmediatamente
        self.activo = False
        self.estado = "inactivo"
        
        if self.ventana:
            try:
                self.ventana.destroy()
                self.ventana = None
                print("✓ Semáforo cerrado")
            except:
                pass
        
        print("✓ Grabador finalizado desde semáforo")
            
    def iniciar_grabacion(self):
        """Cambia estado a grabando"""
        self.estado = "grabando"
        self.tiempo_inicio = time.time()
        self.actualizar_visual()
        
    def pausar_grabacion(self):
        """Cambia estado a pausado"""
        if self.estado == "grabando":
            self.tiempo_transcurrido += time.time() - self.tiempo_inicio
        self.estado = "pausado"
        self.actualizar_visual()
        
    def reanudar_grabacion(self):
        """Reanuda la grabación"""
        self.estado = "grabando"
        self.tiempo_inicio = time.time()
        self.actualizar_visual()
        
    def detener_grabacion(self):
        """Detiene la grabación pero NO cierra el semáforo"""
        if self.estado == "grabando":
            self.tiempo_transcurrido += time.time() - self.tiempo_inicio
        self.estado = "inactivo"  # Vuelve a LISTO
        self.tiempo_transcurrido = 0
        self.actualizar_visual()
        print("✓ Grabación detenida - Semáforo en modo LISTO")
        
    def actualizar_visual(self):
        """Actualiza la apariencia del semáforo"""
        if not self.ventana or not self.activo:
            return
            
        try:
            if self.estado == "grabando":
                # Rojo parpadeante
                self.canvas.itemconfig(self.circulo, fill="#e74c3c")
                self.label_estado.config(text="GRABANDO", fg="#e74c3c")
            elif self.estado == "pausado":
                # Amarillo
                self.canvas.itemconfig(self.circulo, fill="#f39c12")
                self.label_estado.config(text="PAUSADO", fg="#f39c12")
            else:
                # Gris
                self.canvas.itemconfig(self.circulo, fill="#95a5a6")
                self.label_estado.config(text="LISTO", fg="#ecf0f1")
        except:
            pass
            
    def actualizar_tiempo(self):
        """Actualiza el tiempo mostrado"""
        if not self.ventana or not self.activo:
            return
            
        try:
            if self.estado == "grabando":
                tiempo_actual = self.tiempo_transcurrido + (time.time() - self.tiempo_inicio)
            else:
                tiempo_actual = self.tiempo_transcurrido
                
            minutos = int(tiempo_actual // 60)
            segundos = int(tiempo_actual % 60)
            self.label_tiempo.config(text=f"{minutos:02d}:{segundos:02d}")
        except:
            pass
            
    def iniciar_actualizacion(self):
        """Inicia el hilo de actualización"""
        def actualizar():
            while self.activo:
                self.actualizar_tiempo()
                if self.estado == "grabando":
                    # Parpadeo para grabando
                    try:
                        color_actual = self.canvas.itemcget(self.circulo, "fill")
                        nuevo_color = "#c0392b" if color_actual == "#e74c3c" else "#e74c3c"
                        self.canvas.itemconfig(self.circulo, fill=nuevo_color)
                    except:
                        pass
                time.sleep(0.5)
                
        self.hilo_actualizacion = threading.Thread(target=actualizar, daemon=True)
        self.hilo_actualizacion.start()