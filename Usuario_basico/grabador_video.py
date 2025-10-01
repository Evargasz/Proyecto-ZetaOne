import cv2
import numpy as np
import mss
import pygetwindow as gw
import keyboard
import os
import time
import json
from datetime import datetime
import win32process
import win32gui
import win32api
import sys
from Usuario_basico.semaforo_grabacion import SemaforoGrabacion

# --- Configuración ---
# Variable global para el semáforo
semaforo_global = None
CARPETA_GRABACIONES = "C:\\ZetaOne\\Grabaciones"
FPS_CAPTURA = 20.0  # Fotogramas por segundo a capturar
VELOCIDAD_REPRODUCCION = 2.0 # 1.0 es normal, 2.0 es doble velocidad, etc.
CONFIG_FILE = "json\\config.json"
DEBUG_MODE = False  # Controla la salida de debug

def cargar_objetivos_configurados():
    """Carga los objetivos desde config.json"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("objetivos", [])
    except Exception as e:
        print(f"Error cargando configuración: {e}")
    return []

def es_objetivo_valido(seleccion, objetivos_configurados):
    """Verifica si la selección es un objetivo válido"""
    if isinstance(seleccion, list):
        return all(obj in objetivos_configurados for obj in seleccion)
    return seleccion in objetivos_configurados

def esta_ventana_minimizada(window):
    """Verifica si una ventana está minimizada"""
    try:
        if hasattr(window, 'isMinimized') and window.isMinimized:
            return True
        if hasattr(window, '_hWnd'):
            return win32gui.IsIconic(window._hWnd)
        return False
    except:
        return False

def encontrar_ventanas_objetivo(seleccion):
    """Encuentra ventanas objetivo y verifica que no estén minimizadas"""
    ventanas = []
    titles_to_find = seleccion if isinstance(seleccion, list) else [seleccion]
    
    if DEBUG_MODE:
        print(f"DEBUG: Buscando ventanas para: {titles_to_find}")
    
    for title in titles_to_find:
        if DEBUG_MODE:
            print(f"DEBUG: Buscando '{title}'...")
        
        # Buscar ventanas que contengan el título
        all_windows = gw.getAllWindows()
        matching_windows = []
        
        for window in all_windows:
            if window.title and title.lower() in window.title.lower():
                matching_windows.append(window)
                if DEBUG_MODE:
                    print(f"DEBUG: Encontrada ventana: '{window.title}' ({window.width}x{window.height})")
        
        # Si no encuentra con contenido, buscar exacto
        if not matching_windows:
            matching_windows = gw.getWindowsWithTitle(title)
            if DEBUG_MODE:
                print(f"DEBUG: Búsqueda exacta encontró: {len(matching_windows)} ventanas")
        
        for window in matching_windows:
            if window and window.width > 0 and window.height > 0 and window.visible:
                if not esta_ventana_minimizada(window):
                    ventanas.append(window)
                    if DEBUG_MODE:
                        print(f"DEBUG: Ventana válida agregada: '{window.title}'")
                else:
                    if DEBUG_MODE:
                        print(f"DEBUG: Ventana minimizada ignorada: '{window.title}'")
            else:
                if DEBUG_MODE:
                    print(f"DEBUG: Ventana inválida ignorada: '{window.title if window else 'None'}' (dimensiones o visibilidad)")
    
    if DEBUG_MODE:
        print(f"DEBUG: Total ventanas válidas encontradas: {len(ventanas)}")
    return ventanas

def seleccionar_aplicacion():
    """Muestra un menú con objetivos configurados"""
    objetivos = cargar_objetivos_configurados()
    
    if not objetivos:
        print("ERROR: No hay objetivos configurados en config.json")
        return None
    
    print("Objetivos configurados para grabación:")
    for i, objetivo in enumerate(objetivos, 1):
        print(f"  {i}) {objetivo}")
    
    if len(objetivos) >= 2:
        print(f"  {len(objetivos) + 1}) Ambas Aplicaciones")
    
    while True:
        try:
            choice = input("> ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(objetivos):
                return objetivos[choice_num - 1]
            elif choice_num == len(objetivos) + 1 and len(objetivos) >= 2:
                return [objetivos[0], objetivos[1]]
            else:
                print("Selección inválida.")
        except ValueError:
            print("Por favor, ingresa un número válido.")

def iniciar_grabacion(window_title):
    """Prepara y comienza la grabación con validación estricta"""
    objetivos_configurados = cargar_objetivos_configurados()
    
    # REGLA 1: Validar que sea objetivo configurado
    if not es_objetivo_valido(window_title, objetivos_configurados):
        print(f"ERROR: '{window_title}' no es un objetivo válido configurado.")
        return None
    
    # REGLA 2: Verificar que esté abierto
    ventanas_objetivo = encontrar_ventanas_objetivo(window_title)
    if not ventanas_objetivo:
        print(f"ERROR: '{window_title}' no está abierto o está minimizado.")
        print("Abre la aplicación y asegúrate de que no esté minimizada.")
        return None
    
    print(f"Ventanas encontradas y válidas: {len(ventanas_objetivo)}")
    target_pids = []
    
    for ventana in ventanas_objetivo:
        try:
            _, pid = win32process.GetWindowThreadProcessId(ventana._hWnd)
            target_pids.append(pid)
            print(f"  - Ventana '{ventana.title}' válida (PID: {pid})")
        except Exception as e:
            print(f"  - Error obteniendo PID: {e}")
    
    sct = mss.mss()
    monitor_bbox = {}
    width, height = 0, 0

    if isinstance(window_title, list) or window_title == "Ambas (Pantalla Completa)":
        print("  - Grabando en modo PANTALLA COMPLETA.")
        monitor_bbox = sct.monitors[1]
        width, height = monitor_bbox['width'], monitor_bbox['height']
    else:
        target_window = gw.getWindowsWithTitle(window_title)[0]
        if target_window.isMinimized:
            target_window.restore()
        target_window.activate()
        time.sleep(0.5)
        bbox = target_window.box
        monitor_bbox = {'top': bbox.top, 'left': bbox.left, 'width': bbox.width, 'height': bbox.height}
        width, height = bbox.width, bbox.height

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo_actual = os.path.join(CARPETA_GRABACIONES, f"grabacion_{timestamp}.mp4")
    fps_salida = FPS_CAPTURA * VELOCIDAD_REPRODUCCION
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(nombre_archivo_actual, fourcc, fps_salida, (width, height))

    return {
        "writer": video_writer,
        "sct": sct,
        "bbox": monitor_bbox,
        "target_pids": target_pids,
        "nombre_archivo": nombre_archivo_actual,
        "fps_captura": FPS_CAPTURA
    }

def grabar_frame(info):
    """Captura y escribe un solo frame en el video."""
    if not info or not info.get('writer'):
        return
    
    sct_img = info['sct'].grab(info['bbox'])
    frame = np.array(sct_img)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    info['writer'].write(frame)

def obtener_ventana_activa():
    """Obtiene el título de la ventana actualmente activa"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except:
        return ""

