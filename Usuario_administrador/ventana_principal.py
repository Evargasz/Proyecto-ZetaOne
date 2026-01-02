# gui/ventana_principal.py
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from core.simulador import cargar_accesos, simular_acceso
import logging

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
        scrollbar = tb.Scrollbar(frame_tabla, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Frame para los botones y entrada
        frame_botones = tb.Frame(self)
        frame_botones.pack(fill="x")

        self.entry_nueva_columna = tb.Entry(frame_botones, bootstyle="info")
        self.entry_nueva_columna.pack(side="left", padx=(0, 10))
        self.entry_nueva_columna.insert(0, "Nueva Columna")

        self.btn_aceptar_migrar = tb.Button(frame_botones, text="Aceptar y Migrar", command=self.on_aceptar_migrar, bootstyle="success")
        self.btn_aceptar_migrar.pack(side="left", padx=(0, 10))

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
        try:
            if not self.winfo_exists():
                logging.error("La ventana principal ya no existe. Operación cancelada.")
                return

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
        except Exception as e:
            logging.error(f"Error en on_simular: {e}")
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado: {e}", parent=self)

    def on_recargar(self):
        try:
            if not self.winfo_exists():
                logging.error("La ventana principal ya no existe. Operación cancelada.")
                return

            self.accesos = cargar_accesos()
            self.poblar_tabla()
            messagebox.showinfo("Recargado", "La lista de accesos ha sido actualizada desde el archivo.", parent=self)
        except Exception as e:
            logging.error(f"Error en on_recargar: {e}")
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado: {e}", parent=self)

    def on_aceptar_migrar(self):
        try:
            nueva_columna = self.entry_nueva_columna.get().strip()
            if not nueva_columna:
                messagebox.showwarning("Campo vacío", "Por favor, ingrese un nombre para la nueva columna.", parent=self)
                return

            valor_defecto = "Valor por defecto"  # Aquí puedes agregar un campo para que el usuario ingrese el valor por defecto

            seleccion = self.tree.selection()
            if not seleccion:
                messagebox.showwarning("Sin selección", "Por favor, seleccione un acceso de la lista.", parent=self)
                return

            item_id = int(seleccion[0])
            acceso_seleccionado = self.accesos[item_id]

            # Validar ajustes antes de continuar
            ajustes = {nueva_columna: valor_defecto}
            if not self.validar_ajustes(ajustes):
                messagebox.showerror("Error de Validación", "Los ajustes no son válidos.", parent=self)
                return

            # Llamar a la función de migración con la nueva columna y el valor por defecto
            try:
                exito, mensaje = migrar_con_nueva_columna(acceso_seleccionado, nueva_columna, valor_defecto)

                if exito:
                    messagebox.showinfo("Migración Exitosa", mensaje, parent=self)
                else:
                    messagebox.showerror("Error en Migración", mensaje, parent=self)
            except Exception as e:
                logging.error(f"Error en migrar_con_nueva_columna: {e}")
                messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado durante la migración: {e}", parent=self)

            # Regresar a la pantalla principal siempre
            self.master.deiconify()
        except Exception as e:
            logging.error(f"Error en on_aceptar_migrar: {e}")
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado: {e}", parent=self)

    def validar_ajustes(self, ajustes):
        """Valida los ajustes antes de continuar con la migración."""
        try:
            for columna, valor in ajustes.items():
                if not columna or not valor:
                    logging.error(f"Ajuste inválido: {columna} -> {valor}")
                    return False
            logging.info(f"Ajustes validados correctamente: {ajustes}")
            return True
        except Exception as e:
            logging.error(f"Error al validar ajustes: {e}")
            return False