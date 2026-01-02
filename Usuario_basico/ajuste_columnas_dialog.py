import tkinter as tk
from tkinter import ttk, messagebox
import logging

class AjusteColumnasDialog(tk.Toplevel):
    def __init__(self, parent, columnas_extra, col_meta_dest, callback_confirm, abort_func):
        super().__init__(parent)
        self.title("Columnas adicionales en destino detectadas — ¿Desea ajustar y continuar?")
        self.columnas_extra = columnas_extra
        self.col_meta_dest = col_meta_dest
        self.callback_confirm = callback_confirm
        self.abort_func = abort_func
        self.valores = {}
        self.inputs = {}
        self._build_ui()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self):
        frame = ttk.Frame(self)
        frame.pack(padx=16, pady=16, fill="both", expand=True)
        cols = ("Columna", "Tipo", "Nullable", "Default en esquema", "Valor por defecto")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=len(self.columnas_extra))
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.tree = tree

        # Inputs para cada columna
        for idx, col in enumerate(self.columnas_extra):
            meta = self.col_meta_dest.get(col.lower(), {})
            tipo = meta.get('type', 'Desconocido')
            nullable = meta.get('nullable', True)
            default = meta.get('default', None)
            sugerido = self._sugerir_valor(tipo, nullable, default)
            self.valores[col] = tk.StringVar(value="NULL" if sugerido is None else str(sugerido))
            tree.insert('', 'end', iid=col, values=(col, tipo, "Sí" if nullable else "No", default if default else "No", self.valores[col].get()))

        # Agregar funcionalidad de edición
        def on_tree_select(event):
            selected_item = tree.selection()
            if selected_item:
                col = selected_item[0]
                entry = ttk.Entry(frame, textvariable=self.valores[col], width=15)
                entry.grid(row=1, column=0, pady=(12, 0), sticky="ew")
                entry.focus_set()
                def save_value(event):
                    tree.set(col, "Valor por defecto", self.valores[col].get())
                    entry.destroy()
                entry.bind("<Return>", save_value)

        tree.bind("<ButtonRelease-1>", on_tree_select)

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, pady=(12, 0), sticky="ew")
        btn_ok = ttk.Button(btn_frame, text="Ajustar y migrar", command=self._on_confirm)
        btn_ok.pack(side="left", padx=(0, 8))
        btn_cancel = ttk.Button(btn_frame, text="Cancelar", command=self._on_cancel)
        btn_cancel.pack(side="left")

    def _sugerir_valor(self, tipo, nullable, default):
        # Lógica de sugerencia según tipo
        if default is not None:
            return default
        if tipo is None:
            return None
        tipo_str = str(tipo).lower()
        if "int" in tipo_str or "numeric" in tipo_str or "decimal" in tipo_str or "smallint" in tipo_str or "bigint" in tipo_str:
            return 0
        if "float" in tipo_str or "real" in tipo_str or "double" in tipo_str:
            return 0.0
        if "bit" in tipo_str or "bool" in tipo_str:
            return 0
        if "date" in tipo_str or "time" in tipo_str:
            return None
        if "char" in tipo_str or "text" in tipo_str:
            return None
        if "binary" in tipo_str:
            return None
        return None

    def _on_confirm(self):
        try:
            ajuste = {}
            for col in self.columnas_extra:
                val = self.valores[col].get()
                if not self._validar_valor(val):
                    logging.error("Valor inválido para la columna '%s': %s", col, val)
                    messagebox.showerror("Error", f"Valor inválido para la columna '{col}': {val}")
                    return
                ajuste[col] = None if val.upper() == "NULL" else val
            logging.info("Valores ajustados recopilados: %s", ajuste)
            self.callback_confirm(ajuste)
            logging.info("Callback confirm ejecutado con ajustes: %s", ajuste)
        except Exception as e:
            logging.error("Error en _on_confirm: %s", str(e))
            messagebox.showerror("Error crítico", f"Ocurrió un error inesperado: {str(e)}")
        finally:
            logging.info("Diálogo cerrado correctamente.")
            self.destroy()

    def _validar_valor(self, valor):
        # Validar que el valor no sea vacío y cumpla con otros criterios
        if not valor:
            return False
        # Agregar más validaciones según el tipo de dato
        return True

    def _on_cancel(self):
        self.abort_func("Migración cancelada por el usuario.")
        self.destroy()
