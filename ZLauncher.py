import tkinter as tk
from pantalla_inicio_sys import PantallaInicio
from ventana_credenciales import credenciales
from Usuario_administrador.usu_admin_main import usuAdminMain
from Usuario_basico.usu_basico_main import usuBasicoMain

#llamado a los styles
from ttkbootstrap import Style
from styles import configurar_estilos

# --- Versión de la Aplicación ---
__version__ = "1.4.0" # Ejemplo: Major.Minor.Patch

class controladorVentanas:
    def __init__(self, root):
        self.root = root
        self.style = Style(theme="litera")
        configurar_estilos(self.style)
        self.usuario_logueado = None # --- CAMBIO: Añadir variable para el usuario ---
        self.mostrar_pantalla_inicio()        

    def limpiar_root(self):
        """Destruye todos los widgets y resetea la configuración de geometría."""
        for widget in self.root.winfo_children():
            # Desvincula el widget de su gestor de geometría antes de destruirlo
            widget.pack_forget()
            widget.grid_forget()
            widget.place_forget()
            widget.destroy()

    def _configurar_y_centrar_ventana(self, ancho, alto, redimensionable=False):
        """Función de utilidad para configurar y centrar la ventana raíz."""
        # Resetear completamente las configuraciones de ventana
        self.root.withdraw()
        
        # Resetear minsize y maxsize
        self.root.minsize(1, 1)
        self.root.maxsize(self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        
        # Configurar estado y redimensionamiento
        self.root.state('normal')
        self.root.resizable(redimensionable, redimensionable)
        
        # Calcular posición para centrar (ajustado para evitar barra de tareas)
        x = (self.root.winfo_screenwidth() // 2) - (ancho // 2) # --- CORRECCIÓN: Se elimina el offset vertical ---
        y = (self.root.winfo_screenheight() // 2) - (alto // 2)
        
        geometria = f"{ancho}x{alto}+{x}+{y}"
        
        # Aplicar geometría múltiples veces
        self.root.geometry(geometria)
        self.root.update_idletasks()
        self.root.geometry(geometria)
        self.root.update()
        
        # Mostrar la ventana
        self.root.deiconify()
        
        # Aplicar una vez más después de mostrar
        self.root.after(10, lambda: self.root.geometry(geometria))

    def mostrar_pantalla_inicio(self):
        self.limpiar_root()
        self._configurar_y_centrar_ventana(400, 350, redimensionable=False)
        PantallaInicio(self.root, self)
        
    def mostrar_credenciales(self):
        self.limpiar_root()
        self._configurar_y_centrar_ventana(250, 250, redimensionable=False)
        credenciales(self.root, self)

    def mostrar_admin(self):
        self.limpiar_root()
        self._configurar_y_centrar_ventana(1300, 680, redimensionable=True)
        usuAdminMain.iniciar_ventana(self.root, self)

    def mostrar_basico(self):
        self.limpiar_root()
        self._configurar_y_centrar_ventana(900, 650, redimensionable=True)
        usuBasicoMain(self.root, self)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("ZetaOne")
    controlador = controladorVentanas(root)
    root.mainloop()