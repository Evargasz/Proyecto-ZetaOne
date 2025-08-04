import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

class usuBasicoMain:
    def __init__(self, root):
        self.root = root
        #config ventana
        self.root.title("ZetaOne")
        ventana_ancho = 900
        ventana_alto = 600
        pantalla_ancho = self.root.winfo_screenwidth()
        pantalla_alto = self.root.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2 ))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        root.resizable(False, False)
        self.filtro_acceso_rapido = False  # Estado del filtro de acceso rápido
        self.color_boton_activo = "#FF3131"  # Rojo botón activo
        self.color_boton_default = "#F2F2F2"  # Color botón por defecto

        # 1. SIDEBAR IZQUIERDA
        self.sidebar = tk.Frame(self.root, bg="#fff", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.armar_sidebar()

        # 2. ÁREA PRINCIPAL DERECHO
        self.main_frame = tk.Frame(self.root, bg="#F7F7F7")
        self.main_frame.pack(side="right", fill="both", expand=True)
        self.armar_area_principal()

    def armar_sidebar(self):
        usuario_img = Image.open("imagenes_iconos/userico.png") #llamado de imagen
        usuario_img = usuario_img.resize((120, 120)) #ajustar tamaño
        self. usuario_icon = ImageTk.PhotoImage(usuario_img)
        tk.Label(self.sidebar, image=self.usuario_icon, bg="#fff").pack(pady=(30, 10))

        # Texto de bienvenida
        bienvenida_lbl = tk.Label(self.sidebar, text="BIENVENIDO\n*usuario del cp*", bg="#fff", font=("Arial", 12))
        bienvenida_lbl.pack(pady=(0, 300))

        # Botón salir
        btn_salir = tk.Button(self.sidebar, text="salir", bg="#333", fg="#fff", font=("Arial", 12), height=1,
                              relief="flat", width=10, command=self.salir)
        btn_salir.pack(side="bottom", pady=20)

    def armar_area_principal(self):
        # --- Barra superior con búsqueda y switches ---
        barra_superior = tk.Frame(self.main_frame, bg="#fff")
        barra_superior.pack(fill="x", padx=40, pady=20)

        # Campo de búsqueda
        self.entry_busqueda = tk.Entry(barra_superior, width=35, font=("Arial", 14))
        self.entry_busqueda.insert(0, "¿Qué deseas hacer?")
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 0), ipadx=4)

        def clear_placeholder_busqueda(event):
            if self.entry_busqueda.get() == "¿Qué deseas hacer?":
                self.entry_busqueda.delete(0, tk.END)
                self.entry_busqueda.config(foreground='black', show="")

        def add_placeholder_busqueda(event):
            if self.entry_busqueda.get() == "":
                self.entry_busqueda.insert(0, "¿Qué deseas hacer?")
                self.entry_busqueda.config(foreground='black', show="")
        
        self.entry_busqueda.bind("<FocusIn>", clear_placeholder_busqueda)
        self.entry_busqueda.bind("<FocusOut>", add_placeholder_busqueda)
        self.entry_busqueda.bind("<Return>", lambda event: self.accion_busqueda())

        # Botón de búsqueda (solo ícono, aquí como texto)
        lupa_img = Image.open("imagenes_iconos/lupa.png")
        lupa_img = lupa_img.resize((22, 22))
        self.lupa_icon = ImageTk.PhotoImage(lupa_img)

        btn_lupa = tk.Button(barra_superior, image=self.lupa_icon, relief="flat",
                             bg="#fff", cursor="hand2", bd=0,
                             command=self.accion_busqueda)
        btn_lupa.pack(side="left")

    
        #------botones para filtros------

        # ------ Nuevo frame para filtros, alineados a la izquierda ------
        filtros_frame = tk.Frame(self.main_frame, bg="#fff")
        filtros_frame.pack(fill=None, anchor="w", padx=56, pady=(5, 10))  # padding izquierdo y vertical

        self.filtro_todos = tk.Button(filtros_frame, text="Todos", bg="#ddd", relief="groove")
        self.filtro_todos.pack(side="left", padx=(0, 10))  # espaciado horizontal entre botones

        self.boton_acceso_rapido = tk.Button(
            self.frame_botones, text="Acceso rápido",
            bg=self.color_boton_default,
            font=("Arial", 10),
            command=self.toggle_acceso_rapido,
            width=12
        )
        self.boton_acceso_rapido.pack(side="left", padx=5)

        # ------ Línea separadora visual ------
        separador = tk.Frame(self.main_frame, height=2, bg="#dedede", bd=0, relief="flat")
        separador.pack(fill="x", padx=40, pady=(0, 10))

        # ------ Frame principal de cards ------
        self.cards_frame = tk.Frame(self.main_frame, bg="#F7F7F7")
        self.cards_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))


        # Aquí ponemos las cards disponibles (ejemplo con 3 funciones, se puede adaptar a más)
        self.funcionalidades = [
            {
                "titulo": "Desbloquear usuario",
                "desc": "Borrar usuario de un ambiente...",
                "acceso_directo": False
            },
            {
                "titulo": "Autorizar tablas",
                "desc": "Autoriza ciertas tablas en BD.",
                "acceso_directo": False
            },
            {
                "titulo": "Actualizar fecha de contabilidad",
                "desc": "Descripción...",
                "acceso_directo": False
            }
        ]
        self.crear_cards_funcionalidades()

    def mostrar_funcionalidades(self, acceso_rapido=False):
        """
        Muestra las cards de funcionalidades.
        Si acceso_rapido es True, solo muestra las cards habilitadas como acceso rápido.
        """
        # Limpia el frame de cards
        for widget in self.frame_cards.winfo_children():
            widget.destroy()

        # Elige qué funcionalidades mostrar según el filtro
        if acceso_rapido:
            funcionalidades_a_mostrar = [f for f in self.funcionalidades if f["acceso_directo"]]
        else:
            funcionalidades_a_mostrar = self.funcionalidades

        # Aquí abajo, tu rutina original para crear las cards:
        columnas = 2  # Número de columnas de las cards
        fila = 0
        columna = 0
        for func in funcionalidades_a_mostrar:
            card_frame = tk.Frame(self.frame_cards, bd=1, relief="solid", bg="#f9f9f9")
            card_frame.grid(row=fila, column=columna, padx=10, pady=10, sticky="nsew")
            # Título
            tk.Label(card_frame, text=func["titulo"], font=("Arial", 11, "bold"), bg="#f9f9f9").pack(pady=(6, 3))
            # Descripción
            tk.Label(card_frame, text=func["descripcion"], font=("Arial", 9), bg="#f9f9f9").pack(pady=(0, 7), padx=11)
            # Botón acceso rápido
            btn_acceso = tk.Button(
                card_frame,
                text="acceso rápido" if not func["acceso_directo"] else "acceso directo",
                font=("Arial", 8),
                width=15,
                bg="#d5f1ff" if not func["acceso_directo"] else "#FF3131",
                command=lambda f=func: self.toggle_acceso_directo(f)
            )
            btn_acceso.pack(side="left", padx=(14, 8), pady=6)
            # Botón utilizar funcionalidad
            btn_usar = tk.Button(card_frame, text="usar", font=("Arial", 8), width=8,
                                command=lambda t=func["titulo"]: self.usar_funcionalidad(t))
            btn_usar.pack(side="right", padx=(8, 14), pady=6)

            columna += 1
            if columna >= columnas:
                columna = 0
                fila += 1

    def toggle_acceso(self, idx):
        # Alternar estado de acceso rápido/acceso directo
        for i, func in enumerate(self.funcionalidades):
            if i == idx:
                func["acceso_directo"] = not func["acceso_directo"]
        # Ordenar para poner primero los que son acceso directo
        self.funcionalidades.sort(key=lambda x: x["acceso_directo"], reverse=True)
        self.crear_cards_funcionalidades()

    def usar_funcion(self, idx):
        # Placeholder: aquí va la acción que realiza la función
        nombre_func = self.funcionalidades[idx]["titulo"]
        messagebox.showinfo("Funcionalidad", f"¡Has seleccionado usar: {nombre_func}!")

    def salir(self):
        self.root.destroy()

    def accion_busqueda(self):

        txt = self.entry_busqueda.get()
        print(f'buscaste esto: {txt}')
        #si funciona la accion, falta implementarla para que busque ajasjdfsjaf

    #funcion de acceso rapido
    def toggle_acceso_rapido(self):
        """
        Alterna el estado del filtro de acceso rápido.
        Cambia el color del botón y muestra solo las funcionalidades correspondientes.
        """
        # Cambiar el estado del filtro
        self.filtro_acceso_rapido = not self.filtro_acceso_rapido

        if self.filtro_acceso_rapido:
            # Cambia el color del botón a rojo y muestra solo accesos rápidos
            self.boton_acceso_rapido.config(bg=self.color_boton_activo, fg="white")
            self.mostrar_funcionalidades(acceso_rapido=True)
            messagebox.showinfo("Acceso rápido habilitado",
                "Mostrando solo funcionalidades de acceso rápido.\n"
                "El botón está rojo porque el filtro está activo.")
        else:
            # Vuelve el botón a su color y muestra todas las funcionalidades
            self.boton_acceso_rapido.config(bg=self.color_boton_default, fg="black")
            self.mostrar_funcionalidades(acceso_rapido=False)
            messagebox.showinfo("Todos los accesos",
                "Todos los elementos han sido restaurados.")
            
    def toggle_acceso_directo(self, funcionalidad):
        """
        Cambia el valor de acceso rápido y actualiza la visualización.
        """
        funcionalidad["acceso_directo"] = not funcionalidad["acceso_directo"]
        # Al cambiar un acceso, vuelve a mostrar cards conforme el filtro actual
        self.mostrar_funcionalidades(self.filtro_acceso_rapido)
# ----------- Ejecución principal -----------
if __name__ == "__main__":
    root = tk.Tk()
    app = usuBasicoMain(root)
    root.mainloop()