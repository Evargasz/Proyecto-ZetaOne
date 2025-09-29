"""
Utilidades para manejo de ventanas en ZetaOne
"""

def centrar_ventana(ventana, ancho=None, alto=None, offset_y=-20):
    """
    Centra una ventana en la pantalla
    
    Args:
        ventana: La ventana de tkinter a centrar
        ancho: Ancho deseado (opcional, usa el actual si no se especifica)
        alto: Alto deseado (opcional, usa el actual si no se especifica)
        offset_y: Desplazamiento vertical (negativo sube la ventana)
    """
    ventana.update_idletasks()
    
    # Usar dimensiones actuales si no se especifican
    if ancho is None:
        ancho = ventana.winfo_width()
    if alto is None:
        alto = ventana.winfo_height()
    
    # Calcular posición centrada
    x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto // 2) + offset_y
    
    # Aplicar geometría
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

def centrar_ventana_sobre_padre(ventana_hija, ventana_padre, offset_y=0):
    """
    Centra una ventana sobre otra ventana padre
    
    Args:
        ventana_hija: La ventana a centrar
        ventana_padre: La ventana padre sobre la cual centrar
        offset_y: Desplazamiento vertical
    """
    ventana_hija.update_idletasks()
    ventana_padre.update_idletasks()
    
    # Obtener dimensiones y posición del padre
    padre_x = ventana_padre.winfo_x()
    padre_y = ventana_padre.winfo_y()
    padre_ancho = ventana_padre.winfo_width()
    padre_alto = ventana_padre.winfo_height()
    
    # Obtener dimensiones de la ventana hija
    hija_ancho = ventana_hija.winfo_width()
    hija_alto = ventana_hija.winfo_height()
    
    # Calcular posición centrada sobre el padre
    x = padre_x + (padre_ancho // 2) - (hija_ancho // 2)
    y = padre_y + (padre_alto // 2) - (hija_alto // 2) + offset_y
    
    # Aplicar geometría
    ventana_hija.geometry(f"{hija_ancho}x{hija_alto}+{x}+{y}")