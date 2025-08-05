import tkinter as tk
from tkinter import ttk, messagebox

class CatalogacionDialog(tk.Toplevel):
    def __init__(self, parent, aceptar_callback=None):
        super().__init__(parent)
        self.title("Catalogar Archivo")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.aceptar_callback = aceptar_callback

        ttk.Label(self, text="Nombre del archivo:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.entry_nombre = ttk.Entry(self, width=30)
        self.entry_nombre.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self, text="Descripción:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        self.entry_descripcion = ttk.Entry(self, width=30)
        self.entry_descripcion.grid(row=1, column=1, padx=10, pady=10)

        btn_aceptar = tk.Button(self, text="Aceptar", command=self.aceptar)
        btn_aceptar.grid(row=2, column=0, padx=10, pady=10)

        btn_cancelar = tk.Button(self, text="Cancelar", command=self.destroy)
        btn_cancelar.grid(row=2, column=1, padx=10, pady=10)

    def aceptar(self):
        nombre = self.entry_nombre.get()
        descripcion = self.entry_descripcion.get()
        if not nombre:
            messagebox.showwarning("Validación", "Debe ingresar el nombre del archivo.")
            return
        # Puedes agregar más validaciones aquí
        if self.aceptar_callback:
            self.aceptar_callback(nombre, descripcion)
        self.destroy()