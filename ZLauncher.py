import tkinter as tk
from pantalla_inicio_sys import PantallaInicio
from ventana_credenciales import credenciales
from Usuario_administrador.usu_admin_main import usuAdminMain
from Usuario_basico.usu_basico_main import usuBasicoMain

#llamado a los styles
from ttkbootstrap import Style
from styles import configurar_estilos

class controladorVentanas:
    def __init__(self, root):
        self.root = root
        style = Style(theme="litera")
        configurar_estilos(style)
        self.ventana_actual = None
        self.mostrar_pantalla_inicio()        

    def limpiar_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def mostrar_pantalla_inicio(self):
        self.limpiar_root()
        PantallaInicio(self.root, self)
# 
    def mostrar_credenciales(self):
        self.limpiar_root()
        credenciales(self.root, self)

    def mostrar_admin(self):
        self.limpiar_root()
        usuAdminMain.iniciar_ventana(self.root, self)

    def mostrar_basico(self):
        self.limpiar_root()
        usuBasicoMain(self.root, self)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("ese")
    root.geometry("600x400")
    controlador = controladorVentanas(root)
    root.mainloop()