def obtener_pids_objetivo(objetivo):
    """Obtiene los PIDs de las ventanas objetivo"""
    pids = set()
    titles_to_find = objetivo if isinstance(objetivo, list) else [objetivo]
    
    try:
        all_windows = gw.getAllWindows()
        for title in titles_to_find:
            for window in all_windows:
                if window.title and title.lower() in window.title.lower():
                    if window and window.width > 0 and window.height > 0 and window.visible:
                        if not esta_ventana_minimizada(window):
                            try:
                                _, pid = win32process.GetWindowThreadProcessId(window._hWnd)
                                pids.add(pid)
                            except:
                                pass
    except:
        pass
    
    return pids

def es_ventana_objetivo_o_dependiente(titulo_ventana, objetivo):
    """Verifica si la ventana es objetivo o sus ventanas hijas/dependientes"""
    if not titulo_ventana:
        return False
    
    titulo_lower = titulo_ventana.lower()
    titles_to_check = objetivo if isinstance(objetivo, list) else [objetivo]
    
    # 1. Verificar ventana principal objetivo
    for title in titles_to_check:
        if title.lower() in titulo_lower:
            return True
    
    # 2. Verificar por PID del proceso (ventanas del mismo proceso)
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            _, pid_activo = win32process.GetWindowThreadProcessId(hwnd)
            pids_objetivo = obtener_pids_objetivo(objetivo)
            if pid_activo in pids_objetivo:
                return True
    except:
        pass
    
    # 3. Verificar ventanas dependientes por palabras clave
    dependientes = ['diálogo', 'dialog', 'configuración', 'config', 'opciones', 'options', 
                   'propiedades', 'properties', 'buscar', 'search', 'filtro', 'filter',
                   'abrir', 'open', 'guardar', 'save', 'imprimir', 'print', 'exportar', 'export',
                   'nuevo', 'new', 'editar', 'edit', 'modificar', 'modify', 'consulta', 'query',
                   'reporte', 'report', 'listado', 'list', 'seleccionar', 'select', 'mensaje', 'message']
    
    # Si la ventana activa contiene palabras clave Y alguna palabra del objetivo
    if any(keyword in titulo_lower for keyword in dependientes):
        for title in titles_to_check:
            palabras_objetivo = [p for p in title.lower().split() if len(p) > 3]  # Solo palabras significativas
            if any(palabra in titulo_lower for palabra in palabras_objetivo):
                return True
    
    return False

