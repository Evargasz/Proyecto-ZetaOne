#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparador de Archivos - Aplicación con Interfaz Gráfica Moderna
Desarrollado para comparar múltiples archivos y generar reportes de diferencias
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import difflib
import os
from datetime import datetime
from pathlib import Path
import threading

try:
    # Solución Final y Definitiva: Importar el módulo completo.
    import tkinterdnd2
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

class ModernFileComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("Comparador de Archivos - Versión Profesional")
        # La ventana ya no se abre en pantalla completa por defecto
        self.root.resizable(True, True) # Permitir modificar tamaño
        self.root.configure(bg='#f0f0f0') 
        
        # Variables
        self.selected_files = []
        self.processed_file_contents = {} # Almacenar contenido procesado para el reporte
        self.original_file_contents = {}  # Almacenar contenido original para el reporte
        self.all_detailed_diffs = []      # Almacenar todas las diferencias detalladas para el resumen
        self.comparison_results = []
        self._is_syncing_selection = False # Flag para evitar recursión en la sincronización de selección
        
        # Configurar estilo moderno
        self.setup_styles()
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.center_window()
    
    def setup_styles(self):
        """Configurar estilos modernos para la interfaz"""
        # --- CORRECCIÓN CLAVE ---
        # En lugar de crear un nuevo estilo, obtenemos el estilo existente de la ventana.
        # Esto evita sobreescribir los estilos de toda la aplicación.
        style = ttk.Style(self.root)
        
        # Colores modernos
        colors = {
            'primary': '#2196F3',
            'secondary': '#FFC107',
            'success': '#4CAF50',
            'danger': '#F44336',
            'dark': '#212121',
            'light': '#FAFAFA'
        }
        
        # Configurar estilos personalizados
        style.configure('Modern.TButton',
                       background=colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        style.map('Modern.TButton',
                 background=[('active', '#1976D2')])
        
        style.configure('Success.TButton',
                       background=colors['success'],
                       foreground='white',
                       borderwidth=2,
                       focuscolor='none',
                       padding=(15, 8),
                       font=('Segoe UI', 11, 'bold'))
        
        style.map('Success.TButton',
                 background=[('active', '#45a049')],
                 relief=[('pressed', 'flat'), ('!pressed', 'raised')])
        
        style.configure('Modern.TFrame',
                       background='#ffffff',
                       relief='flat',
                       borderwidth=1)
    
    def create_interface(self):
        """Crear la interfaz gráfica principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, 
                              text="🔍 Comparador de Archivos Profesional",
                              font=('Segoe UI', 24, 'bold'),
                              bg='#ffffff',
                              fg='#2196F3')
        title_label.pack(pady=(0, 30))
        
        # Contenedor principal para los paneles (ahora estáticos)
        # Usar un PanedWindow para permitir al usuario redimensionar los paneles
        panels_container = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg='#f0f0f0')
        panels_container.pack(fill=tk.BOTH, expand=True)

        # --- Panel Izquierdo (Controles) ---
        controls_frame = ttk.Frame(panels_container, style='Modern.TFrame')
        panels_container.add(controls_frame, width=350, minsize=300) # Añadir al PanedWindow

        # Frame para los botones de acción inferiores, anclado abajo
        bottom_actions_frame = ttk.Frame(controls_frame, style='Modern.TFrame')
        bottom_actions_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        self.create_report_action_buttons(bottom_actions_frame)

        # --- Área central con scroll para los controles principales ---
        # Esto evita que los botones se oculten en ventanas pequeñas.
        canvas = tk.Canvas(controls_frame, bg='#ffffff', highlightthickness=0)
        scrollbar = ttk.Scrollbar(controls_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Panel Derecho (Resultados) ---
        results_container = ttk.Frame(panels_container, style='Modern.TFrame')
        panels_container.add(results_container, minsize=400) # Añadir al PanedWindow
        self.create_results_frame(results_container)
        
        # Crear los componentes dentro del frame con scroll
        self.create_file_selection_frame(scrollable_frame)
        self.create_options_frame(scrollable_frame)
    
    def create_file_selection_frame(self, parent):
        """Crear frame para selección de archivos"""
        file_frame = ttk.LabelFrame(parent, text="📁 Selección de Archivos", 
                                   style='Modern.TFrame', padding=(20, 10))
        file_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 10), padx=10)
        
        # Lista de archivos seleccionados
        self.files_listbox = tk.Listbox(file_frame, 
                                       height=6, # Reducir altura para dar espacio a las opciones
                                       font=('Consolas', 10),
                                       bg='#f8f9fa',
                                       selectbackground='#2196F3',
                                       selectforeground='white', relief=tk.FLAT, borderwidth=0)
        self.files_listbox.pack(fill=tk.X, pady=(0, 15))
        
        # Solución Definitiva: Registrar el Listbox directamente como el objetivo de drop.
        if DND_AVAILABLE:
            self.files_listbox.drop_target_register(tkinterdnd2.DND_FILES)
            self.files_listbox.dnd_bind('<<Drop>>', self.on_drop_files)
        
        # Configurar texto para drag & drop
        if DND_AVAILABLE:
            drop_text = "💡 Arrastra archivos aquí desde el explorador"
        else:
            drop_text = "💡 (Instala 'tkinterdnd2' para Drag & Drop)"

        tk.Label(file_frame, text=drop_text,
                 font=('Segoe UI', 9, 'italic'),
                 bg='#ffffff', fg='#666666').pack(pady=(0, 10))
        
        
        # Botones de gestión de archivos
        buttons_frame = tk.Frame(file_frame, bg='#ffffff')
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="➕ Agregar Archivos", 
                  style='Modern.TButton',
                  command=self.add_files).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        # ttk.Button(buttons_frame, text="🗑️ Eliminar Seleccionado", 
        #         command=self.remove_selected_file).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        ttk.Button(buttons_frame, text="🧹 Limpiar Todo", 
                  command=self.clear_all_files).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
    def create_options_frame(self, parent):
        """Crear frame de opciones de comparación"""
        options_frame = ttk.LabelFrame(parent, text="⚙️ Opciones de Comparación",
                                      style='Modern.TFrame', padding=(20, 10))
        options_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 10), padx=10)
        
        # Variables de opciones
        self.ignore_whitespace = tk.BooleanVar(value=False)
        self.ignore_case = tk.BooleanVar(value=False)
        self.show_context = tk.BooleanVar(value=True)
        self.sync_scroll = tk.BooleanVar(value=True)
        
        # Checkboxes
        tk.Checkbutton(options_frame, text="Ignorar espacios en blanco",
                      variable=self.ignore_whitespace,
                      bg='#ffffff', font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        tk.Checkbutton(options_frame, text="Ignorar mayúsculas/minúsculas",
                      variable=self.ignore_case,
                      bg='#ffffff', font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        tk.Checkbutton(options_frame, text="Mostrar contexto en diferencias",
                      variable=self.show_context,
                      bg='#ffffff', font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        tk.Checkbutton(options_frame, text="Sincronizar archivos",
                      variable=self.sync_scroll,
                      bg='#ffffff', font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        # Botón de comparación, ahora dentro de este frame
        self.compare_button = ttk.Button(options_frame, text="🔍 COMPARAR", 
                  style='Success.TButton',
                  command=self.compare_files,
                  state='disabled') # Deshabilitado inicialmente
        # Padding superior para separarlo de los checkboxes
        self.compare_button.pack(expand=True, fill=tk.X, pady=(15, 0))
    
    def create_results_frame(self, parent):
        """Crear frame para mostrar resultados"""
        results_frame = ttk.LabelFrame(parent, text="📊 Resultados de Comparación", 
                                      style='Modern.TFrame', padding=20)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # RF10.1: Contenedor tipo splitter horizontal
        panels_display_frame = ttk.Frame(results_frame, style='Modern.TFrame')
        panels_display_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid para que las dos columnas tengan el mismo peso
        panels_display_frame.grid_columnconfigure(0, weight=1)
        panels_display_frame.grid_columnconfigure(1, weight=1)
        panels_display_frame.grid_rowconfigure(0, weight=1) # Solo una fila

        # Panel A (Izquierda)
        frame_a = ttk.Frame(panels_display_frame, style='Modern.TFrame')
        title_frame_a = self._create_title_frame(frame_a, "Archivo 1")
        self.title_label_a = title_frame_a['title']
        self.status_label_a = title_frame_a['status']
        self.text_a = self._create_text_widget(frame_a, self.status_label_a, is_left=True)
        frame_a.grid(row=0, column=0, sticky="nsew") # Empaquetar con grid

        # Panel B (Derecha)
        frame_b = ttk.Frame(panels_display_frame, style='Modern.TFrame')
        title_frame_b = self._create_title_frame(frame_b, "Archivo 2")
        self.title_label_b = title_frame_b['title']
        self.status_label_b = title_frame_b['status']
        self.text_b = self._create_text_widget(frame_b, self.status_label_b, is_left=False)
        frame_b.grid(row=0, column=1, sticky="nsew") # Empaquetar con grid

        # Actualizar posición inicial del cursor
        self._update_status_display(self.text_a, self.status_label_a)
        self._update_status_display(self.text_b, self.status_label_b)

        # Sincronizar scroll
        # La configuración se hace en _create_text_widget para tener acceso a las scrollbars

        # Configurar tags para colores
        for text_widget in [self.text_a, self.text_b]:
            text_widget.tag_configure("diff", background="#FFEBEE") # Rojo claro para diferencias
            text_widget.tag_configure("diff_word", background="#F44336", foreground="white", font=('Consolas', 10, 'bold')) # Rojo intenso
            text_widget.tag_configure("header", foreground="#2196F3", font=('Consolas', 10, 'bold'))

    def _create_title_frame(self, parent, initial_text):
        """Crea el frame del título con el nombre del archivo y la etiqueta de estado."""
        title_frame = ttk.Frame(parent, style='Modern.TFrame')
        title_frame.pack(pady=(0, 5), padx=5, fill=tk.X)
        
        title_label = tk.Label(title_frame, text=initial_text, font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#333333', anchor='w')
        title_label.pack(side=tk.LEFT)
        
        status_label = tk.Label(title_frame, text="", font=('Segoe UI', 9), bg='#ffffff', fg='#666666', anchor='e')
        status_label.pack(side=tk.RIGHT)
        
        return {'title': title_label, 'status': status_label}

    def _create_text_widget(self, parent, status_label, is_left):
        """Crea un widget de texto con scrollbars e indicador de posición del cursor."""
        container_frame = tk.Frame(parent, bg='#f8f9fa')
        container_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame para el texto y sus scrollbars
        text_frame = tk.Frame(container_frame, bg='#f8f9fa', relief=tk.GROOVE, borderwidth=1)
        text_frame.pack(fill=tk.BOTH, expand=True)
        text = tk.Text(text_frame, wrap=tk.NONE, font=('Consolas', 10), 
                       bg='#f8f9fa', borderwidth=0, highlightthickness=0)
        
        # Asignar el comando de scroll correcto para la sincronización
        # La sincronización se maneja a través de los comandos de las scrollbars
        scroll_command_y = self._on_scroll_a_y if is_left else self._on_scroll_b_y
        scroll_command_x = self._on_scroll_a_x if is_left else self._on_scroll_b_x
        
        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=scroll_command_y)
        h_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=scroll_command_x)
        
        text.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y) 
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X) 
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) 

        # Bind events to update cursor position display
        text.bind("<KeyRelease>", lambda event, t=text, l=status_label: self._on_ui_change(event, t, l))
        text.bind("<ButtonRelease-1>", lambda event, t=text, l=status_label: self._on_ui_change(event, t, l))
        
        # Sincronizar selección
        text.bind("<<Selection>>", lambda event, t=text, l=status_label: self._on_selection_sync(event, t, l))
        
        # RF: Vincular el evento de la rueda del mouse para sincronización
        text.bind("<MouseWheel>", self._on_mouse_wheel) # Para Windows y macOS
        text.bind("<Button-4>", self._on_mouse_wheel)   # Para Linux (scroll up)
        text.bind("<Button-5>", self._on_mouse_wheel)   # Para Linux (scroll down)
        text.bind("<Shift-MouseWheel>", self._on_horizontal_mouse_wheel) # Scroll horizontal
        
        return text

    def _on_ui_change(self, event, source_widget, status_label): # text_widget was not defined
        """Manejador para eventos que actualizan la UI y sincronizan el cursor."""
        # Actualizar la etiqueta de estado del widget actual
        self._update_status_display(source_widget, status_label)

        # Sincronizar la posición del cursor si la opción está activa
        if not self.sync_scroll.get() or self._is_syncing_selection:
            return
        
        self._is_syncing_selection = True
        try:
            target_widget = self.text_b if source_widget == self.text_a else self.text_a
            target_status_label = self.status_label_b if source_widget == self.text_a else self.status_label_a
            
            # Sincronizar la posición del cursor (marca INSERT)
            current_cursor_pos = source_widget.index(tk.INSERT)
            target_widget.mark_set(tk.INSERT, current_cursor_pos)
            
            # Actualizar también la etiqueta de estado del widget de destino
            self._update_status_display(target_widget, target_status_label)
        finally:
            self.root.after_idle(lambda: setattr(self, '_is_syncing_selection', False))

    def _update_status_display(self, text_widget, status_label):
        """Actualiza la etiqueta de estado con la posición del cursor y la información de selección."""
        try:
            cursor_index = text_widget.index(tk.INSERT)
            line, char = map(int, cursor_index.split('.'))
            
            status_text = f"Ln {line}, Col {char + 1}"

            if text_widget.tag_ranges("sel"):
                sel_start_index = text_widget.index("sel.first")
                sel_end_index = text_widget.index("sel.last")
                
                sel_start_line, sel_start_char = map(int, sel_start_index.split('.'))
                sel_end_line, sel_end_char = map(int, sel_end_index.split('.'))
                
                selected_chars = len(text_widget.get(sel_start_index, sel_end_index))
                selected_lines = sel_end_line - sel_start_line + 1
                
                status_text += f"  ({selected_chars} caracteres, {selected_lines} líneas seleccionadas)"

            status_label.config(text=status_text)
        except tk.TclError:
            status_label.config(text="Ln ?, Col ?")

    def _on_selection_sync(self, event, source_widget, status_label):
        """Sincroniza la selección entre los dos paneles de texto si la opción está activa."""
        # Primero, actualiza el estado del widget actual
        self._update_status_display(source_widget, status_label)

        # Luego, sincroniza la selección si está activado
        if not self.sync_scroll.get() or self._is_syncing_selection:
            return

        self._is_syncing_selection = True
        try:
            target_widget = self.text_b if source_widget == self.text_a else self.text_a
            
            # Limpiar selección anterior en el widget de destino
            target_widget.tag_remove("sel", "1.0", "end")

            # Si hay selección en el origen, aplicarla al destino
            if source_widget.tag_ranges("sel"):
                start, end = source_widget.tag_ranges("sel")
                target_widget.tag_add("sel", start, end)
                # Al seleccionar, también asegúrate de que el área sea visible en el otro panel
                target_widget.see(start)
            else:
                target_widget.see(source_widget.index(tk.INSERT))
        finally:
            # Asegurarse de que el flag se resetee siempre
            self.root.after_idle(lambda: setattr(self, '_is_syncing_selection', False))

    def _on_scroll_a_y(self, *args):
        """Maneja el scroll vertical del panel A y sincroniza con B."""
        # args son (fraction_start, fraction_end) del scrollbar.set
        if self.sync_scroll.get():
            # Aplicar la acción de scroll a ambos paneles.
            # El método yview del Text widget interpreta correctamente todos los tipos de *args del scrollbar.
            self.text_a.yview(*args) # Esto es idempotente, pero asegura que el panel A se mueva.
            self.text_b.yview(*args) # Sincroniza el panel B con la misma acción.
        else:
            # Solo mover el panel A
            self.text_a.yview(*args)

    def _on_scroll_b_y(self, *args):
        """Maneja el scroll vertical del panel B y sincroniza con A."""
        if self.sync_scroll.get():
            self.text_b.yview(*args) # Mueve el panel B.
            self.text_a.yview(*args) # Sincroniza el panel A con la misma acción.
        else:
            self.text_b.yview(*args)

    def _on_scroll_a_x(self, *args):
        """Maneja el scroll horizontal del panel A y sincroniza con B."""
        if self.sync_scroll.get():
            self.text_a.xview(*args)
            self.text_b.xview(*args)
        else:
            self.text_a.xview(*args)

    def _on_scroll_b_x(self, *args):
        """Maneja el scroll horizontal del panel B y sincroniza con A."""
        if self.sync_scroll.get():
            self.text_b.xview(*args)
            self.text_a.xview(*args)
        else:
            self.text_b.xview(*args)

    def _on_mouse_wheel(self, event):
        """Maneja el scroll con la rueda del mouse y sincroniza ambos paneles si la opción está activa."""
        if self.sync_scroll.get():
            # Determinar la dirección del scroll para compatibilidad entre plataformas
            if event.num == 5 or event.delta < 0:
                scroll_units = 2  # Scroll hacia abajo
            else:
                scroll_units = -2 # Scroll hacia arriba
            
            # Aplicar el scroll a ambos paneles
            self.text_a.yview_scroll(scroll_units, "units")
            self.text_b.yview_scroll(scroll_units, "units")
            
            # Devolver "break" para evitar que el evento se propague y cause un doble scroll
            return "break"

    def _on_horizontal_mouse_wheel(self, event):
        """Maneja el scroll horizontal con la rueda del mouse (Shift + Rueda) y sincroniza."""
        if self.sync_scroll.get():
            if event.delta > 0:
                scroll_units = -2 # Scroll hacia la izquierda
            else:
                scroll_units = 2  # Scroll hacia la derecha
            
            # Aplicar el scroll a ambos paneles
            self.text_a.xview_scroll(scroll_units, "units")
            self.text_b.xview_scroll(scroll_units, "units")
            
            return "break"

    def create_report_action_buttons(self, parent):
        """Crear botones de acción de reporte (Guardar y Limpiar Resultados)"""
        report_action_frame = tk.Frame(parent, bg='#ffffff')
        report_action_frame.pack(fill=tk.X, padx=10, pady=10) # Padding consistente
        
        ttk.Button(report_action_frame, text="💾 Guardar Reporte", 
                  style='Modern.TButton',
                  command=self.save_report).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.summary_button = ttk.Button(report_action_frame, text="📊 Resumen", 
                                         style='Modern.TButton', command=self._show_summary_window, state='disabled')
        self.summary_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        ttk.Button(report_action_frame, text="🧹 Limpiar Resultados", 
                  command=self.clear_results).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
        # Botón de Salir
        ttk.Button(parent, text="Salir",
                  command=self.root.destroy).pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5,0))

    def center_window(self):
        """Centrar la ventana en la pantalla"""
        self.root.update_idletasks()
        # Definir un tamaño inicial razonable (ej. 80% del ancho, 75% del alto)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = int(screen_width * 0.8)
        height = int(screen_height * 0.85) # Aumentar altura inicial
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2) - 40 # Subir la ventana 50px
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def add_files(self):
        """Agregar archivos para comparar"""
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos para comparar",
            filetypes=[
                ("Archivos de salida", "*.out *.output *.result"),
                ("Archivos de texto", "*.txt *.log *.csv *.json *.xml *.properties"),
                ("Archivos de código", "*.py *.java *.js *.html *.css *.sql"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.files_listbox.insert(tk.END, os.path.basename(file))
        self._update_compare_button_state()
    
    def on_drop_files(self, event):
        """Manejar archivos arrastrados desde el explorador"""
        if DND_AVAILABLE:
            files = self.root.tk.splitlist(event.data)
        else:
            return
        
        added_count = 0
        for file_path in files:
            if os.path.isfile(file_path) and file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self.files_listbox.insert(tk.END, os.path.basename(file_path))
                added_count += 1
        
        if added_count > 0:
            messagebox.showinfo("Archivos agregados", 
                              f"Se agregaron {added_count} archivo(s) por drag & drop")
        self._update_compare_button_state()
    
    def remove_selected_file(self):
        """Eliminar archivo seleccionado"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            # Eliminar de la lista de archivos seleccionados
            del self.selected_files[index]
            # Eliminar del listbox
            self.files_listbox.delete(index)
        self._update_compare_button_state()
    
    def clear_all_files(self):
        """Limpiar todos los archivos"""
        self.files_listbox.delete(0, tk.END)
        self.selected_files.clear()
        self.processed_file_contents.clear()
        self.all_detailed_diffs.clear() # Limpiar también las diferencias detalladas
        self.original_file_contents.clear()
        # Limpiar también los resultados de la comparación
        self.clear_results()
        self._update_compare_button_state()
    
    def clear_results(self):
        """Limpiar resultados"""
        self.comparison_results.clear()
        for widget in [self.text_a, self.text_b]:
            widget.config(state=tk.NORMAL)
            widget.delete(1.0, tk.END)
            widget.config(state=tk.DISABLED)
        # Limpiar indicadores de cursor
        self.status_label_a.config(text="Ln 1, Col 1")
        self.status_label_b.config(text="Ln 1, Col 1")
        self.title_label_a.config(text="Archivo 1")
        self.title_label_b.config(text="Archivo 2")
    
    def compare_files(self):
        """Comparar archivos seleccionados"""
        if len(self.selected_files) < 2:
            messagebox.showwarning("Advertencia", 
                                 "Selecciona al menos 2 archivos para comparar")
            return
        
        self.compare_button.config(state='disabled') # Deshabilitar durante la comparación
        # Limpiar resultados anteriores
        self.clear_results()
        
        # Mostrar mensaje de procesamiento
        for widget in [self.text_a, self.text_b]:
            widget.config(state=tk.NORMAL)
            widget.insert(tk.END, "🔄 Procesando comparación...\n")
            widget.config(state=tk.DISABLED)
        self.root.update()
        
        # Ejecutar comparación en hilo separado
        thread = threading.Thread(target=self._perform_comparison)
        thread.daemon = True
        thread.start()
    
    def _perform_comparison(self):
        """Realizar la comparación de archivos"""
        # RF2: Crear la carpeta C:\comparador si no existe
        output_dir = Path("C:/zetaOne/comparador")
        output_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        
        try:
            self.comparison_results.clear()
            self.processed_file_contents.clear()
            self.original_file_contents.clear()
            
            self.all_detailed_diffs.clear() # Limpiar diferencias detalladas antes de una nueva comparación
            # Leer y pre-procesar contenido de archivos
            file_contents = {}
            for file_path in self.selected_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_content_str = f.read()
                        self.original_file_contents[file_path] = raw_content_str.splitlines()
                        processed_content_str = raw_content_str
                        if self.ignore_case.get():
                            processed_content_str = processed_content_str.lower()
                        if self.ignore_whitespace.get():
                            processed_content_str = '\n'.join(line.strip() for line in processed_content_str.splitlines())
                        file_contents[file_path] = processed_content_str.splitlines()
                        self.processed_file_contents[file_path] = processed_content_str.splitlines() # Store processed content for UI
                except Exception as e:
                    error_msg = f"❌ Error leyendo {os.path.basename(file_path)}: {str(e)}\n"
                    self.root.after(0, lambda msg=error_msg: self.text_a.insert(tk.END, msg))

                    continue
            
            # Comparar archivos de a pares
            # Asegurarse de que solo se comparan archivos que se pudieron leer
            for i, file1_path in enumerate(self.selected_files):
                for j, file2_path in enumerate(self.selected_files[i+1:], i+1):
                    if file1_path in file_contents and file2_path in file_contents:
                        self._compare_pair(file1_path, file2_path, 
                                           file_contents[file1_path], 
                                           file_contents[file2_path])
            # Si hay resultados de comparación, generar las diferencias detalladas para el primer par
            if self.comparison_results:
                first_comparison = self.comparison_results[0]
                self.all_detailed_diffs = self._generate_detailed_diff_entries(
                    difflib.SequenceMatcher(None, self.processed_file_contents[first_comparison['file1']], self.processed_file_contents[first_comparison['file2']]),
                    self.original_file_contents[first_comparison['file1']], self.original_file_contents[first_comparison['file2']])
            # Mostrar resumen
            self.root.after(0, self._finalize_comparison)
            
        except Exception as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Error", f"Error durante la comparación: {str(err)}"))
    
    def _compare_pair(self, file1_path, file2_path, content1_processed, content2_processed):
        """Comparar un par de archivos"""
        name1 = os.path.basename(file1_path)
        name2 = os.path.basename(file2_path)
        
        # Usar SequenceMatcher para obtener opcodes, que es más útil para la vista de dos paneles
        matcher = difflib.SequenceMatcher(None, content1_processed, content2_processed)
        
        # Almacenar resultados
        comparison_result = {
            'file1': file1_path,
            'file2': file2_path,
            'opcodes': matcher.get_opcodes(),
            'has_differences': matcher.ratio() < 1.0
        }
        self.comparison_results.append(comparison_result)
        
        # Mostrar resultados en la interfaz
        # La visualización se hará una vez para el primer par comparado
        if len(self.comparison_results) == 1:
            self.root.after(0, lambda: self._display_comparison(comparison_result))
    
    def _display_comparison(self, result):
        """Mostrar comparación en la interfaz"""
        # La visualización se hará una vez para el primer par comparado
        if len(self.comparison_results) == 1:
            first_result = self.comparison_results[0]
            content1 = self.processed_file_contents.get(first_result['file1'], [])
            content2 = self.processed_file_contents.get(first_result['file2'], [])
            opcodes = first_result['opcodes']
            
            # Actualizar los títulos de los paneles con los nombres de archivo
            name1 = os.path.basename(first_result['file1'])
            name2 = os.path.basename(first_result['file2'])
            self.title_label_a.config(text=name1)
            self.title_label_b.config(text=name2)

            # Limpiar y habilitar paneles
            for widget in [self.text_a, self.text_b]:
                widget.config(state=tk.NORMAL)
                widget.delete(1.0, tk.END)

            # Poblar paneles y resaltar diferencias
            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'equal':
                    for i in range(i1, i2):
                        self.text_a.insert(tk.END, content1[i] + '\n')
                    for j in range(j1, j2):
                        self.text_b.insert(tk.END, content2[j] + '\n')
                
                elif tag == 'replace':
                    # Diferencia a nivel de palabra para reemplazos
                    num_lines = max(i2 - i1, j2 - j1)
                    for i in range(num_lines):
                        line1 = content1[i1 + i] if i1 + i < i2 else ""
                        line2 = content2[j1 + i] if j1 + i < j2 else ""
                        self._highlight_char_diffs(line1, line2)
                elif tag == 'delete':
                    # Líneas eliminadas en el archivo 1
                    for i in range(i1, i2):
                        self.text_a.insert(tk.END, content1[i] + '\n', ('diff', 'diff_word'))
                        self.text_b.insert(tk.END, '\n', 'diff')
                elif tag == 'insert':
                    # Líneas insertadas en el archivo 2
                    for j in range(j1, j2):
                        self.text_a.insert(tk.END, '\n', 'diff')
                        self.text_b.insert(tk.END, content2[j] + '\n', ('diff', 'diff_word'))

            # Deshabilitar edición
            for widget in [self.text_a, self.text_b]:
                widget.config(state=tk.DISABLED)
            
            # Asegurar que ambos paneles comiencen desde la parte superior
            self.text_a.yview_moveto(0.0)
            self.text_b.yview_moveto(0.0)

    def _highlight_char_diffs(self, line1, line2):
        """
        Compara dos líneas carácter por carácter y resalta las diferencias exactas.
        """
        # 1. Insertar las líneas y aplicar el resaltado de fondo claro a toda la línea
        self.text_a.insert(tk.END, line1 + '\n', 'diff')
        self.text_b.insert(tk.END, line2 + '\n', 'diff')

        # 2. Obtener la posición de la línea recién insertada (es la penúltima)
        # El índice es "line.char", así que extraemos solo la parte de la línea.
        line_num_a = self.text_a.index('end-2l').split('.')[0]
        line_num_b = self.text_b.index('end-2l').split('.')[0]

        # 3. Usar SequenceMatcher a nivel de carácter
        matcher = difflib.SequenceMatcher(None, line1, line2)

        # 4. Aplicar el resaltado intenso a las secciones diferentes
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                # Construir el índice correctamente en formato "linea.columna"

                # Resaltar en el panel A
                start_a = f"{line_num_a}.{i1}"
                end_a = f"{line_num_a}.{i2}"
                self.text_a.tag_add("diff_word", start_a, end_a)
                
                # Resaltar en el panel B
                start_b = f"{line_num_b}.{j1}"
                end_b = f"{line_num_b}.{j2}"
                self.text_b.tag_add("diff_word", start_b, end_b)

    def _finalize_comparison(self):
        """Mostrar resumen final y generar reporte."""
        # Al finalizar, asegurar que la vista de ambos paneles esté al inicio.
        self.text_a.yview_moveto(0.0)
        self.text_b.yview_moveto(0.0)

        self.compare_button.config(state='normal') # Habilitar de nuevo
        self.summary_button.config(state='normal') # Habilitar el botón de resumen

        # Generar reporte automáticamente al finalizar
        if self.comparison_results:
            self.save_report()
    
    def save_report(self):
        """Guardar reporte de diferencias"""
        if not self.comparison_results:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar")
            return
        
        if len(self.selected_files) < 2:
            messagebox.showwarning("Advertencia", "Se requieren al menos dos archivos para generar un reporte detallado.")
            return
        
        # RF2: Asegurar que la carpeta C:\comparador existe
        output_dir = Path("C:/zetaOne/comparador")
        output_dir.mkdir(parents=True, exist_ok=True) # Asegura que la carpeta existe
        
        # RF3: Nombre del archivo determinístico
        if not self.selected_files:
            messagebox.showerror("Error", "No hay archivos seleccionados para determinar el nombre del reporte.")
            return
        # RF3: Nombre del archivo determinístico
        first_file_name_base = os.path.basename(self.selected_files[0]).split('.')[0]
        report_filename = output_dir / f"resCompara_{first_file_name_base}.txt"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # RF4, RF5: ENCABEZADO (metadatos)
                f.write("BEGIN INFORME\n")
                f.write("ENCABEZADO\n")
                f.write(f"FECHA_PROCESO: {now}\n")
                f.write(f"FECHA_EJECUCION: {now}\n")
                
                # Para el reporte determinístico, tomaremos el primer par de la comparación si existe.
                if self.comparison_results:
                    first_comparison = self.comparison_results[0]
                    file1_path = first_comparison['file1']
                    file2_path = first_comparison['file2']
                    name1 = os.path.basename(file1_path)
                    name2 = os.path.basename(file2_path)
                    
                    f.write(f"PRIMER_ARCHIVO: {name1}\n")
                    f.write(f"SEGUNDO_ARCHIVO: {name2}\n")
                    f.write("\n")
                    
                    # RF4, RF5: RESUMEN EJECUTIVO
                    f.write("RESUMEN EJECUTIVO\n")
                    
                    content1_processed = self.processed_file_contents.get(file1_path, [])
                    content2_processed = self.processed_file_contents.get(file2_path, [])

                    content1_original = self.original_file_contents.get(file1_path, [])
                    content2_original = self.original_file_contents.get(file2_path, [])
                    
                    total_lines_file1 = len(content1_processed)
                    total_lines_file2 = len(content2_processed)
                    
                    matcher = difflib.SequenceMatcher(None, content1_processed, content2_processed)
                    # Corrección: Contar el número total de líneas afectadas, no solo los bloques de diferencia.
                    diff_count = 0
                    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
                        if opcode != 'equal':
                            # Sumar el número de líneas en el bloque de diferencia más grande (replace)
                            # o el número de líneas agregadas/eliminadas.
                            diff_count += max(i2 - i1, j2 - j1)

                    f.write(f"Total líneas Archivo1: {total_lines_file1}\n")
                    f.write(f"Total líneas Archivo2: {total_lines_file2}\n")
                    f.write(f"DIFERENCIAS: {diff_count}\n")
                    f.write("Notas: Diferencias encontradas en el contenido de los archivos.\n")
                    f.write("\n")

                    # RF: NUEVA SECCIÓN - RESUMEN DE TIPOS DE DIFERENCIA
                    f.write("RESUMEN DE TIPOS DE DIFERENCIA (Basado en el primer par comparado)\n")
                    diff_summary = self._calculate_diff_summary(matcher, content1_original, content2_original)
                    f.write(f"Líneas agregadas: {diff_summary['lineas_agregadas']}\n")
                    f.write(f"Líneas eliminadas: {diff_summary['lineas_eliminadas']}\n")
                    f.write(f"Modificaciones de fecha: {diff_summary['reemplazos_fecha']}\n")
                    f.write(f"Modificaciones de espaciado: {diff_summary['reemplazos_espacios']}\n")
                    f.write(f"Otras modificaciones de contenido: {diff_summary['reemplazos_otro']}\n")
                    f.write("\n")
                    
                    # RF4, RF5: DATOS TOTALES
                    f.write("DATOS TOTALES\n")
                    f.write(f"Líneas Archivo1: {total_lines_file1}\n")
                    f.write(f"Líneas Archivo2: {total_lines_file2}\n")
                    
                    try:
                        size1_bytes = os.path.getsize(file1_path)
                        size2_bytes = os.path.getsize(file2_path)
                        f.write(f"Tamaño Archivo1: {size1_bytes / 1024:.2f} KB\n")
                        f.write(f"Tamaño Archivo2: {size2_bytes / 1024:.2f} KB\n")
                    except OSError:
                        f.write("Tamaño Archivo1: No disponible\n")
                        f.write("Tamaño Archivo2: No disponible\n")
                    f.write("\n")
                    
                    # RF4, RF5: DETALLE DE DIFERENCIAS
                    f.write("DETALLE DE DIFERENCIAS\n")
                    f.write("Nota: Las diferencias marcadas con [...] incluyen contexto antes y después.\n")
                    
                    if diff_count == 0:
                        f.write("No se encontraron diferencias.\n")
                    else:
                        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
                            if opcode == 'replace':
                                f.write(f"\n--- Diferencia en bloque de líneas (Archivo1: {i1 + 1}-{i2}, Archivo2: {j1 + 1}-{j2}) ---\n")
                                
                                for k_line in range(max(i2 - i1, j2 - j1)):
                                    line1_original_content = content1_original[i1 + k_line] if (i1 + k_line) < i2 else ""
                                    line2_original_content = content2_original[j1 + k_line] if (j1 + k_line) < j2 else ""
                                    
                                    # Report line numbers for both files, indicating if a line is "missing" in one
                                    line_num_1_str = f"LÍNEA {i1 + k_line + 1}" if (i1 + k_line) < i2 else "N/A"
                                    line_num_2_str = f"LÍNEA {j1 + k_line + 1}" if (j1 + k_line) < j2 else "N/A"

                                    f.write(f"{line_num_1_str} (Archivo1) / {line_num_2_str} (Archivo2)\n")
                                    f.write(f"ARCHIVO1: \"{self._get_report_formatted_line(line1_original_content, line2_original_content, True)}\"\n")
                                    f.write(f"ARCHIVO2: \"{self._get_report_formatted_line(line2_original_content, line1_original_content, False)}\"\n")
                                    f.write("DIFERENCIA: Contenido distinto\n")

                            elif opcode == 'delete':
                                f.write(f"\n--- Línea(s) {i1 + 1}-{i2} eliminada(s) de Archivo1 ---\n")
                                for line_num in range(i1, i2):
                                    f.write(f"LÍNEA {line_num + 1}\n")
                                    f.write(f"ARCHIVO1: \"{content1_original[line_num]}\"\n")
                                    f.write("ARCHIVO2: \"\"\n")
                                    f.write("DIFERENCIA: Línea eliminada\n")

                            elif opcode == 'insert':
                                f.write(f"\n--- Línea(s) {j1 + 1}-{j2} agregada(s) en Archivo2 ---\n")
                                for line_num in range(j1, j2):
                                    f.write(f"LÍNEA {line_num + 1} (en Archivo2)\n")
                                    f.write("ARCHIVO1: \"\"\n")
                                    f.write(f"ARCHIVO2: \"{content2_original[line_num]}\"\n")
                                    f.write("DIFERENCIA: Línea agregada\n")

                else:
                    f.write("No se pudieron obtener los contenidos de los archivos para el reporte detallado.\n")
                
                f.write("\nFIN DEL INFORME\n")
            
            messagebox.showinfo("Éxito", f"Reporte guardado exitosamente en:\n{report_filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el reporte: {str(e)}")

    def _generate_detailed_diff_entries(self, matcher, content1_original, content2_original):
        """
        Genera una lista de diccionarios, cada uno representando una diferencia detallada
        a nivel de línea, incluyendo información de diferencias a nivel de carácter para reemplazos.
        """
        detailed_diffs = []

        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == 'replace':
                for k_line in range(max(i2 - i1, j2 - j1)):
                    line1 = content1_original[i1 + k_line] if (i1 + k_line) < i2 else ""
                    line2 = content2_original[j1 + k_line] if (j1 + k_line) < j2 else ""
                    
                    diff_type = self._classify_difference(line1, line2)
                    
                    char_diff_info = []
                    char_matcher = difflib.SequenceMatcher(None, line1, line2)
                    for tag_char, c1_start, c1_end, c2_start, c2_end in char_matcher.get_opcodes():
                        if tag_char != 'equal':
                            char_diff_info.append({
                                'tag': tag_char,
                                'file1_char_start': c1_start,
                                'file1_char_end': c1_end,
                                'file2_char_start': c2_start,
                                'file2_char_end': c2_end
                            })

                    detailed_diffs.append({
                        'type': diff_type,
                        'opcode': opcode,
                        'file1_line_num': i1 + k_line + 1 if (i1 + k_line) < i2 else "N/A",
                        'file2_line_num': j1 + k_line + 1 if (j1 + k_line) < j2 else "N/A",
                        'file1_content': line1,
                        'file2_content': line2,
                        'char_diff_info': char_diff_info
                    })

            elif opcode == 'delete':
                for k_line in range(i1, i2):
                    detailed_diffs.append({
                        'type': 'eliminada',
                        'opcode': opcode,
                        'file1_line_num': k_line + 1,
                        'file2_line_num': "N/A",
                        'file1_content': content1_original[k_line],
                        'file2_content': "",
                        'char_diff_info': []
                    })
            elif opcode == 'insert':
                for k_line in range(j1, j2):
                    detailed_diffs.append({
                        'type': 'agregada',
                        'opcode': opcode,
                        'file1_line_num': "N/A",
                        'file2_line_num': k_line + 1,
                        'file1_content': "",
                        'file2_content': "", # No content in file1 for an insert
                        'char_diff_info': []
                    })
        return detailed_diffs

    def _calculate_diff_summary(self, matcher, content1_original, content2_original): # This method is for the report
        """Calcula un resumen de los tipos de diferencias encontradas."""
        summary = {
            'reemplazos_fecha': 0,
            'reemplazos_espacios': 0,
            'reemplazos_otro': 0,
            'lineas_agregadas': 0,
            'lineas_eliminadas': 0,
        }
        
        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == 'replace':
                # Para simplificar, clasificamos el bloque 'replace' basado en la primera línea del bloque.
                line1 = content1_original[i1] if i1 < i2 else ""
                line2 = content2_original[j1] if j1 < j2 else ""
                diff_type = self._classify_difference(line1, line2)

                # Contar todas las líneas dentro del bloque de reemplazo
                num_lines_in_block = max(i2 - i1, j2 - j1)
                summary[f'reemplazos_{diff_type}'] += num_lines_in_block
            elif opcode == 'delete':
                summary['lineas_eliminadas'] += (i2 - i1)
            elif opcode == 'insert':
                summary['lineas_agregadas'] += (j2 - j1)

        return summary

    def _classify_difference(self, line1, line2):
        """
        Clasifica el tipo de diferencia entre dos líneas.
        Utiliza heurísticas para identificar si es una diferencia de fecha, espaciado u otra.
        Retorna 'fecha', 'espacios', 'otro'.
        """
        import re

        # Heurística 1: Diferencia de espaciado
        # Si las líneas son iguales después de quitar espacios al inicio y al final, es una diferencia de espaciado.
        if line1.strip() == line2.strip() and line1 != line2:
            # Asegurarse de que la diferencia sea *solo* de espaciado
            # Si las versiones procesadas (ignorando espacios) son iguales, entonces es solo espaciado.
            processed_line1 = line1.strip()
            processed_line2 = line2.strip()
            if self.ignore_case.get():
                processed_line1 = processed_line1.lower()
                processed_line2 = processed_line2.lower()
            
            if processed_line1 == processed_line2:
                return 'espacios'
            # Si no, es otro tipo de diferencia que casualmente tiene espaciado distinto
            return 'otro'

        # Heurística 2: Diferencia de fecha
        # Regex para formatos comunes de fecha (dd/mm/yyyy, yyyy-mm-dd, etc.)
        # Mejorar la regex para ser más robusta y capturar fechas en diferentes contextos
        date_regex = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        
        # Buscar fechas en ambas líneas
        dates1 = re.findall(date_regex, line1)
        dates2 = re.findall(date_regex, line2)

        # Si encontramos al menos una fecha en cada línea y son diferentes, lo clasificamos como fecha
        if dates1 and dates2 and any(d1 != d2 for d1, d2 in zip(dates1, dates2)):
            # Para ser más precisos, verificamos si la *única* diferencia significativa
            # entre las líneas (ignorando espacios y mayúsculas) es la fecha.
            # Esto es complejo de hacer perfectamente sin un parser de texto más avanzado.
            # Por ahora, si hay fechas y son diferentes, y las líneas no son idénticas,
            # lo consideramos una diferencia de fecha.
            if line1 != line2: # Asegurarse de que realmente hay una diferencia
                return 'fecha'

        return 'otro'

    def _show_summary_window(self):
        """Muestra una nueva ventana con el resumen detallado de las diferencias."""
        if not self.all_detailed_diffs:
            messagebox.showinfo("Resumen", "No hay diferencias para mostrar en el resumen.")
            return

        summary_window = tk.Toplevel(self.root)
        summary_window.title("Resumen de Diferencias Detallado")
        summary_window.geometry("1000x700")
        summary_window.transient(self.root)
        summary_window.grab_set()

        # Frame para los botones de resumen por tipo
        summary_counts_frame = ttk.LabelFrame(summary_window, text="Resumen por Tipo", padding=10)
        summary_counts_frame.pack(fill=tk.X, padx=10, pady=5)

        # Calcular los conteos de resumen a partir de self.all_detailed_diffs
        current_summary_counts = {
            'reemplazos_fecha': 0,
            'reemplazos_espacios': 0,
            'reemplazos_otro': 0,
            'lineas_agregadas': 0,
            'lineas_eliminadas': 0,
        }
        for diff in self.all_detailed_diffs:
            if diff['opcode'] == 'replace':
                current_summary_counts[f'reemplazos_{diff["type"]}'] += 1
            elif diff['opcode'] == 'delete':
                current_summary_counts['lineas_eliminadas'] += 1
            elif diff['opcode'] == 'insert':
                current_summary_counts['lineas_agregadas'] += 1

        categories = {
            'Modificaciones de fecha': ('reemplazos_fecha', '#FFEBEE'),
            'Modificaciones de espaciado': ('reemplazos_espacios', '#FFFDE7'),
            'Otras modificaciones de contenido': ('reemplazos_otro', '#E3F2FD'),
            'Líneas agregadas': ('lineas_agregadas', '#E8F5E9'),
            'Líneas eliminadas': ('lineas_eliminadas', '#FFEBEE')
        }

        self.detailed_display_text = scrolledtext.ScrolledText(summary_window, wrap=tk.NONE, font=('Consolas', 9), bg='#f8f9fa', borderwidth=0, highlightthickness=0)
        self.detailed_display_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.detailed_display_text.config(state=tk.DISABLED)

        # Definir tags para resaltar en la vista detallada
        self.detailed_display_text.tag_configure("diff_word", background="#F44336", foreground="white", font=('Consolas', 9, 'bold'))
        self.detailed_display_text.tag_configure("line_num", foreground="#2196F3", font=('Consolas', 9, 'bold'))
        self.detailed_display_text.tag_configure("header", foreground="#2196F3", font=('Consolas', 9, 'bold'))
        self.detailed_display_text.tag_configure("file1_line", foreground="#D32F2F") # Rojo para contenido de archivo 1
        self.detailed_display_text.tag_configure("file2_line", foreground="#388E3C") # Verde para contenido de archivo 2

        for text_label, (key, bg_color) in categories.items():
            count = current_summary_counts[key]
            btn = ttk.Button(summary_counts_frame, text=f"{text_label}: {count}",
                             command=lambda k=key: self._display_detailed_diffs_in_summary(k, summary_window))
            btn.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Botón para mostrar todas las diferencias
        ttk.Button(summary_counts_frame, text="Mostrar Todas", 
                   command=lambda: self._display_detailed_diffs_in_summary(None, summary_window)).pack(side=tk.RIGHT, padx=5, pady=2)

        # Mostrar todas las diferencias inicialmente
        self._display_detailed_diffs_in_summary(None, summary_window)

        summary_window.protocol("WM_DELETE_WINDOW", lambda: self._on_summary_close(summary_window))

    def _on_summary_close(self, summary_window):
        """Libera el grab y destruye la ventana de resumen."""
        summary_window.grab_release()
        summary_window.destroy()

    def _display_detailed_diffs_in_summary(self, diff_type_filter, parent_window):
        """
        Muestra las diferencias detalladas en el widget ScrolledText de la ventana de resumen,
        filtrando por tipo si se especifica.
        """
        self.detailed_display_text.config(state=tk.NORMAL)
        self.detailed_display_text.delete(1.0, tk.END)

        if diff_type_filter:
            display_title = f"--- Detalles para: {diff_type_filter.replace('reemplazos_', '').replace('_', ' ').title()} ---\n\n"
        else:
            display_title = "--- Detalles de Todas las Diferencias ---\n\n"
        self.detailed_display_text.insert(tk.END, display_title, "header")

        for diff_entry in self.all_detailed_diffs:
            # Filtrar por el tipo de diferencia
            match = False
            if diff_type_filter is None: # Mostrar todas
                match = True
            elif diff_entry['opcode'] == 'replace' and f'reemplazos_{diff_entry["type"]}' == diff_type_filter:
                match = True
            elif diff_entry['opcode'] == 'delete' and diff_type_filter == 'lineas_eliminadas':
                match = True
            elif diff_entry['opcode'] == 'insert' and diff_type_filter == 'lineas_agregadas':
                match = True
            
            if match:
                self.detailed_display_text.insert(tk.END, f"Línea Archivo1: {diff_entry['file1_line_num']} | Línea Archivo2: {diff_entry['file2_line_num']}\n", "line_num")
                
                # Display File 1 content
                self.detailed_display_text.insert(tk.END, "ARCHIVO1: ", "file1_line")
                start_idx_file1 = self.detailed_display_text.index(tk.END + "-1c") # Get current end index
                self.detailed_display_text.insert(tk.END, f"{diff_entry['file1_content']}\n")
                if diff_entry['opcode'] == 'replace':
                    for char_diff in diff_entry['char_diff_info']:
                        if char_diff['tag'] != 'equal':
                            self.detailed_display_text.tag_add("diff_word", 
                                                               f"{start_idx_file1}+{char_diff['file1_char_start']}c", 
                                                               f"{start_idx_file1}+{char_diff['file1_char_end']}c")
                elif diff_entry['opcode'] == 'delete':
                    self.detailed_display_text.tag_add("diff_word", start_idx_file1, tk.END + "-1c")

                # Display File 2 content
                self.detailed_display_text.insert(tk.END, "ARCHIVO2: ", "file2_line")
                start_idx_file2 = self.detailed_display_text.index(tk.END + "-1c") # Get current end index
                self.detailed_display_text.insert(tk.END, f"{diff_entry['file2_content']}\n")
                if diff_entry['opcode'] == 'replace':
                    for char_diff in diff_entry['char_diff_info']:
                        if char_diff['tag'] != 'equal':
                            self.detailed_display_text.tag_add("diff_word", 
                                                               f"{start_idx_file2}+{char_diff['file2_char_start']}c", 
                                                               f"{start_idx_file2}+{char_diff['file2_char_end']}c")
                elif diff_entry['opcode'] == 'insert':
                    self.detailed_display_text.tag_add("diff_word", start_idx_file2, tk.END + "-1c")

                self.detailed_display_text.insert(tk.END, "----------------------------------------\n\n")

        self.detailed_display_text.config(state=tk.DISABLED)

    def _get_report_formatted_line(self, line_content, other_line_content, is_file1_line, num_words_context=3, max_context_chars=60, chars_after_diff=10):
        """
        Formatea una línea para el reporte, marcando las diferencias con corchetes
        y añadiendo contexto antes y después.
        
        Args:
            line_content (str): La línea actual del archivo que se está formateando.
            other_line_content (str): La línea correspondiente del otro archivo (para la comparación).
            is_file1_line (bool): True si line_content es del archivo 1, False si es del archivo 2.
            num_words_context (int): Número máximo de palabras de contexto antes de la diferencia.
            max_context_chars (int): Número máximo de caracteres de contexto a mostrar antes de la diferencia.
            chars_after_diff (int): Número de caracteres de contexto a mostrar después de la diferencia.
        Returns:
            str: La línea formateada con marcadores de diferencia y contexto.
        """
        if not line_content and not other_line_content:
            return ""
        
        # Usar SequenceMatcher a nivel de carácter para encontrar las diferencias exactas
        matcher = difflib.SequenceMatcher(None, line_content, other_line_content)
        
        first_diff_start_idx = -1
        first_diff_end_idx = -1
        
        # Encontrar el primer segmento de diferencia para determinar el punto de inicio del contexto
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                # Los índices i1, i2 son para line_content, j1, j2 para other_line_content
                # Si estamos formateando line_content (que es del archivo 1), usamos i1, i2.
                # Si estamos formateando line_content (que es del archivo 2), usamos j1, j2.
                if is_file1_line:
                    first_diff_start_idx = i1
                    first_diff_end_idx = i2
                else:
                    first_diff_start_idx = j1
                    first_diff_end_idx = j2
                break # Solo nos interesa la primera diferencia para calcular el contexto inicial

        if first_diff_start_idx == -1: # No se encontraron diferencias a nivel de carácter (debería ser raro en un bloque 'replace')
            return line_content # Si no hay diferencias, devolver la línea completa sin marcar

        # Determinar el inicio del contexto
        # Primero, intentamos retroceder por palabras
        temp_context_start = first_diff_start_idx
        words_found = 0
        while temp_context_start > 0 and words_found < num_words_context:
            # Retroceder hasta el inicio de la palabra anterior
            search_pos = temp_context_start - 1
            while search_pos > 0 and not line_content[search_pos].isspace():
                search_pos -= 1
            # Retroceder a través de los espacios en blanco antes de esa palabra
            while search_pos > 0 and line_content[search_pos].isspace():
                search_pos -= 1
            # Si no retrocedimos nada, salimos para evitar bucle infinito
            if search_pos == temp_context_start - 1:
                break
            temp_context_start = search_pos + 1 if search_pos > 0 else 0
            words_found += 1
        
        # Aplicar el límite máximo de caracteres de contexto
        context_start_char = max(temp_context_start, first_diff_start_idx - max_context_chars)
        context_start_char = max(0, context_start_char) # Asegurarse de no ser negativo

        # Construir la cadena de salida
        output_string = ""
        if context_start_char > 0:
            output_string += "..." # Indicar que hay contenido truncado antes
        
        # Añadir el contexto antes de la diferencia
        output_string += line_content[context_start_char:first_diff_start_idx]
        
        # Añadir la parte diferente con marcadores
        output_string += f"[{line_content[first_diff_start_idx:first_diff_end_idx]}]"
        
        # Añadir algunos caracteres de contexto después de la diferencia
        after_diff_context_end = min(len(line_content), first_diff_end_idx + chars_after_diff)
        output_string += line_content[first_diff_end_idx:after_diff_context_end]
        
        if after_diff_context_end < len(line_content):
            output_string += "..." # Indicar que hay contenido truncado después
            
        return output_string
    
    def _update_compare_button_state(self):
        """Actualiza el estado del botón 'COMPARAR' basado en el número de archivos seleccionados."""
        if len(self.selected_files) >= 2:
            self.compare_button.config(state='normal')
        else:
            self.compare_button.config(state='disabled')
        # El botón de resumen se habilita solo después de una comparación exitosa
        self.summary_button.config(state='disabled')

def main():
    """Función principal"""
    # Solución Final y Definitiva: La forma correcta de inicializar para el
    # paquete 'tkinterdnd2' es usar la clase Tk() que provee el propio módulo.
    if DND_AVAILABLE:
        root = tkinterdnd2.Tk()
    else:
        root = tk.Tk()

    app = ModernFileComparator(root)
    root.mainloop()

if __name__ == "__main__":
    main()