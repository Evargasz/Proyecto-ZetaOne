import cv2
import numpy as np
import mss
import pygetwindow as gw
import keyboard
import os
import time
from datetime import datetime
import win32process

# --- Configuración ---
CARPETA_GRABACIONES = "grabaciones"
FPS_CAPTURA = 20.0  # Fotogramas por segundo a capturar
VELOCIDAD_REPRODUCCION = 2.0 # 1.0 es normal, 2.0 es doble velocidad, etc.

# Configuración de aplicaciones conocidas
APLICACIONES_CONOCIDAS = {
    "1": "Sistema de Cartera",
    "2": "C O B I S  Clientes", 
    "3": "Ambas (Pantalla Completa)"
}

def seleccionar_aplicacion():
    """
    Muestra un menú para que el usuario elija qué aplicación grabar.
    """
    print("Selecciona la aplicación que deseas grabar:")
    for key, value in APLICACIONES_CONOCIDAS.items():
        print(f"  {key}) {value}")
    print("  *) O escribe el título exacto de otra ventana")

    while True:
        choice = input("> ").strip()
        if choice in APLICACIONES_CONOCIDAS:
            # Si se elige "Ambas", devolvemos una lista con los títulos
            if choice == "3":
                return [APLICACIONES_CONOCIDAS["1"], APLICACIONES_CONOCIDAS["2"]]
            else:
                return APLICACIONES_CONOCIDAS[choice]
        if choice:
            return choice
        print("Selección inválida. Por favor, elige un número o escribe un título.")

def iniciar_grabacion(window_title):
    """
    Prepara y comienza la grabación. Devuelve un diccionario con la información
    necesaria para los siguientes frames o None si falla.
    """
    print("Buscando ventana...")
    target_pids = []
    titles_to_find = window_title if isinstance(window_title, list) else [window_title]
    
    for title in titles_to_find:
        windows = gw.getWindowsWithTitle(title)
        if windows:
            try:
                _, pid = win32process.GetWindowThreadProcessId(windows[0]._hWnd)
                target_pids.append(pid)
                print(f"  - Ventana '{title}' encontrada (PID: {pid}).")
            except Exception as e:
                print(f"  - Error al obtener PID para '{title}': {e}")
        else:
            print(f"  - Advertencia: No se encontró la ventana '{title}'.")

    if not target_pids:
        print("Error: No se encontró ninguna de las ventanas de destino.")
        return None
    
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

def pausar_por_foco(target_pids, was_paused):
    """Comprueba si la ventana activa es una de las de destino."""
    active_window = gw.getActiveWindow()
    active_pid = None
    if active_window:
        try:
            _, active_pid = win32process.GetWindowThreadProcessId(active_window._hWnd)
        except Exception:
            active_pid = None
    
    if active_pid in target_pids:
        if was_paused:
            print("...Reanudando grabación.")
        return False, False # No pausado, no era pausado
    else:
        if not was_paused:
            print(f"Ninguna ventana de destino está activa. Pausando grabación...")
        return True, True # Pausado, ahora está pausado

def detener_grabacion(info):
    """Detiene la grabación y libera los recursos."""
    if info and info.get('writer'):
        info['writer'].release()
        print(f"Video guardado como: {info['nombre_archivo']}")
        return info['nombre_archivo']
    return None

def main():
    """
    Función principal que maneja la lógica de grabación.
    """
    window_title = seleccionar_aplicacion()
    print(f"\nListo para grabar '{window_title}'.")
    os.makedirs(CARPETA_GRABACIONES, exist_ok=True)

    recording = False
    video_writer = None
    sct = None
    monitor_bbox = None
    target_window = None
    was_paused = False
    target_pids = []
    nombre_archivo_actual = ""

    print("Presiona F9 para iniciar/detener la grabación.")
    print("Presiona Esc para salir.")

    while True:
        try:
            if keyboard.is_pressed('f9'):
                time.sleep(0.5)  # Evita dobles detecciones
                recording = not recording

                if recording:
                    # --- Iniciar Grabación ---
                    print("Buscando ventana...")
                    target_pids = []
                    
                    # Lógica para una o varias ventanas
                    titles_to_find = window_title if isinstance(window_title, list) else [window_title]
                    
                    for title in titles_to_find:
                        windows = gw.getWindowsWithTitle(title)
                        if windows:
                            try:
                                _, pid = win32process.GetWindowThreadProcessId(windows[0]._hWnd)
                                target_pids.append(pid)
                                print(f"  - Ventana '{title}' encontrada (PID: {pid}).")
                            except Exception as e:
                                print(f"  - Error al obtener PID para '{title}': {e}")
                        else:
                            print(f"  - Advertencia: No se encontró la ventana '{title}'.")

                    if not target_pids:
                        print("Error: No se encontró ninguna de las ventanas de destino. Abortando grabación.")
                        recording = False
                        continue
                    
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

                    print(f"Grabando... Presiona F9 de nuevo para detener.")

                else:
                    # --- Detener Grabación ---
                    if video_writer:
                        print("Deteniendo grabación...")
                        video_writer.release()
                        video_writer = None
                        sct = None
                        print(f"Video guardado como: {nombre_archivo_actual}")

            if recording and sct and video_writer:
                # --- Lógica de Pausa/Reanudación Automática ---
                # Comprueba si la ventana activa pertenece a alguno de los procesos de destino.
                active_window = gw.getActiveWindow()
                active_pid = None
                if active_window:
                    try:
                        _, active_pid = win32process.GetWindowThreadProcessId(active_window._hWnd)
                    except Exception:
                        active_pid = None # La ventana puede cerrarse justo en este momento
                if active_pid in target_pids:
                    if was_paused:
                        print("...Reanudando grabación.")
                        was_paused = False

                    # Capturar el frame solo si la ventana está activa
                    sct_img = sct.grab(monitor_bbox)

                    # Convertir la imagen a un formato que OpenCV pueda usar (numpy array)
                    frame = np.array(sct_img)

                    # Convertir de BGRA (formato de mss) a BGR (formato de OpenCV)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    # Escribir el frame en el archivo de video
                    video_writer.write(frame)
                else:
                    if not was_paused:
                        print(f"Ninguna ventana de destino está activa. Pausando grabación...")
                        was_paused = True
                    time.sleep(0.5) # Esperar un poco más si está pausado para no consumir CPU
                    continue # Saltar el resto del bucle para no grabar

            if keyboard.is_pressed('esc'):
                if recording and video_writer:
                    video_writer.release()
                print("¡Programa finalizado!")
                break

            # Ajustar el tiempo de espera para que coincida con los FPS de captura
            time.sleep(1 / FPS_CAPTURA)

        except Exception as e:
            print(f"Ocurrió un error: {e}")
            if video_writer:
                video_writer.release()
            recording = False
            time.sleep(1)

if __name__ == "__main__":
    main()