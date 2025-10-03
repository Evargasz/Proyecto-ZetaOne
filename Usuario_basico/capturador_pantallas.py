import pyautogui
import keyboard
import time
import os
import json
from docx import Document
from docx.shared import Inches
from pywinauto import Desktop, uia_defines
from PIL import Image, ImageDraw
import math
from io import BytesIO
import win32clipboard

# Configuración de aplicaciones desde config.json
def cargar_objetivos_configurados():
    """Carga los objetivos desde config.json"""
    try:
        config_file = "json\\config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("objetivos", [])
    except Exception as e:
        print(f"Error cargando configuración: {e}")
    return ["Sistema de Cartera", "C O B I S  Clientes", "C.O.B.I.S TERMINAL ADMINISTRATIVA"]

# Generar APLICACIONES_CONOCIDAS dinámicamente
objetivos = cargar_objetivos_configurados()
APLICACIONES_CONOCIDAS = {}
for i, objetivo in enumerate(objetivos, 1):
    APLICACIONES_CONOCIDAS[str(i)] = objetivo

if len(objetivos) >= 2:
    APLICACIONES_CONOCIDAS[str(len(objetivos) + 1)] = f"{objetivos[0]} y {objetivos[1]}"

APLICACIONES_CONOCIDAS[str(len(APLICACIONES_CONOCIDAS) + 1)] = "Todas (Pantalla Completa)"

def seleccionar_aplicacion():
    """Muestra un menú para que el usuario elija qué aplicación capturar."""
    print("Selecciona la aplicación de la que deseas tomar capturas:")
    for key, value in APLICACIONES_CONOCIDAS.items():
        print(f"  {key}) {value}")
    print("  *) O escribe el título exacto de otra ventana")

    while True:
        choice = input("> ").strip()
        if choice in APLICACIONES_CONOCIDAS:
            valor = APLICACIONES_CONOCIDAS[choice]
            # Si contiene " y ", es una opción combinada
            if " y " in valor and valor != "Todas (Pantalla Completa)":
                objetivos = cargar_objetivos_configurados()
                if len(objetivos) >= 2:
                    return [objetivos[0], objetivos[1]]
            return valor
        if choice:
            return choice
        print("Selección inválida. Por favor, elige un número o escribe un título.")

def encontrar_ventana(window_title):
    """Encuentra ventana usando win32gui (sin pywinauto)"""
    import win32gui
    
    def callback(hwnd, ventanas):
        if win32gui.IsWindowVisible(hwnd):
            texto = win32gui.GetWindowText(hwnd)
            if window_title.lower() in texto.lower() and texto.strip():
                ventanas.append(hwnd)
        return True
    
    ventanas = []
    try:
        win32gui.EnumWindows(callback, ventanas)
        if ventanas:
            hwnd = ventanas[0]
            # Crear objeto simulado compatible
            class VentanaSimulada:
                def __init__(self, hwnd):
                    self.hwnd = hwnd
                
                def exists(self):
                    return win32gui.IsWindow(self.hwnd)
                
                def is_minimized(self):
                    return win32gui.IsIconic(self.hwnd)
                
                def restore(self):
                    win32gui.ShowWindow(self.hwnd, 9)  # SW_RESTORE
                
                def set_focus(self):
                    win32gui.SetForegroundWindow(self.hwnd)
                
                def rectangle(self):
                    rect = win32gui.GetWindowRect(self.hwnd)
                    class Rect:
                        def __init__(self, rect):
                            self.left = rect[0]
                            self.top = rect[1]
                            self.right = rect[2]
                            self.bottom = rect[3]
                        
                        def width(self):
                            return self.right - self.left
                        
                        def height(self):
                            return self.bottom - self.top
                    
                    return Rect(rect)
            
            return VentanaSimulada(hwnd)
    except:
        pass
    
    return None

def agregar_a_word(doc, img_path, nombre_word, primera=False):
    if not primera:
        doc.add_paragraph("\n\n")
    doc.add_picture(img_path, width=Inches(6))
    doc.save(nombre_word)

def detectar_elemento_bajo_cursor():
    """Detecta el elemento UI más preciso bajo el cursor del mouse"""
    try:
        import win32gui
        import win32api
        
        # Obtener posición actual del cursor
        cursor_x, cursor_y = win32api.GetCursorPos()
        
        # Método 1: Usar WindowFromPoint para obtener el control exacto
        hwnd = win32gui.WindowFromPoint((cursor_x, cursor_y))
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            # Verificar si es un control pequeño (campo de texto, botón, etc.)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            # Si es un control de tamaño razonable, usarlo
            if 10 < width < 800 and 10 < height < 200:
                return {
                    'left': rect[0],
                    'top': rect[1], 
                    'right': rect[2],
                    'bottom': rect[3],
                    'method': 'WindowFromPoint'
                }
            
        return None
        
    except Exception as e:
        print(f"Error detectando elemento: {e}")
        return None

