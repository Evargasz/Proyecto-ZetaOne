import pyautogui
import keyboard
import time
import os
from docx import Document
from docx.shared import Inches
from pywinauto import Desktop, uia_defines
from PIL import Image, ImageDraw

def seleccionar_aplicacion():
    """Muestra un menú para que el usuario elija qué aplicación capturar."""
    print("Selecciona la aplicación de la que deseas tomar capturas:")
    for key, value in APLICACIONES_CONOCIDAS.items():
        print(f"  {key}) {value}")
    print("  *) O escribe el título exacto de otra ventana")

    while True:
        choice = input("> ").strip()
        if choice in APLICACIONES_CONOCIDAS:
            # Si se elige la opción combinada, devolvemos una lista con los títulos
            if choice == "4":
                return [APLICACIONES_CONOCIDAS["1"], APLICACIONES_CONOCIDAS["2"]]
            return APLICACIONES_CONOCIDAS[choice]
        if choice:
            return choice
        print("Selección inválida. Por favor, elige un número o escribe un título.")

def encontrar_ventana(window_title):
    """Encuentra y conecta con la ventana de la aplicación Cartera usando pywinauto."""
    try:
        return Desktop(backend="uia").window(title_re=f".*{window_title}.*")
    except Exception:
        return None

def agregar_a_word(doc, img_path, nombre_word, primera=False):
    if not primera:
        doc.add_paragraph("\n\n")
    doc.add_picture(img_path, width=Inches(6))
    doc.save(nombre_word)

def capturar_y_guardar(seleccion, carpeta_capturas, contador):
    """
    Lógica centralizada para tomar una captura de pantalla.
    Devuelve (nombre_archivo, screenshot_object) o None si falla.
    """
    try:
        screenshot = None
        rect_offset_x, rect_offset_y = 0, 0

        if isinstance(seleccion, list):
            ventanas_encontradas = [encontrar_ventana(titulo) for titulo in seleccion]
            ventanas_validas = [v for v in ventanas_encontradas if v and v.exists()]
            if not ventanas_validas:
                print(f"No se encontró ninguna de las ventanas: {seleccion}. ¿Están abiertas?")
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
                print(f"No se encontró la ventana '{seleccion}'. ¿Está abierta?")
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

        focused_element = uia_defines.IUIA().get_focused_element()
        if focused_element:
            control_rect = focused_element.CurrentBoundingRectangle
            relative_rect = (
                control_rect.left - rect_offset_x, control_rect.top - rect_offset_y,
                control_rect.right - rect_offset_x, control_rect.bottom - rect_offset_y
            )
            ImageDraw.Draw(screenshot).rectangle(relative_rect, outline="yellow", width=3)

        nombre_archivo = os.path.join(carpeta_capturas, f"captura_{contador:03d}.png")
        screenshot.save(nombre_archivo)
        os.startfile(nombre_archivo)
        return nombre_archivo, screenshot
    except Exception as e:
        print(f"Error durante la captura: {e}")
        return None

def main():
    seleccion = seleccionar_aplicacion()
    # Usamos 'isinstance' para manejar tanto una cadena de texto como una lista de ellas
    window_title = " y ".join(seleccion) if isinstance(seleccion, list) else seleccion
    print(f"\nListo para capturar '{window_title}'.")

    # Nombres dinámicos basados en la aplicación seleccionada
    nombre_base = window_title.lower().replace(" ", "_").replace(".", "")
    carpeta_capturas = f"capturas_{nombre_base}"
    nombre_word = f"pantallazos_{nombre_base}.docx"

    os.makedirs(carpeta_capturas, exist_ok=True)
    print("Presiona F8 para capturar la ventana. Presiona Esc para salir.")

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
            print("¡Programa finalizado!")
            break

if __name__ == "__main__":
    main()