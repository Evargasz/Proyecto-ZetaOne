# gui/ventana_principal.py
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from core.simulador import cargar_accesos, simular_acceso

class VentanaPrincipal(tb.Frame):
    def __init__(self, master):
        super().__init__(master, padding=15)
        self.master = master
        self.master.title("Simulador de Accesos")
        self.master.geometry("700x400")
        self.pack(fill="both", expand=True)

        # Cargar los datos
        self.accesos = cargar_accesos()

        # Crear la interfaz
        self.crear_widgets()
        self.poblar_tabla()

    def crear_widgets(self):
        # Frame para la tabla
        frame_tabla = tb.Frame(self)
        frame_tabla.pack(fill="both", expand=True, pady=(0, 15))

        # Tabla (Treeview)
        columnas = ("tipo", "usuario", "ruta")
        self.tree = tb.Treeview(frame_tabla, columns=columnas, show="headings", bootstyle="primary")
        
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("usuario", text="Usuario")
        self.tree.heading("ruta", text="Ruta / URL")

        self.tree.column("tipo", width=80, anchor="center")
        self.tree.column("usuario", width=150)
        self.tree.column("ruta", width=400)

        # Scrollbar
        scrollbar = tb.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview, bootstyle="round")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Frame para los botones
        frame_botones = tb.Frame(self)
        frame_botones.pack(fill="x")

        self.btn_simular = tb.Button(frame_botones, text="Simular Acceso Seleccionado", command=self.on_simular, bootstyle="success")
        self.btn_simular.pack(side="left", padx=(0, 10))

        self.btn_recargar = tb.Button(frame_botones, text="Recargar Lista", command=self.on_recargar, bootstyle="secondary-outline")
        self.btn_recargar.pack(side="left")

    def poblar_tabla(self):
        # Limpiar tabla anterior
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Llenar con nuevos datos
        for i, acceso in enumerate(self.accesos):
            self.tree.insert("", "end", iid=i, values=(acceso['tipo'], acceso['usuario'], acceso['ruta']))

    def on_simular(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un acceso de la lista.", parent=self)
            return
        
        item_id = int(seleccion[0])
        acceso_seleccionado = self.accesos[item_id]

        exito, mensaje = simular_acceso(acceso_seleccionado)

        if exito:
            messagebox.showinfo("Simulación Exitosa", mensaje, parent=self)
        else:
            messagebox.showerror("Error en Simulación", mensaje, parent=self)

    def on_recargar(self):
        self.accesos = cargar_accesos()
        self.poblar_tabla()
        messagebox.showinfo("Recargado", "La lista de accesos ha sido actualizada desde el archivo.", parent=self)