def capturar_y_guardar(seleccion, carpeta_capturas, contador):
    """
    Lógica centralizada para tomar una captura de pantalla con marcación precisa.
    Devuelve (nombre_archivo, screenshot_object) o None si falla.
    """
    try:
        screenshot = None
        rect_offset_x, rect_offset_y = 0, 0

        if isinstance(seleccion, list):
            ventanas_encontradas = [encontrar_ventana(titulo) for titulo in seleccion]
            ventanas_validas = [v for v in ventanas_encontradas if v and v.exists()]
            if not ventanas_validas:
                ventanas_str = " y ".join(seleccion)
                print(f"❌ No encuentra la ventana o pantalla '{ventanas_str}' parametrizada abierta!")
                return None
            min_left = min(v.rectangle().left for v in ventanas_validas)
            min_top = min(v.rectangle().top for v in ventanas_validas)
            max_right = max(v.rectangle().right for v in ventanas_validas)
            max_bottom = max(v.rectangle().bottom for v in ventanas_validas)
            region_captura = (min_left, min_top, max_right - min_left, max_bottom - min_top)
            screenshot = pyautogui.screenshot(region=region_captura)
            rect_offset_x, rect_offset_y = min_left, min_top
        elif seleccion == "Todas (Pantalla Completa)":
            screenshot = pyautogui.screenshot()
        else:
            ventana = encontrar_ventana(seleccion)
            if not (ventana and ventana.exists()):
                print(f"❌ No encuentra la ventana o pantalla '{seleccion}' parametrizada abierta!")
                return None
            if ventana.is_minimized():
                ventana.restore()
            ventana.set_focus()
            time.sleep(0.2)
            window_rect = ventana.rectangle()
            if window_rect.width() <= 0 or window_rect.height() <= 0:
                print(f"La ventana '{seleccion}' no tiene un tamaño visible.")
                return None
            screenshot = pyautogui.screenshot(region=(window_rect.left, window_rect.top, window_rect.width(), window_rect.height()))
            rect_offset_x, rect_offset_y = window_rect.left, window_rect.top

        # MARCACIÓN MEJORADA: Detectar elemento bajo cursor
        elemento_detectado = detectar_elemento_bajo_cursor()
        if elemento_detectado:
            # Convertir coordenadas absolutas a relativas de la captura
            relative_left = max(0, elemento_detectado['left'] - rect_offset_x)
            relative_top = max(0, elemento_detectado['top'] - rect_offset_y)
            relative_right = min(screenshot.width, elemento_detectado['right'] - rect_offset_x)
            relative_bottom = min(screenshot.height, elemento_detectado['bottom'] - rect_offset_y)
            
            # Dibujar contorno amarillo más visible
            draw = ImageDraw.Draw(screenshot)
            
            # Contorno principal amarillo grueso
            draw.rectangle(
                [relative_left, relative_top, relative_right, relative_bottom], 
                outline="yellow", 
                width=4
            )
            
            # Contorno interior negro fino para contraste
            draw.rectangle(
                [relative_left+1, relative_top+1, relative_right-1, relative_bottom-1], 
                outline="black", 
                width=1
            )
            
            print(f"✓ Elemento detectado ({elemento_detectado['method']}): {elemento_detectado['right']-elemento_detectado['left']}x{elemento_detectado['bottom']-elemento_detectado['top']}")
        else:
            # Fallback: marcar posición del cursor
            cursor_x, cursor_y = pyautogui.position()
            relative_x = cursor_x - rect_offset_x
            relative_y = cursor_y - rect_offset_y
            
            if 0 <= relative_x < screenshot.width and 0 <= relative_y < screenshot.height:
                draw = ImageDraw.Draw(screenshot)
                # flecha amarilla en la posición del cursor
                flecha(draw, cursor_x, cursor_y, offset=30, largo=60)
                print("✓ Marcador de cursor aplicado")

        nombre_archivo = os.path.join(carpeta_capturas, f"captura_{contador:03d}.png")
        screenshot.save(nombre_archivo)
        os.startfile(nombre_archivo)
        copy_clipboard(screenshot)
        return nombre_archivo, screenshot
    except Exception as e:
        print(f"Error durante la captura: {e}")
        return None
    
