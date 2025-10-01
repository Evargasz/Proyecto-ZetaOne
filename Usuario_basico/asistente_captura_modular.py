import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import json
from datetime import datetime

# Importaciones del proyecto
from styles import etiqueta_titulo, entrada_estandar, boton_accion, boton_exito, boton_rojo
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from util_rutas import recurso_path

# Importaciones condicionales
try:
    from Usuario_basico import grabador_video
    from Usuario_basico import capturador_pantallas
    MODULOS_DISPONIBLES = True
except ImportError as e:
    MODULOS_DISPONIBLES = False
    IMPORT_ERROR = str(e)

class AsistenteCapturaModular(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Asistente de Captura y Grabación")
        self.geometry("650x650")
        self.resizable(True, True)
        self.minsize(600, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_salir)
        
        # Habilitar botón minimizar
        self.attributes("-toolwindow", False)
        
        # Variables de estado
        self.proceso_captura = None
        self.proceso_video = None
        
        # Configuración
        self.config_file = recurso_path("json", "config.json")
        self.objetivos_base = []
        
        # Variables de selección
        self.captura_var = tk.StringVar()
        self.video_var = tk.StringVar()
        
        # Variables de control de objetivo actual
        self.objetivo_captura_actual = None
        self.objetivo_video_actual = None
        
        self.crear_interfaz()
        self.cargar_configuracion()
        self.centrar_ventana()
        
    def centrar_ventana(self):
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def crear_interfaz(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Título
        titulo = etiqueta_titulo(
            main_frame, 
            texto="Asistente de Captura y Grabación",
            font=("Arial", 16, "bold")
        )
        titulo.pack(pady=(0, 15))
        
        if not MODULOS_DISPONIBLES:
            self.mostrar_error_dependencias(main_frame)
            return
        
        # Frame superior para las secciones
        superior_frame = tb.Frame(main_frame)
        superior_frame.pack(fill="x", pady=(0, 10))
        
        # Sección de Captura de Pantallas
        self.crear_seccion_captura(superior_frame)
        
        # Sección de Grabación de Video
        self.crear_seccion_video(superior_frame)
        
        # Log de actividad (más grande)
        self.crear_seccion_log(main_frame)
        
        # Botones inferiores (siempre visibles)
        self.crear_botones_inferiores(main_frame)

    def mostrar_error_dependencias(self, parent):
        error_frame = tb.Frame(parent)
        error_frame.pack(fill="both", expand=True)
        
        etiqueta_titulo(
            error_frame,
            texto="⚠️ Módulos No Disponibles",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        mensaje = f"Error cargando módulos:\n{IMPORT_ERROR}\n\nVerifica que los archivos existan:\n• grabador_video.py\n• capturador_pantallas.py"
        etiqueta_titulo(error_frame, texto=mensaje).pack(pady=10)
        
        boton_rojo(
            error_frame, 
            "Cerrar", 
            comando=self.destroy,
            width=15
        ).pack(pady=20)

    def crear_seccion_captura(self, parent):
        captura_frame = tb.LabelFrame(parent, text="📸 Capturador de Pantallas", padding=8)
        captura_frame.pack(fill="x", pady=(0, 5))
        
        # Selector de objetivo
        selector_frame = tb.Frame(captura_frame)
        selector_frame.pack(fill="x", pady=(0, 5))
        
        tb.Label(selector_frame, text="Objetivo:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))
        
        self.captura_combo = tb.Combobox(
            selector_frame,
            textvariable=self.captura_var,
            state="readonly",
            font=("Arial", 9),
            width=35
        )
        self.captura_combo.pack(side="left", fill="x", expand=True)
        self.captura_combo.bind("<<ComboboxSelected>>", self.on_captura_objetivo_changed)
        
        info_text = "F8: Capturar ventana seleccionada | ESC: Salir del capturador"
        etiqueta_titulo(captura_frame, texto=info_text, font=("Arial", 8)).pack(pady=(5, 5))
        
        self.btn_captura = tb.Button(
            captura_frame,
            text="🔴 Iniciar Capturador",
            command=self.toggle_capturador,
            bootstyle="success",
            width=25
        )
        self.btn_captura.pack(pady=(0, 5))

    def crear_seccion_video(self, parent):
        video_frame = tb.LabelFrame(parent, text="🎥 Grabador de Video", padding=8)
        video_frame.pack(fill="x", pady=(0, 5))
        
        # Selector de objetivo
        selector_frame = tb.Frame(video_frame)
        selector_frame.pack(fill="x", pady=(0, 5))
        
        tb.Label(selector_frame, text="Objetivo:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))
        
        self.video_combo = tb.Combobox(
            selector_frame,
            textvariable=self.video_var,
            state="readonly",
            font=("Arial", 9),
            width=35
        )
        self.video_combo.pack(side="left", fill="x", expand=True)
        self.video_combo.bind("<<ComboboxSelected>>", self.on_video_objetivo_changed)
        
        info_text = "F9: Iniciar/Detener grabación | ESC: Salir del grabador"
        etiqueta_titulo(video_frame, texto=info_text, font=("Arial", 8)).pack(pady=(5, 5))
        
        self.btn_video = tb.Button(
            video_frame,
            text="🎥 Iniciar Grabador",
            command=self.iniciar_grabador,
            bootstyle="primary",
            width=25
        )
        self.btn_video.pack(pady=(0, 5))

    def crear_seccion_log(self, parent):
        log_frame = tb.LabelFrame(parent, text="📋 Log de Actividad", padding=10)
        log_frame.pack(fill="both", expand=True, pady=(5, 10))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=12, 
            font=("Consolas", 9),
            state="disabled"
        )
        self.log_text.pack(fill="both", expand=True)

    def crear_botones_inferiores(self, parent):
        btn_frame = tb.Frame(parent)
        btn_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        # Frame para centrar botones
        botones_centrados = tb.Frame(btn_frame)
        botones_centrados.pack(expand=True)
        
        boton_accion(
            botones_centrados,
            "⚙️ Editar Objetivos",
            comando=self.abrir_editor_objetivos,
            width=18
        ).pack(side="left", padx=5)
        
        boton_accion(
            botones_centrados,
            "📁 Abrir Capturas",
            comando=self.abrir_carpeta_capturas,
            width=18
        ).pack(side="left", padx=5)
        
        boton_accion(
            botones_centrados,
            "📁 Abrir Grabaciones",
            comando=self.abrir_carpeta_grabaciones,
            width=18
        ).pack(side="left", padx=5)
        
        boton_rojo(
            botones_centrados,
            "🚪 Salir",
            comando=self.on_salir,
            width=15
        ).pack(side="left", padx=5)

    def log(self, mensaje):
        """Añade un mensaje al log con timestamp"""
        try:
            if not hasattr(self, 'log_text') or self.log_text is None:
                print(f"[LOG] {mensaje}")
                return
            
            if not self.log_text.winfo_exists():
                print(f"[LOG] {mensaje}")
                return
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            mensaje_completo = f"[{timestamp}] {mensaje}\n"
            
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, mensaje_completo)
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        except:
            print(f"[LOG] {mensaje}")

    def cargar_configuracion(self):
        """Carga los objetivos y rutas desde config.json"""
        objetivos_default = ["Sistema de Cartera", "C O B I S  Clientes", "C.O.B.I.S TERMINAL ADMINISTRATIVA"]
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.objetivos_base = config.get("objetivos", objetivos_default)
                    self.ruta_capturas = config.get("ruta_capturas", "C:\\ZetaOne\\Capturas")
                    self.ruta_grabaciones = config.get("ruta_grabaciones", "C:\\ZetaOne\\Grabaciones")
            else:
                self.objetivos_base = objetivos_default
                self.ruta_capturas = "C:\\ZetaOne\\Capturas"
                self.ruta_grabaciones = "C:\\ZetaOne\\Grabaciones"
                self.guardar_configuracion()
        except Exception as e:
            self.log(f"Error cargando configuración: {e}")
            self.objetivos_base = objetivos_default
            self.ruta_capturas = "C:\\ZetaOne\\Capturas"
            self.ruta_grabaciones = "C:\\ZetaOne\\Grabaciones"
        
        self.actualizar_combos()
        self.log(f"Objetivos configurados: {', '.join(self.objetivos_base)}")

    def guardar_configuracion(self):
        """Guarda la configuración actual"""
        try:
            config = {
                "objetivos": self.objetivos_base,
                "ruta_capturas": getattr(self, 'ruta_capturas', "C:\\ZetaOne\\Capturas"),
                "ruta_grabaciones": getattr(self, 'ruta_grabaciones', "C:\\ZetaOne\\Grabaciones")
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"Error guardando configuración: {e}")

    def toggle_capturador(self):
        """Alterna entre iniciar y detener el capturador"""
        if self.proceso_captura and self.proceso_captura.poll() is None:
            # Si está activo, cerrarlo
            self.cerrar_capturador()
        else:
            # Si no está activo, iniciarlo
            self.iniciar_capturador()
    
    def iniciar_capturador(self):
        """Inicia el capturador de pantallas en proceso separado"""
        if self.proceso_captura and self.proceso_captura.poll() is None:
            self.log("El capturador ya está ejecutándose")
            return
        
        objetivo_seleccionado = self.captura_var.get()
        if not objetivo_seleccionado:
            self.log("ERROR: Selecciona un objetivo antes de iniciar")
            messagebox.showwarning("Objetivo Requerido", "Selecciona un objetivo antes de iniciar el capturador.")
            return
        
        try:
            self.log(f"Iniciando capturador para: {objetivo_seleccionado}")
            self.log("Instrucciones: F8 = Capturar | ESC = Salir")
            self.btn_captura.config(text="⏹️ Capturador Activo", bootstyle="warning")
            
            # Guardar objetivo actual
            self.objetivo_captura_actual = objetivo_seleccionado
            
            # Crear script temporal con objetivo preseleccionado
            script_captura = f'''
from Usuario_basico.capturador_pantallas import main_con_objetivo
main_con_objetivo("{objetivo_seleccionado}")
'''
            
            self.proceso_captura = subprocess.Popen([
                sys.executable, "-c", script_captura
            ], cwd=os.path.dirname(os.path.dirname(__file__)))
            
            # Monitorear proceso en hilo separado
            threading.Thread(target=self.monitorear_capturador, daemon=True).start()
            
        except Exception as e:
            self.log(f"Error iniciando capturador: {e}")
            self.btn_captura.config(text="🔴 Iniciar Capturador", bootstyle="success")

    def iniciar_grabador(self):
        """Inicia el grabador de video con semáforo integrado"""
        if hasattr(self, 'grabador_activo') and self.grabador_activo:
            # Detener grabador activo
            self.detener_grabador()
            return
        
        objetivo_seleccionado = self.video_var.get()
        if not objetivo_seleccionado:
            self.log("ERROR: Selecciona un objetivo antes de iniciar")
            messagebox.showwarning("Objetivo Requerido", "Selecciona un objetivo antes de iniciar el grabador.")
            return
        
        try:
            self.log(f"Iniciando grabador para: {objetivo_seleccionado}")
            self.log("F9 = Iniciar/Detener grabación | ESC = Salir")
            self.btn_video.config(text="⏹️ Detener Grabador", bootstyle="danger")
            
            # Guardar objetivo actual
            self.objetivo_video_actual = objetivo_seleccionado
            self.grabador_activo = True
            
            # Ejecutar grabador en hilo separado con callback
            def ejecutar_grabador():
                try:
                    from Usuario_basico.grabador_video import main_con_objetivo_con_semaforo
                    main_con_objetivo_con_semaforo(objetivo_seleccionado, self.log)
                except Exception as e:
                    self.log(f"Error en grabador: {e}")
                finally:
                    self.grabador_activo = False
                    try:
                        self.btn_video.config(text="🎥 Iniciar Grabador", bootstyle="primary")
                        self.log("Grabador finalizado")
                    except:
                        pass
            
            self.hilo_grabador = threading.Thread(target=ejecutar_grabador, daemon=True)
            self.hilo_grabador.start()
            
        except Exception as e:
            self.log(f"Error iniciando grabador: {e}")
            self.btn_video.config(text="🎥 Iniciar Grabador", bootstyle="primary")
            self.grabador_activo = False
    
    def detener_grabador(self):
        """Detiene el grabador activo (solo si no está grabando)"""
        # Verificar si hay semáforo activo y está grabando o en pausa
        try:
            from Usuario_basico.grabador_video import semaforo_global
            if semaforo_global and semaforo_global.estado in ["grabando", "pausado"]:
                self.log(f"⚠️ NO SE PUEDE DETENER: {semaforo_global.estado.upper()}")
                return  # Bloquear si está grabando o en pausa
            
            # Cerrar semáforo directamente
            if semaforo_global:
                semaforo_global.ocultar()
                self.log("✓ Semáforo cerrado directamente")
        except Exception as e:
            self.log(f"Error cerrando semáforo: {e}")
        
        if hasattr(self, 'grabador_activo'):
            self.grabador_activo = False
        
        # Enviar ESC para cerrar grabador
        try:
            import keyboard
            keyboard.press_and_release('esc')
            self.log("✓ ESC enviado al grabador")
        except:
            pass
            
        self.btn_video.config(text="🎥 Iniciar Grabador", bootstyle="primary")
        self.objetivo_video_actual = None
        self.log("Grabador detenido por usuario")

    def on_captura_objetivo_changed(self, event=None):
        """Se ejecuta cuando cambia el objetivo de captura"""
        nuevo_objetivo = self.captura_var.get()
        
        # Si hay un capturador activo y el objetivo cambió
        if (self.proceso_captura and self.proceso_captura.poll() is None and 
            self.objetivo_captura_actual and nuevo_objetivo != self.objetivo_captura_actual):
            
            self.log(f"Objetivo cambiado de '{self.objetivo_captura_actual}' a '{nuevo_objetivo}' - Cerrando capturador")
            self.cerrar_capturador()
    
    def on_video_objetivo_changed(self, event=None):
        """Se ejecuta cuando cambia el objetivo de video"""
        nuevo_objetivo = self.video_var.get()
        
        # Si hay un grabador activo y el objetivo cambió
        if (hasattr(self, 'grabador_activo') and self.grabador_activo and 
            self.objetivo_video_actual and nuevo_objetivo != self.objetivo_video_actual):
            
            self.log(f"Objetivo cambiado de '{self.objetivo_video_actual}' a '{nuevo_objetivo}' - Cerrando grabador")
            self.cerrar_grabador()
    
    def cerrar_capturador(self):
        """Cierra el capturador activo"""
        if self.proceso_captura and self.proceso_captura.poll() is None:
            try:
                self.proceso_captura.terminate()
                self.proceso_captura.wait(timeout=3)
            except:
                try:
                    self.proceso_captura.kill()
                except:
                    pass
            
            self.btn_captura.config(text="🔴 Iniciar Capturador", bootstyle="success")
            self.objetivo_captura_actual = None
            self.log("Capturador cerrado por cambio de objetivo")
    
    def cerrar_grabador(self):
        """Cierra el grabador activo"""
        # Verificar si está grabando o en pausa antes de cerrar
        try:
            from Usuario_basico.grabador_video import semaforo_global
            if semaforo_global and semaforo_global.estado in ["grabando", "pausado"]:
                self.log(f"⚠️ NO SE PUEDE CERRAR: {semaforo_global.estado.upper()}")
                return
            
            # Cerrar semáforo directamente
            if semaforo_global:
                semaforo_global.ocultar()
                self.log("✓ Semáforo cerrado por cambio de objetivo")
        except:
            pass
        
        # Simular ESC para cerrar completamente
        try:
            import keyboard
            keyboard.press_and_release('esc')
        except:
            pass
        
        self.detener_grabador()
        self.log("Grabador cerrado por cambio de objetivo")
    
    def monitorear_capturador(self):
        """Monitorea el proceso del capturador"""
        if self.proceso_captura:
            self.proceso_captura.wait()
            try:
                self.btn_captura.config(text="🔴 Iniciar Capturador", bootstyle="success")
                self.objetivo_captura_actual = None
                self.log("Capturador finalizado")
            except:
                pass

    def monitorear_grabador(self):
        """Función mantenida para compatibilidad"""
        pass

    def abrir_editor_objetivos(self):
        """Abre el editor de objetivos"""
        EditorObjetivos(self)
    
    def actualizar_combos(self):
        """Actualiza los combobox con los objetivos disponibles"""
        if not hasattr(self, 'captura_combo') or not hasattr(self, 'video_combo'):
            return
        
        # Opciones para captura (incluye pantalla completa)
        opciones_captura = list(self.objetivos_base)
        if len(self.objetivos_base) >= 2:
            opciones_captura.append(f"{self.objetivos_base[0]} y {self.objetivos_base[1]}")
        opciones_captura.append("Pantalla Completa")
        
        self.captura_combo['values'] = opciones_captura
        if opciones_captura:
            self.captura_combo.current(0)
        
        # Opciones para video (solo objetivos configurados)
        opciones_video = list(self.objetivos_base)
        if len(self.objetivos_base) >= 2:
            opciones_video.append("Ambas Aplicaciones")
        
        self.video_combo['values'] = opciones_video
        if opciones_video:
            self.video_combo.current(0)
    
    def abrir_carpeta_capturas(self):
        """Abre la carpeta de capturas en el explorador"""
        try:
            carpeta_capturas = getattr(self, 'ruta_capturas', "C:\\ZetaOne\\Capturas")
            os.makedirs(carpeta_capturas, exist_ok=True)
            os.startfile(carpeta_capturas)
            self.log(f"Abriendo carpeta: {carpeta_capturas}")
        except Exception as e:
            self.log(f"Error abriendo carpeta: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de capturas.\n\nError: {e}")
    
    def abrir_carpeta_grabaciones(self):
        """Abre la carpeta de grabaciones en el explorador"""
        try:
            carpeta_grabaciones = getattr(self, 'ruta_grabaciones', "C:\\ZetaOne\\Grabaciones")
            os.makedirs(carpeta_grabaciones, exist_ok=True)
            os.startfile(carpeta_grabaciones)
            self.log(f"Abriendo carpeta: {carpeta_grabaciones}")
        except Exception as e:
            self.log(f"Error abriendo carpeta: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de grabaciones.\n\nError: {e}")

    def on_salir(self):
        """Maneja el cierre de la ventana"""
        # Terminar procesos activos
        self.cerrar_capturador()
        self.detener_grabador()
        
        self.destroy()

class EditorObjetivos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Configuración de Captura y Grabación")
        self.geometry("600x550")
        self.resizable(False, False)
        
        self.crear_interfaz()
        self.cargar_configuracion()
        
        # Hacer modal
        self.transient(parent)
        self.focus_set()
        self.grab_set()
        
        # Centrar
        self.centrar_ventana()

    def centrar_ventana(self):
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def crear_interfaz(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Título
        etiqueta_titulo(
            main_frame,
            texto="Configuración de Captura y Grabación",
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 15))
        
        # Sección de Objetivos
        objetivos_frame = tb.LabelFrame(main_frame, text="Objetivos de Captura y Grabación", padding=10)
        objetivos_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        instrucciones = (
            "Escriba los títulos exactos de las ventanas objetivo (un título por línea):\n"
            "Ejemplos: Sistema de Cartera, C O B I S  Clientes, etc."
        )
        
        etiqueta_titulo(
            objetivos_frame,
            texto=instrucciones,
            font=("Arial", 9)
        ).pack(pady=(0, 10), anchor="w")
        
        self.text_area = scrolledtext.ScrolledText(
            objetivos_frame,
            height=6,
            font=("Consolas", 10),
            wrap="word"
        )
        self.text_area.pack(fill="both", expand=True)
        
        # Sección de Carpetas
        carpetas_frame = tb.LabelFrame(main_frame, text="Carpetas de Guardado", padding=10)
        carpetas_frame.pack(fill="x", pady=(0, 15))
        
        # Carpeta de Capturas
        tb.Label(carpetas_frame, text="Carpeta de Capturas:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        capturas_input_frame = tb.Frame(carpetas_frame)
        capturas_input_frame.pack(fill="x", pady=(0, 10))
        
        self.capturas_entry = entrada_estandar(capturas_input_frame, font=("Arial", 9))
        self.capturas_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        boton_accion(
            capturas_input_frame,
            "Examinar",
            comando=lambda: self.examinar_carpeta(self.capturas_entry),
            width=10
        ).pack(side="right")
        
        # Carpeta de Grabaciones
        tb.Label(carpetas_frame, text="Carpeta de Grabaciones:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        grabaciones_input_frame = tb.Frame(carpetas_frame)
        grabaciones_input_frame.pack(fill="x")
        
        self.grabaciones_entry = entrada_estandar(grabaciones_input_frame, font=("Arial", 9))
        self.grabaciones_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        boton_accion(
            grabaciones_input_frame,
            "Examinar",
            comando=lambda: self.examinar_carpeta(self.grabaciones_entry),
            width=10
        ).pack(side="right")
        
        # Botones inferiores centrados
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(15, 0))
        
        botones_centrados = tb.Frame(btn_frame)
        botones_centrados.pack(expand=True)
        
        boton_exito(
            botones_centrados,
            "✓ Guardar",
            comando=self.guardar_configuracion,
            width=15
        ).pack(side="left", padx=10)
        
        boton_rojo(
            botones_centrados,
            "❌ Salir",
            comando=self.destroy,
            width=15
        ).pack(side="left", padx=10)

    def cargar_configuracion(self):
        """Carga la configuración actual"""
        # Cargar objetivos
        objetivos_texto = "\n".join(self.parent.objetivos_base)
        self.text_area.insert("1.0", objetivos_texto)
        
        # Cargar rutas
        self.capturas_entry.delete(0, tk.END)
        self.capturas_entry.insert(0, getattr(self.parent, 'ruta_capturas', "C:\\ZetaOne\\Capturas"))
        
        self.grabaciones_entry.delete(0, tk.END)
        self.grabaciones_entry.insert(0, getattr(self.parent, 'ruta_grabaciones', "C:\\ZetaOne\\Grabaciones"))

    def examinar_carpeta(self, entry_widget):
        """Abre selector de carpeta usando PowerShell"""
        import subprocess
        import tempfile
        
        temp_file = os.path.join(tempfile.gettempdir(), "zetaone_folder_selection.txt")
        
        ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$browser = New-Object System.Windows.Forms.FolderBrowserDialog
$browser.Description = "Seleccionar carpeta"
$browser.SelectedPath = "{entry_widget.get() if os.path.exists(entry_widget.get()) else 'C:\\'}"
$result = $browser.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    $browser.SelectedPath | Out-File -FilePath "{temp_file}" -Encoding ASCII
}}
'''
        
        try:
            subprocess.run(["powershell", "-Command", ps_script], 
                         creationflags=subprocess.CREATE_NO_WINDOW)
            
            if os.path.exists(temp_file):
                with open(temp_file, 'r', encoding='utf-8-sig') as f:
                    carpeta = f.read().strip().lstrip('\ufeff')
                
                if carpeta:
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, carpeta)
                
                os.remove(temp_file)
                
        except Exception as e:
            messagebox.showerror("Error", "No se pudo abrir el selector de carpeta.")
    
    def guardar_configuracion(self):
        """Guarda toda la configuración editada"""
        # Validar objetivos
        texto = self.text_area.get("1.0", tk.END).strip()
        nuevos_objetivos = [linea.strip() for linea in texto.split("\n") if linea.strip()]
        
        if not nuevos_objetivos:
            messagebox.showwarning("Error", "Debe especificar al menos un objetivo.")
            return
        
        # Validar rutas
        nueva_ruta_capturas = self.capturas_entry.get().strip()
        nueva_ruta_grabaciones = self.grabaciones_entry.get().strip()
        
        if not nueva_ruta_capturas or not nueva_ruta_grabaciones:
            messagebox.showwarning("Error", "Debe especificar ambas rutas de guardado.")
            return
        
        # Intentar crear las carpetas
        try:
            os.makedirs(nueva_ruta_capturas, exist_ok=True)
            os.makedirs(nueva_ruta_grabaciones, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron crear las carpetas:\n{e}")
            return
        
        # Guardar configuración
        self.parent.objetivos_base = nuevos_objetivos
        self.parent.ruta_capturas = nueva_ruta_capturas
        self.parent.ruta_grabaciones = nueva_ruta_grabaciones
        self.parent.guardar_configuracion()
        self.parent.actualizar_combos()
        self.parent.log(f"Configuración actualizada: {len(nuevos_objetivos)} objetivos")
        self.parent.log(f"Rutas actualizadas - Capturas: {nueva_ruta_capturas}")
        self.parent.log(f"Rutas actualizadas - Grabaciones: {nueva_ruta_grabaciones}")
        
        messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
        self.destroy()

# Función para usar desde el menú principal
def abrir_asistente_captura_modular(master):
    """Función para abrir el asistente modular desde el menú principal"""
    ventana = AsistenteCapturaModular(master)
    ventana.grab_set()
    return ventana