def validar_objetivo_disponible_y_activo(window_title, was_paused):
    """Valida si el objetivo está disponible Y es la ventana activa"""
    # 1. Verificar que existe la ventana objetivo
    ventanas = []
    titles_to_find = window_title if isinstance(window_title, list) else [window_title]
    
    for title in titles_to_find:
        all_windows = gw.getAllWindows()
        for window in all_windows:
            if window.title and title.lower() in window.title.lower():
                if window and window.width > 0 and window.height > 0 and window.visible:
                    if not esta_ventana_minimizada(window):
                        ventanas.append(window)
                        break
    
    # 2. Verificar que la ventana activa es objetivo o dependiente
    ventana_activa = obtener_ventana_activa()
    es_objetivo_activo = es_ventana_objetivo_o_dependiente(ventana_activa, window_title)
    
    # 3. Determinar estado
    if not ventanas or not es_objetivo_activo:
        if not was_paused:
            if not ventanas:
                print(f"❌ GRABACIÓN PAUSADA: '{window_title}' no está abierto")
            else:
                print(f"❌ GRABACIÓN PAUSADA: Cambió a otra aplicación")
        return True, True  # Pausado
    else:
        if was_paused:
            print(f"✅ GRABACIÓN REANUDADA: Volvió a '{window_title}'")
        return False, False  # Activo

def generar_nombre_base(seleccion):
    """Genera un nombre base para archivos"""
    if isinstance(seleccion, list):
        return "_y_".join(seleccion).lower().replace(" ", "_").replace(".", "")
    else:
        return seleccion.lower().replace(" ", "_").replace(".", "")