def flecha(draw, cursor_x, cursor_y, offset=0, largo=60, color="yellow"):
    """Dibuja una flecha cuyo extremo apunta justo donde está el cursor."""


    #define el ángulo de entrada de la flecha 
    angulo = math.radians(45)  

    #calcula el vector de direccion (no se :P)
    dx = math.cos(angulo)
    dy = math.sin(angulo)

    #punto donde empieza la flecha
    start_x = cursor_x + (offset + largo) * dx
    start_y = cursor_y + (offset + largo) * dy
    base_x = cursor_x + offset * dx 
    base_y = cursor_y + offset * dy

    flecha_angle = math.atan2(cursor_y - base_y, cursor_x - base_x)
    # Dibuja el cuerpo de la flecha (recta principal hacia el cursor)
    draw.line([(start_x, start_y), (base_x, base_y)], fill=color, width=3)

    #dibuja la cabeza de la flecha 
    head_len = 15  # longitud de la cabeza de la flecha
    for head_angle in [-math.radians(30), math.radians(30)]:
        theta = flecha_angle + head_angle
        x2 = base_x - head_len * math.cos(theta)
        y2 = base_y - head_len * math.sin(theta)
        draw.line([(base_x, base_y), (x2, y2)], fill=color, width=3)
    
def copy_clipboard(img):
    output = BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def main():
    if not APLICACIONES_CONOCIDAS:
        print("ERROR: No hay objetivos configurados en config.json")
        return
    
    seleccion = seleccionar_aplicacion()
    if not seleccion:
        return
    
    # Usamos 'isinstance' para manejar tanto una cadena de texto como una lista de ellas
    window_title = " y ".join(seleccion) if isinstance(seleccion, list) else seleccion
    print(f"\nListo para capturar '{window_title}'.")

    # Nombres dinámicos basados en la aplicación seleccionada
    nombre_base = window_title.lower().replace(" ", "_").replace(".", "")
    carpeta_capturas = f"C:\\ZetaOne\\Capturas\\capturas_{nombre_base}"
    nombre_word = f"C:\\ZetaOne\\Capturas\\pantallazos_{nombre_base}.docx"

    os.makedirs(carpeta_capturas, exist_ok=True)
    print("Presiona F8 para capturar la ventana. Presiona ESC para salir.")

    # Abre el documento de Word existente o crea uno nuevo
    if os.path.exists(nombre_word):
        doc = Document(nombre_word)
        primera_captura = False
    else:
        doc = Document()
        primera_captura = True

    contador = 1
    while True:
        if keyboard.is_pressed('f8'):
            resultado = capturar_y_guardar(seleccion, carpeta_capturas, contador)
            if resultado:
                nombre_archivo, _ = resultado
                print(f"¡Captura {contador} guardada en {nombre_archivo}!")
                agregar_a_word(doc, nombre_archivo, nombre_word, primera=primera_captura)
                primera_captura = False
                contador += 1

            time.sleep(0.8)
        if keyboard.is_pressed('esc'):
            print("¡Capturador finalizado!")
            break

def main_con_objetivo(objetivo_preseleccionado):
    """Función principal con objetivo preseleccionado desde la interfaz"""
    # Usar directamente el objetivo preseleccionado (SIN MENÚ)
    seleccion = objetivo_preseleccionado
    
    # Manejar opciones especiales
    if " y " in seleccion and seleccion != "Todas (Pantalla Completa)":
        objetivos = cargar_objetivos_configurados()
        if len(objetivos) >= 2:
            seleccion = [objetivos[0], objetivos[1]]
    
    window_title = " y ".join(seleccion) if isinstance(seleccion, list) else seleccion
    print(f"\n=== CAPTURADOR INICIADO ===")
    print(f"Objetivo: {window_title}")
    print("F8 = Capturar | ESC = Salir")
    print("==============================")
    
    # Nombres dinámicos basados en la aplicación seleccionada
    nombre_base = window_title.lower().replace(" ", "_").replace(".", "")
    carpeta_capturas = f"C:\\ZetaOne\\Capturas\\capturas_{nombre_base}"
    nombre_word = f"C:\\ZetaOne\\Capturas\\pantallazos_{nombre_base}.docx"
    
    os.makedirs(carpeta_capturas, exist_ok=True)
    
    # Abre el documento de Word existente o crea uno nuevo
    if os.path.exists(nombre_word):
        doc = Document(nombre_word)
        primera_captura = False
    else:
        doc = Document()
        primera_captura = True
    
    contador = 1
    while True:
        if keyboard.is_pressed('f8'):
            resultado = capturar_y_guardar(seleccion, carpeta_capturas, contador)
            if resultado:
                nombre_archivo, _ = resultado
                print(f"✓ Captura {contador} guardada: {os.path.basename(nombre_archivo)}")
                agregar_a_word(doc, nombre_archivo, nombre_word, primera=primera_captura)
                primera_captura = False
                contador += 1
            
            time.sleep(0.8)
        if keyboard.is_pressed('esc'):
            print("\n¡Capturador finalizado!")
            break

if __name__ == "__main__":
    main()