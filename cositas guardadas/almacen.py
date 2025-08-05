#ventana modal de desbloquear usuario

import tkinter as tk
from tkinter import Toplevel, Entry, Label, Button

def abrir_modal_desbloquear_usuario():
    # Crear ventana modal
    modal = Toplevel()
    modal.title("Desbloquear Usuario")
    modal.geometry("300x150")  # Ajusta tamaño según tu interfaz
    modal.grab_set()  # Hace que esta ventana sea modal

    # Etiqueta y campo "Ambiente"
    lbl_ambiente = Label(modal, text="Ambiente")
    lbl_ambiente.place(x=20, y=30)
    entry_ambiente = Entry(modal)
    entry_ambiente.place(x=100, y=30, width=150)

    # Etiqueta y campo "Usuario"
    lbl_usuario = Label(modal, text="Usuario")
    lbl_usuario.place(x=20, y=70)
    entry_usuario = Entry(modal)
    entry_usuario.place(x=100, y=70, width=150)

    # Botón continuar en la esquina inferior derecha
    btn_continuar = Button(modal, text="Continuar", width=10)
    btn_continuar.place(relx=1.0, rely=1.0, x=-90, y=-20, anchor='se')

# Esto es solo para prueba aislada, en tu aplicación se llamaría desde el botón USAR de la card "Desbloquear Usuario"
root = tk.Tk()
btn = Button(root, text="Abrir Modal", command=abrir_modal_desbloquear_usuario)
btn.pack(pady=20)
root.mainloop()