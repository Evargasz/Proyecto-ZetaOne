# login_dialog.py

import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from usuario import UsuarioSesion

class LoginDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Usuario:").grid(row=0, column=0, sticky="e")
        tk.Label(master, text="Contraseña:").grid(row=1, column=0, sticky="e")
        tk.Label(master, text="Rol:").grid(row=2, column=0, sticky="e")

        self.user_entry = tk.Entry(master)
        self.pass_entry = tk.Entry(master, show="*")
        self.role_combo = ttk.Combobox(master, values=["Catalogador", "Administrador"], state="readonly")
        self.role_combo.current(0)

        self.user_entry.grid(row=0, column=1, padx=5, pady=4)
        self.pass_entry.grid(row=1, column=1, padx=5, pady=4)
        self.role_combo.grid(row=2, column=1, padx=5, pady=4)

        return self.user_entry  # initial focus

    def apply(self):
        usuario = self.user_entry.get().strip()
        clave = self.pass_entry.get()
        rol = self.role_combo.get()
        credenciales = {
            "Catalogador": {"usuario": "catalogador", "clave": "catalogo123"},
            "Administrador": {"usuario": "admin", "clave": "admin123"}
        }
        if usuario == credenciales[rol]["usuario"] and clave == credenciales[rol]["clave"]:
            UsuarioSesion.iniciar(usuario, rol.lower())
        else:
            UsuarioSesion.cerrar()
            messagebox.showerror("Error", "Usuario o clave incorrectos")