def obtener_carpeta_grabaciones():
    """Obtiene la carpeta de grabaciones desde config.json"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("ruta_grabaciones", CARPETA_GRABACIONES)
    except Exception as e:
        print(f"Error leyendo configuración: {e}")
    return CARPETA_GRABACIONES

def detener_grabacion(info):
    """Detiene la grabación y libera los recursos."""
    if info and info.get('writer'):
        info['writer'].release()
        print(f"Video guardado como: {info['nombre_archivo']}")
        return info['nombre_archivo']
    return None

def main():
    """Función principal que maneja la lógica de grabación."""
    window_title = seleccionar_aplicacion()
    if not window_title:
        return
    
    # Validar objetivos antes de continuar
    objetivos_configurados = cargar_objetivos_configurados()
    if not es_objetivo_valido(window_title, objetivos_configurados):
        print(f"ERROR: '{window_title}' no es un objetivo válido.")
        return
    
    print(f"\nListo para grabar '{window_title}'.")
    carpeta_grabaciones = obtener_carpeta_grabaciones()
    os.makedirs(carpeta_grabaciones, exist_ok=True)

    recording = False
    video_writer = None
    sct = None
    monitor_bbox = None
    target_window = None
    was_paused = False
    target_pids = []
    nombre_archivo_actual = ""
    frame_count = 0

    print("Presiona F9 para iniciar/detener la grabación.")
    print("Presiona Esc para salir.")

    while True:
        try:
            if keyboard.is_pressed('f9'):
                time.sleep(0.5)  # Evita dobles detecciones
                recording = not recording

                if recording:
                    # --- VALIDACIÓN ESTRICTA ANTES DE INICIAR ---
                    ventanas_objetivo = encontrar_ventanas_objetivo(window_title)
                    if not ventanas_objetivo:
                        print(f"ERROR: No se puede iniciar grabación. '{window_title}' no está abierto o está minimizado.")
                        recording = False
                        continue
                    
                    target_pids = []
                    for ventana in ventanas_objetivo:
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(ventana._hWnd)
                            target_pids.append(pid)
                            print(f"  - Ventana '{ventana.title}' válida (PID: {pid})")
                        except Exception as e:
                            print(f"  - Error obteniendo PID: {e}")
                    
                    was_paused = False
                    
                    # Iniciar el capturador de pantalla
                    sct = mss.mss()

                    if isinstance(window_title, list):
                        # Grabar pantalla completa si son varias apps
                        print("  - Grabando en modo PANTALLA COMPLETA.")
                        monitor_bbox = sct.monitors[1] # Monitor primario
                        width, height = monitor_bbox['width'], monitor_bbox['height']
                    else:
                        # Grabar solo la ventana si es una app
                        target_window = gw.getWindowsWithTitle(window_title)[0]
                        if target_window.isMinimized:
                            target_window.restore()
                        target_window.activate()
                        time.sleep(0.5) # Dar tiempo a que la ventana se active

                        # Obtener dimensiones y posición de la ventana
                        bbox = target_window.box
                        monitor_bbox = {'top': bbox.top, 'left': bbox.left, 'width': bbox.width, 'height': bbox.height}
                        width, height = bbox.width, bbox.height

                    # Configurar el codificador de video
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    nombre_archivo_actual = os.path.join(CARPETA_GRABACIONES, f"grabacion_{timestamp}.mp4")

                    fps_salida = FPS_CAPTURA * VELOCIDAD_REPRODUCCION
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec para .mp4
                    video_writer = cv2.VideoWriter(nombre_archivo_actual, fourcc, fps_salida, (width, height))

                    print(f"🔴 INICIANDO GRABACIÓN de '{window_title}'...")
                    sys.stdout.flush()

                else:
                    # --- Detener Grabación ---
                    if video_writer:
                        print("⏹️ DETENIENDO GRABACIÓN...")
                        sys.stdout.flush()
                        video_writer.release()
                        video_writer = None
                        sct = None
                        print(f"💾 Video guardado: {nombre_archivo_actual}")
                        sys.stdout.flush()

            if recording and sct and video_writer:
                # --- VALIDACIÓN CONTINUA DE OBJETIVOS Y VENTANA ACTIVA ---
                pausado, was_paused = validar_objetivo_disponible_y_activo(window_title, was_paused)
                
                if not pausado:
                    # Solo grabar si el objetivo está disponible
                    sct_img = sct.grab(monitor_bbox)
                    frame = np.array(sct_img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    video_writer.write(frame)
                    
                    # Indicador visual cada 5 segundos
                    frame_count += 1
                    if frame_count % (int(FPS_CAPTURA) * 5) == 0:
                        print(f"🔴 GRABANDO... ({frame_count // int(FPS_CAPTURA)}s)", flush=True)
                else:
                    # Pausado - esperar más tiempo para no consumir CPU
                    time.sleep(0.5)
                    continue

            if keyboard.is_pressed('esc'):
                if recording and video_writer:
                    print("⏹️ DETENIENDO GRABACIÓN por ESC...", flush=True)
                    video_writer.release()
                    print(f"💾 Video guardado: {nombre_archivo_actual}", flush=True)
                print("❌ GRABADOR FINALIZADO", flush=True)
                break

            # Ajustar el tiempo de espera para que coincida con los FPS de captura
            time.sleep(1 / FPS_CAPTURA)

        except Exception as e:
            print(f"Ocurrió un error: {e}")
            if video_writer:
                video_writer.release()
            recording = False
            time.sleep(1)

def main_con_objetivo_con_semaforo(objetivo_preseleccionado, callback_log=None):
    """Función principal con semáforo visual"""
    objetivos_configurados = cargar_objetivos_configurados()
    
    def log_mensaje(mensaje):
        print(mensaje)
        if callback_log:
            callback_log(mensaje)
    
    # Procesar objetivo preseleccionado
    if objetivo_preseleccionado == "Ambas Aplicaciones" and len(objetivos_configurados) >= 2:
        window_title = [objetivos_configurados[0], objetivos_configurados[1]]
    else:
        window_title = objetivo_preseleccionado
    
    # Validar objetivos
    if not es_objetivo_valido(window_title, objetivos_configurados):
        log_mensaje(f"ERROR: '{window_title}' no es un objetivo válido.")
        return
    
    # Crear y mostrar semáforo
    global semaforo_global
    semaforo_global = SemaforoGrabacion()
    semaforo_global.mostrar()
    
    log_mensaje(f"Grabador iniciado para: {window_title}")
    log_mensaje("F9 = Iniciar/Detener grabación | ESC = Salir")
    
    carpeta_grabaciones = obtener_carpeta_grabaciones()
    os.makedirs(carpeta_grabaciones, exist_ok=True)
    
    recording = False
    video_writer = None
    sct = None
    monitor_bbox = None
    was_paused = False
    nombre_archivo_actual = ""
    
    try:
        while True:
            if keyboard.is_pressed('f9'):
                time.sleep(0.5)
                recording = not recording
                
                if recording:
                    # Iniciar grabación
                    ventanas_objetivo = encontrar_ventanas_objetivo(window_title)
                    if not ventanas_objetivo:
                        log_mensaje(f"ERROR: '{window_title}' no está disponible")
                        recording = False
                        continue
                    
                    was_paused = False
                    sct = mss.mss()
                    
                    if isinstance(window_title, list):
                        monitor_bbox = sct.monitors[1]
                        width, height = monitor_bbox['width'], monitor_bbox['height']
                    else:
                        target_window = gw.getWindowsWithTitle(window_title)[0]
                        if target_window.isMinimized:
                            target_window.restore()
                        target_window.activate()
                        time.sleep(0.5)
                        bbox = target_window.box
                        monitor_bbox = {'top': bbox.top, 'left': bbox.left, 'width': bbox.width, 'height': bbox.height}
                        width, height = bbox.width, bbox.height
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    nombre_base = generar_nombre_base(window_title)
                    nombre_archivo_actual = os.path.join(carpeta_grabaciones, f"grabacion_{nombre_base}_{timestamp}.mp4")
                    
                    fps_salida = FPS_CAPTURA * VELOCIDAD_REPRODUCCION
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    video_writer = cv2.VideoWriter(nombre_archivo_actual, fourcc, fps_salida, (width, height))
                    
                    semaforo_global.iniciar_grabacion()
                    log_mensaje(f"🔴 GRABACIÓN INICIADA: {window_title}")
                else:
                    # Detener grabación (pero NO cerrar semáforo)
                    if video_writer:
                        video_writer.release()
                        video_writer = None
                        sct = None
                        semaforo_global.detener_grabacion()  # Solo cambia a LISTO
                        log_mensaje(f"⏹️ GRABACIÓN DETENIDA")
                        log_mensaje(f"💾 Video guardado: {os.path.basename(nombre_archivo_actual)}")
                        log_mensaje("Semáforo en modo LISTO - Usa ESC o X para cerrar")
                        # NO cerrar semáforo - solo detener grabación
            
            if recording and sct and video_writer:
                # Validación continua
                pausado, was_paused = validar_objetivo_disponible_y_activo_con_semaforo(window_title, was_paused, semaforo_global, log_mensaje)
                
                if not pausado:
                    sct_img = sct.grab(monitor_bbox)
                    frame = np.array(sct_img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    video_writer.write(frame)
                else:
                    time.sleep(0.5)
                    continue
            
            if keyboard.is_pressed('esc'):
                if recording and video_writer:
                    video_writer.release()
                    log_mensaje(f"💾 Video guardado: {os.path.basename(nombre_archivo_actual)}")
                break
            
            time.sleep(1 / FPS_CAPTURA)
            
    except Exception as e:
        log_mensaje(f"Error: {e}")
        if video_writer:
            video_writer.release()
    finally:
        if semaforo_global:
            semaforo_global.ocultar()
        log_mensaje("Grabador finalizado")

def validar_objetivo_disponible_y_activo_con_semaforo(window_title, was_paused, semaforo, log_callback):
    """Validación con control de semáforo"""
    ventanas = []
    titles_to_find = window_title if isinstance(window_title, list) else [window_title]
    
    for title in titles_to_find:
        all_windows = gw.getAllWindows()
        for window in all_windows:
            if window.title and title.lower() in window.title.lower():
                if window and window.width > 0 and window.height > 0 and window.visible:
                    if not esta_ventana_minimizada(window):
                        ventanas.append(window)
                        break
    
    ventana_activa = obtener_ventana_activa()
    es_objetivo_activo = es_ventana_objetivo_o_dependiente(ventana_activa, window_title)
    
    if not ventanas or not es_objetivo_activo:
        if not was_paused:
            semaforo.pausar_grabacion()
            if not ventanas:
                log_callback(f"⏸️ PAUSADO: '{window_title}' no disponible")
            else:
                log_callback(f"⏸️ PAUSADO: Cambió a otra aplicación")
        return True, True
    else:
        if was_paused:
            semaforo.reanudar_grabacion()
            log_callback(f"▶️ REANUDADO: Volvió a '{window_title}'")
        return False, False

def main_con_objetivo(objetivo_preseleccionado):
    """Función principal con objetivo preseleccionado desde la interfaz"""
    objetivos_configurados = cargar_objetivos_configurados()
    
    # Procesar objetivo preseleccionado (SIN MENÚ)
    if objetivo_preseleccionado == "Ambas Aplicaciones" and len(objetivos_configurados) >= 2:
        window_title = [objetivos_configurados[0], objetivos_configurados[1]]
    else:
        window_title = objetivo_preseleccionado
    
    # Validar objetivos antes de continuar
    if not es_objetivo_valido(window_title, objetivos_configurados):
        print(f"ERROR: '{window_title}' no es un objetivo válido.")
        return
    
    print(f"\n=== GRABADOR INICIADO ===")
    print(f"Objetivo: {window_title}")
    print("F9 = Iniciar/Detener | ESC = Salir")
    print("=============================")
    sys.stdout.flush()
    carpeta_grabaciones = obtener_carpeta_grabaciones()
    os.makedirs(carpeta_grabaciones, exist_ok=True)
    
    recording = False
    video_writer = None
    sct = None
    monitor_bbox = None
    was_paused = False
    nombre_archivo_actual = ""
    frame_count = 0
    
    while True:
        try:
            if keyboard.is_pressed('f9'):
                time.sleep(0.5)  # Evita dobles detecciones
                recording = not recording
                
                if recording:
                    # VALIDACIÓN ESTRICTA ANTES DE INICIAR
                    ventanas_objetivo = encontrar_ventanas_objetivo(window_title)
                    if not ventanas_objetivo:
                        print(f"ERROR: No se puede iniciar grabación. '{window_title}' no está abierto o está minimizado.")
                        recording = False
                        continue
                    
                    was_paused = False
                    sct = mss.mss()
                    
                    if isinstance(window_title, list):
                        print("  - Grabando en modo PANTALLA COMPLETA.")
                        monitor_bbox = sct.monitors[1]
                        width, height = monitor_bbox['width'], monitor_bbox['height']
                    else:
                        target_window = gw.getWindowsWithTitle(window_title)[0]
                        if target_window.isMinimized:
                            target_window.restore()
                        target_window.activate()
                        time.sleep(0.5)
                        bbox = target_window.box
                        monitor_bbox = {'top': bbox.top, 'left': bbox.left, 'width': bbox.width, 'height': bbox.height}
                        width, height = bbox.width, bbox.height
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    nombre_base = generar_nombre_base(window_title)
                    carpeta_grabaciones = obtener_carpeta_grabaciones()
                    nombre_archivo_actual = os.path.join(carpeta_grabaciones, f"grabacion_{nombre_base}_{timestamp}.mp4")
                    
                    fps_salida = FPS_CAPTURA * VELOCIDAD_REPRODUCCION
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    video_writer = cv2.VideoWriter(nombre_archivo_actual, fourcc, fps_salida, (width, height))
                    
                    print(f"🔴 INICIANDO GRABACIÓN de '{window_title}'...")
                    sys.stdout.flush()
                else:
                    if video_writer:
                        print("⏹️ DETENIENDO GRABACIÓN...")
                        sys.stdout.flush()
                        video_writer.release()
                        video_writer = None
                        sct = None
                        print(f"💾 Video guardado: {nombre_archivo_actual}")
                        sys.stdout.flush()
            
            if recording and sct and video_writer:
                # VALIDACIÓN CONTINUA DE OBJETIVOS Y VENTANA ACTIVA
                pausado, was_paused = validar_objetivo_disponible_y_activo(window_title, was_paused)
                
                if not pausado:
                    sct_img = sct.grab(monitor_bbox)
                    frame = np.array(sct_img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    video_writer.write(frame)
                    
                    # Indicador visual cada 5 segundos
                    frame_count += 1
                    if frame_count % (int(FPS_CAPTURA) * 5) == 0:
                        print(f"🔴 GRABANDO... ({frame_count // int(FPS_CAPTURA)}s)")
                        sys.stdout.flush()
                else:
                    time.sleep(0.5)
                    continue
            
            if keyboard.is_pressed('esc'):
                if recording and video_writer:
                    print("⏹️ DETENIENDO GRABACIÓN por ESC...", flush=True)
                    video_writer.release()
                    print(f"💾 Video guardado: {nombre_archivo_actual}", flush=True)
                print("❌ GRABADOR FINALIZADO", flush=True)
                break
            
            time.sleep(1 / FPS_CAPTURA)
            
        except Exception as e:
            print(f"Ocurrió un error: {e}")
            if video_writer:
                video_writer.release()
            recording = False
            time.sleep(1)

if __name__ == "__main__":
    main()