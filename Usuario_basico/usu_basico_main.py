import tkinter as tk
from tkinter import messagebox, Toplevel, Entry, Label, Button, Frame
from tkinter import ttk
from PIL import Image, ImageTk
import os
import getpass
import json

FAVORITOS_FILE = 'Favoritos.json'

#--------------------Precargar favoritos guardados-------------------
def cargar_favoritos():
    if os.path.exists(FAVORITOS_FILE):
        try:
            with open(FAVORITOS_FILE, 'r', encoding='utf-8') as fav:
                return json.load(fav)
        except Exception as err:
            print(f"Error al leer favoritos: {err}")
            return[]
    return []

def guardar_favoritos(favoritos):
    try:
        with open(FAVORITOS_FILE, 'w', encoding='utf-8') as fav:
            json.dump(favoritos, fav, ensure_ascii=False, indent=4)
    except Exception as err:
        print(f"Error al guardar favoritos: {err}")

class usuBasicoMain(tk.Frame):
    def __init__(self, master, controlador):
        super().__init__(master)
        self.root = master
        self.master = master

        # Cargar ambientes desde ambientes.json
        self.lista_de_ambientes = []
        try:
            with open(r'json\ambientes.json', 'r', encoding='utf-8') as f:
                self.lista_de_ambientes = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar ambientes.json\n{e}")

        # Configuración de ventana
        self.root.title("ZetaOne")
        ventana_ancho = 790
        ventana_alto = 600
        pantalla_ancho = self.root.winfo_screenwidth()
        pantalla_alto = self.root.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.root.resizable(False, False)

        # funcionalidades 
        self.funcionalidades = [
            {
                "titulo": "Desbloquear usuario",
                "desc": "Borrar usuario de un ambiente...",
                "Favoritos": False,
                "accion": self.usar_desbloquear_usuario
            },
            {
                "titulo": "Autorizar tablas",
                "desc": "Autoriza ciertas tablas en BD.",
                "Favoritos": False,
                "accion": self.usar_autorizar_tablas
            },
            {
                "titulo": "Actualizar fecha de contabilidad",
                "desc": "Descripción...",
                "Favoritos": False,
                "accion": self.usar_actualizar_fecha_cont
            }
        ]

        self.favoritos = cargar_favoritos()
        for func in self.funcionalidades:
            func["Favoritos"] = func["titulo"] in self.favoritos
    
        #variables de la barra de busqueda
        self.texto_busqueda = ""
        self.placeholder_text = "¿Qué deseas hacer?"
    
        #icono
        self.root.iconbitmap("imagenes_iconos/Zeta99.ico")

        # Variables de control del filtro
        self.filtro_favoritos = False
        self.color_boton_activo = "#20ABFC"
        self.color_boton_default = "#F2F2F2"

        # 1. SIDEBAR IZQUIERDA
        self.sidebar = tk.Frame(self.root, bg="#fff", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.armar_sidebar()

        # 2. ÁREA PRINCIPAL DERECHA
        self.main_frame = tk.Frame(self.root, bg="#F7F7F7")
        self.main_frame.pack(side="right", fill="both", expand=True)
        self.armar_area_principal()

    #frame de la izquierda
    def armar_sidebar(self):
        usuario_img = Image.open("imagenes_iconos/userico.png")
        usuario_img = usuario_img.resize((120, 120))
        self.usuario_icon = ImageTk.PhotoImage(usuario_img)
        tk.Label(self.sidebar, image=self.usuario_icon, bg="#fff").pack(pady=(30, 10))

        nombre_usuario = getpass.getuser()
        bienvenida_lbl = tk.Label(self.sidebar, text=f"BIENVENIDO\n{nombre_usuario}", bg="#fff", font=("Arial", 12))
        bienvenida_lbl.pack(pady=(0, 300))

        btn_salir = tk.Button(self.sidebar, text="salir", bg="#333", fg="#fff", font=("Arial", 12), height=1,
                              relief="flat", width=10, command=self.salir)
        btn_salir.pack(side="bottom", pady=20)
        
    #------------------------------------------frame de la derecha---------------------------------------------
    def armar_area_principal(self):
        #Buscador

        barra_superior = tk.Frame(self.main_frame, bg="#fff")
        barra_superior.pack(fill="x", padx=40, pady=20)

        self.entry_busqueda = tk.Entry(barra_superior, font=("Arial", 14))
        self.entry_busqueda.insert(0, self.placeholder_text)
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 0), ipady=4)

        def clear_placeholder_busqueda(event):
            if self.entry_busqueda.get() == self.placeholder_text:
                self.entry_busqueda.delete(0, tk.END)
                self.entry_busqueda.config(foreground='black', show="")

        def add_placeholder_busqueda(event):
            if self.entry_busqueda.get() == "":
                self.entry_busqueda.insert(0, self.placeholder_text)
                self.entry_busqueda.config(foreground='black', show="")

        self.entry_busqueda.bind("<FocusIn>", clear_placeholder_busqueda)
        self.entry_busqueda.bind("<FocusOut>", add_placeholder_busqueda)
        self.entry_busqueda.bind("<Return>", lambda event: self.accion_busqueda())

        lupa_img = Image.open("imagenes_iconos/lupa.png")
        lupa_img = lupa_img.resize((22, 22))
        self.lupa_icon = ImageTk.PhotoImage(lupa_img)

        btn_lupa = tk.Button(barra_superior, image=self.lupa_icon, relief="flat",
                             bg="#fff", cursor="hand2", bd=0,
                             command=self.accion_busqueda)
        btn_lupa.pack(side="left")

        #-----------------------filtrado de contenido---------------------------------

        filtros_frame = tk.Frame(self.main_frame, bg="#fff")
        filtros_frame.pack(anchor="w", padx=56, pady=(5, 10))

        self.filtro_todos = tk.Button(filtros_frame, text="Todos", bg="#ddd", relief="groove", command=self.mostrar_todos)
        self.filtro_todos.pack(side="left", padx=(0, 10))

        self.boton_filtro_favoritos = tk.Button(
            filtros_frame, text="Favoritos",
            bg=self.color_boton_default,
            font=("Arial", 10),
            command=self.toggle_filtro_favoritos,
            width=12
        )
        self.boton_filtro_favoritos.pack(side="left", padx=5)
        
        self.boton_recargar = tk.Button(
            filtros_frame, text="Recargar",
            bg="#e6e6e6",
            font=("Arial", 10),
            command=self.recargar_cards,
            width=12
        )
        self.boton_recargar.pack(side="left", padx=5)

        separador = tk.Frame(self.main_frame, height=2, bg="#dedede", bd=0, relief="flat")
        separador.pack(fill="x", padx=40, pady=(0, 10))

        self.cards_frame = tk.Frame(self.main_frame, bg="#F7F7F7")
        self.cards_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        

        self.mostrar_funcionalidades()

    def mostrar_funcionalidades(self, filtro_favoritos=False):
                
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        if filtro_favoritos:
            funcionalidades_a_mostrar = [f for f in self.funcionalidades if f.get("Favoritos")]
            if not funcionalidades_a_mostrar:
                mensaje = tk.Label(
                    self.cards_frame,
                    text="no tienes ningun acceso rapido activo. \nMarca alguna funcionalidad y la veras aqui",
                    font=("Arial", 12, "italic"),
                    bg="#f7f7f7",
                    fg="#212020",
                    justify="center"
                )
                mensaje.pack(expand=True, pady=50)
                return
        else:
            funcionalidades_a_mostrar = self.funcionalidades

        texto = getattr(self, "texto_busqueda", "")
        if texto:
            funcionalidades_a_mostrar = [
                f for f in funcionalidades_a_mostrar
                if texto in f["titulo"].lower() or texto in f["desc"].lower()
            ]

        if not funcionalidades_a_mostrar:
            mensaje = tk.Label(
                self.cards_frame,
                text="No se encontraron funcionalidades con relacion a la busqueda",
                font=("Arial", 12, "italic"),
                bg="#f7f7f7",
                fg="#212020",
                justify="center"
            )
            mensaje.pack(expand=True, pady=50)
            return

        columnas = 2
        fila = 0
        columna = 0
        for func in funcionalidades_a_mostrar:
            card_frame = tk.Frame(self.cards_frame, bd=1, relief="solid", bg="#f9f9f9")
            card_frame.grid(row=fila, column=columna, padx=10, pady=10, sticky="nsew")
            tk.Label(card_frame, text=func["titulo"], font=("Arial", 11, "bold"), bg="#f9f9f9").pack(pady=(6, 3))
            tk.Label(card_frame, text=func["desc"], font=("Arial", 9), bg="#f9f9f9").pack(pady=(0, 7), padx=11)
            es_fav = func.get("Favoritos", False)
            btn_acceso = tk.Button(
                card_frame,
                text="Añadir a favoritos" if not func.get("Favoritos") else "Quitar de favoritos",
                bg="#f9f9f9" if not func.get("Favoritos") else "#20ABFC",
                command=lambda f=func: self.toggle_Favoritos(f))
            btn_acceso.pack(side="left", padx=(14, 8), pady=6)
            btn_usar = Button(
                card_frame,
                text="Usar",
                command=func["accion"]
                )
            btn_usar.pack(side="right", padx=10, pady=6)

            columna += 1
            if columna >= columnas:
                columna = 0
                fila += 1

    def salir(self):
        self.root.destroy()
    
    def accion_busqueda(self):
        txt = self.entry_busqueda.get()
        if txt == self.placeholder_text or txt.strip() == "":
            self.texto_busqueda = ""
        else:
            self.texto_busqueda = txt.strip().lower()
        self.mostrar_funcionalidades(filtro_favoritos=self.filtro_favoritos)

    def toggle_filtro_favoritos(self):
        self.filtro_favoritos = not self.filtro_favoritos

        if self.filtro_favoritos:
            self.boton_filtro_favoritos.config(bg=self.color_boton_activo, fg="white")
            self.mostrar_funcionalidades(filtro_favoritos=True)
            print("Acceso rápido habilitado")
        else:
            self.boton_filtro_favoritos.config(bg=self.color_boton_default, fg="black")
            self.mostrar_funcionalidades(filtro_favoritos=False)
            print("Todos los accesos")

    def toggle_Favoritos(self, funcionalidad):
        funcionalidad["Favoritos"] = not funcionalidad.get("Favoritos", False)
        # ACTUALIZA tu lista de favoritos y GUARDA
        self.favoritos = [f["titulo"] for f in self.funcionalidades if f.get("Favoritos", False)]
        guardar_favoritos(self.favoritos)
        self.mostrar_funcionalidades(self.filtro_favoritos)
            
    def mostrar_todos(self):
        self.filtro_favoritos = False
        self.boton_filtro_favoritos.config(bg=self.color_boton_default, fg="black")
        self.mostrar_funcionalidades(filtro_favoritos=False)

    def recargar_cards(self):
        self.entry_busqueda.delete(0, tk.END)
        self.entry_busqueda.insert(0, self.placeholder_text)
        self.entry_busqueda.config(foreground='black')
        self.texto_busqueda = ""
        self.filtro_favoritos = False
        self.boton_filtro_favoritos.config(bg=self.color_boton_default, fg="black")
        self.mostrar_funcionalidades(filtro_favoritos=False)
        self.entry_busqueda.focus_set()
        self.entry_busqueda.icursor(0)
        self.root.focus()

    def abrir_modal(self, parent, ambientes_lista, callback_confirmar):
        import getpass
        from tkinter import ttk
        modal = Toplevel(parent)
        ancho, alto = 320, 160
        modal.title("desbloquear usuario")
        self.centrar_ventana(modal, ancho, alto)
        modal.grab_set()
        modal.resizable(False, False)
        lbl_ambiente = Label(modal, text="Ambiente")
        lbl_ambiente.place(x=20, y=30)
        # Usar nombre del ambiente para el Combobox
        lista_nombres_ambiente = [amb['nombre'] for amb in ambientes_lista]
        entry_ambiente = ttk.Combobox(modal, values=lista_nombres_ambiente, state='readonly')
        entry_ambiente.place(x=100, y=30, width=180)

        lbl_usuario = Label(modal, text="Usuario")
        lbl_usuario.place(x=20, y=70)
        entry_usuario = Entry(modal)
        entry_usuario.place(x=100, y=70, width=180)
        entry_usuario.insert(0, getpass.getuser())

        def on_continuar():
            ambiente = entry_ambiente.get()
            usuario = entry_usuario.get()
            if not ambiente or not usuario: 
                messagebox.showwarning("Campo/s vació/s", "Por favor complete ambos campos.")
                return
            ambiente_obj = next((a for a in ambientes_lista if a['nombre'] == ambiente), None)
            if ambiente_obj is None:
                messagebox.showerror("Ambiente no encontrado", "Por favor seleccione un ambiente válido.")
                return
            callback_confirmar(usuario, ambiente_obj)
            modal.destroy()

        btn_continuar = Button(modal, text="Continuar", width=12, command=on_continuar)
        btn_continuar.place(relx=1.0, rely=1.0, x=-30, y=-20, anchor='se')

    def centrar_ventana(self, ventana, ancho, alto):
        ventana.update_idletasks()
        pantalla_ancho = ventana.winfo_screenwidth()
        pantalla_alto = ventana.winfo_screenheight()
        x = int((pantalla_ancho/2)-(ancho/2))
        y = int((pantalla_alto/2)-(alto/2))
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    def usar_desbloquear_usuario(self):
        self.abrir_modal(self.master, self.lista_de_ambientes, self.desbloquear_usuario_en_bd)

    def usar_autorizar_tablas(self):
        messagebox.showinfo("funcion no implementada", "esta funcion estara disponible en breve" )
    
    def usar_actualizar_fecha_cont(self):
        messagebox.showinfo("funcion no implementada", "esta funcion estara disponible en breve")
    
    def desbloquear_usuario_en_bd(self, usuario, ambiente):
        '''
        Construye la cadena de conexión según el driver, para Sybase ASE ODBC Driver usa PORT=,
        para los demás (SQL Server, Sybase clásico) usa SERVER=ip,puerto
        '''
        import pyodbc
        resp = messagebox.askyesno(
            "Confirmar acción",
            f"¿Está seguro de borrar la sesión en '{ambiente['nombre']}' para el usuario '{usuario}'?"
        )
        if not resp:
            return

        driver = ambiente['driver']
        if driver == 'Sybase ASE ODBC Driver':
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={ambiente['ip']};"
                f"PORT={ambiente['puerto']};"
                f"DATABASE={ambiente['base']};"
                f"UID={ambiente['usuario']};"
                f"PWD={ambiente['clave']};"
            )
        else:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={ambiente['ip']},{ambiente['puerto']};"
                f"DATABASE={ambiente['base']};"
                f"UID={ambiente['usuario']};"
                f"PWD={ambiente['clave']};"
            )

        print("[DEBUG] Cadena de conexión:", conn_str)
        print("[DEBUG] Drivers instalados:", pyodbc.drivers())
        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()
            cursor.execute("delete cobis..in_login where lo_login = ?", usuario)
            conn.commit()
            conn.close()
            messagebox.showinfo(
                "Éxito",
                f"Sesión del usuario '{usuario}' borrada correctamente en el ambiente '{ambiente['nombre']}'."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")