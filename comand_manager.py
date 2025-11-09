import sys
import json
import os
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QTextEdit, QLineEdit, QPushButton,
    QDockWidget, QToolBar, QToolButton, QMessageBox, QInputDialog,
    QTabWidget, QListWidgetItem, QStyle, QFormLayout, QComboBox, QLabel,
    QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt, QProcess, QSize, QObject, Signal
from PySide6.QtGui import QIcon, QFont, QAction

# --- Estilo Moderno Oscuro (Dark Theme QSS) ---
DARK_THEME_QSS = """
QWidget {
    background-color: #2b2b2b;
    color: #f0f0f0;
    font-size: 10pt;
}
QMainWindow {
    background-color: #2b2b2b;
}
QDockWidget {
    background-color: #3c3c3c;
}
QDockWidget::title {
    background-color: #353535;
    padding: 4px;
    border-radius: 4px;
}
QListWidget {
    background-color: #3c3c3c;
    border: none;
    padding: 5px;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
}
QListWidget::item:hover {
    background-color: #4a4a4a;
}
QListWidget::item:selected {
    background-color: #0078d7;
    color: #ffffff;
}
QTextEdit {
    background-color: #252525;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 5px;
    font-family: "Consolas", "Courier New", monospace;
}
QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    font-family: "Consolas", "Courier New", monospace;
}
QLineEdit:read-only {
    background-color: #252525;
    border: 1px solid #444;
}
QPushButton, QToolButton {
    background-color: #0078d7;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}
QPushButton:hover, QToolButton:hover {
    background-color: #008afb;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #006acb;
}
QToolButton {
    padding: 6px;
}
QToolBar {
    background-color: #3c3c3c;
    border: none;
    padding: 4px;
}
/* Barra de herramientas de comandos (central) */
QToolBar#CommandToolBar {
    background-color: #333333;
    border-bottom: 1px solid #444;
    padding: 2px;
}
QToolBar#CommandToolBar QToolButton {
    font-size: 9pt;
    padding: 5px 10px;
    background-color: #3a3a3a;
}
QToolBar#CommandToolBar QToolButton:hover { background-color: #4a4a4a; }

/* Barras de herramientas de gestión (docks) */
QToolBar#DockToolBar {
    background-color: #333333;
    padding: 2px;
}
QToolBar#DockToolBar QToolButton {
    font-size: 9pt;
    padding: 5px 10px;
    background-color: #3a3a3a;
    width: 100%;
}
QToolBar#DockToolBar QToolButton:hover { background-color: #4a4a4a; }

QTabWidget::pane {
    border: 1px solid #444;
    border-top: none;
}
QTabBar::tab {
    background: #3c3c3c;
    padding: 8px 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #2b2b2b;
    border: 1px solid #444;
    border-bottom: 1px solid #2b2b2b;
}
QTabBar::tab:!selected {
    background: #444;
}
/* Botón de cerrar pestaña (para la pestaña de edición) */
QTabBar::close-button {
    /* (Usaremos el icono estándar de PySide) */
    subcontrol-position: right;
    border: none;
    padding: 2px;
}
QTabBar::close-button:hover {
    background-color: #4a4a4a;
}

QScrollBar:vertical {
    border: none;
    background: #2b2b2b;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #555;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
QFormLayout {
    padding: 5px;
    background-color: #333333;
    border-radius: 4px;
}
QLabel {
    padding: 5px 0px;
}
QComboBox {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    border: 1px solid #555;
    selection-background-color: #0078d7;
}
QSplitter::handle {
    background-color: #2b2b2b;
    height: 4px;
}
QSplitter::handle:hover {
    background-color: #0078d7;
}
"""

COMMANDS_FILE = "commands.json"
VARIABLES_FILE = "variables.json"


# --- Helper para el editor de valores (Fase 4) ---
class ValueEditorSignals(QObject):
    # Señal que se emite cuando un valor es añadido o eliminado
    # (nombre_variable, nuevo_valor, es_añadido)
    valueChanged = Signal(str, str, bool)

class CommandManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Manager GUI")
        self.setGeometry(100, 100, 1400, 800)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)

        self.variables_db = self.load_data(VARIABLES_FILE, self.get_default_variables)
        self.commands_db = self.load_data(COMMANDS_FILE, self.get_default_commands)

        self.current_template = ""
        self.dynamic_variable_widgets = {}
        
        self.is_editing_command = False
        self.current_edit_category = ""
        self.current_edit_command_name = ""
        
        # --- NUEVO: Pestañas de edición y señales ---
        self.editor_tabs = {} # Almacena las pestañas de edición de variables
        self.value_editor_signals = ValueEditorSignals()
        # -------------------------------------------

        self.setup_ui()
        self.init_signals()
        self.refresh_right_dock()
        
        # Seleccionar la primera categoría y comando si existen
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)
            list_widget = self.command_stack.widget(0)
            if list_widget and list_widget.count() > 0:
                list_widget.setCurrentRow(0)
                self.on_command_selected(list_widget.item(0))


    # --- Lógica de Carga y Guardado de Datos ---
    def load_data(self, file_name, default_data_func):
        """Carga un archivo JSON. Si no existe, lo crea con datos por defecto."""
        if not os.path.exists(file_name):
            print(f"Advertencia: No se encontró '{file_name}'. Creando archivo por defecto.")
            default_data = default_data_func()
            self.save_data(file_name, default_data)
            return default_data
        
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar '{file_name}': {e}")
            QMessageBox.critical(self, "Error de Carga",
                                 f"No se pudo cargar el archivo '{file_name}'.\n{e}")
            return default_data_func() # Carga los valores por defecto en caso de error

    def save_data(self, file_name, data):
        """Guarda los datos (diccionario) en un archivo JSON."""
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar '{file_name}': {e}")
            QMessageBox.critical(self, "Error de Guardado",
                                 f"No se pudo guardar el archivo '{file_name}'.\n{e}")

    def get_default_variables(self):
        """Define las variables globales por defecto si 'variables.json' no existe."""
        return {
            "TU_USUARIO": {"descripcion": "Usuario de GitHub o Docker Hub", "valores": ["ariel", "juan", "pedro"]},
            "IMAGEN_REPO": {"descripcion": "Nombre del repositorio en el registry", "valores": ["mi-app", "mi-backend"]},
            "IMAGEN_LOCAL": {"descripcion": "Nombre de la imagen local (ej: app:tag)", "valores": ["mi-app:latest", "backend:1.0"]},
            "CONTENEDOR_ID": {"descripcion": "ID o Nombre de un contenedor", "valores": ["contenedor_1", "db_postgres"]},
            "ID_O_TAG": {"descripcion": "ID o Tag de una imagen", "valores": ["imagen_id", "mi-app:latest"]}
        }
    
    def get_default_commands(self):
        """Define los comandos por defecto si 'commands.json' no existe."""
        return {
            "Contenedores": {
                "Ver activos": { "template": "docker ps", "info": "Muestra contenedores en ejecución." },
                "Ver todos": { "template": "docker ps -a", "info": "Muestra todos los contenedores." },
                "Detener un contenedor": { "template": "docker stop [CONTENEDOR_ID]", "info": "Detiene un contenedor." }
            },
            "Imágenes": {
                "Listar imágenes": { "template": "docker images", "info": "Muestra imágenes locales." }
            },
            "Push a GitHub (GHCR)": {
                "1. Login en GHCR": { "template": "docker login ghcr.io -u [TU_USUARIO]", "info": "Inicia sesión en GHCR." },
                "2. Etiquetar (Tag) Imagen": { "template": "docker tag [IMAGEN_LOCAL] ghcr.io/[TU_USUARIO]/[IMAGEN_REPO]", "info": "Etiqueta una imagen local." }
            }
        }
    # --- Fin de la lógica de Datos ---

    def setup_ui(self):
        """Configura la UI principal."""
        self.setup_toolbar()
        self.setup_docks()
        
        # --- Stack Central de Vistas ---
        self.main_stack = QStackedWidget()
        
        # Vista 0: Ejecución
        self.execution_widget = QWidget()
        self.setup_execution_ui(self.execution_widget)
        self.main_stack.addWidget(self.execution_widget)
        
        # Vista 1: Editor de Comandos
        self.editor_widget = QWidget()
        self.setup_editor_ui(self.editor_widget)
        self.main_stack.addWidget(self.editor_widget)

        self.setCentralWidget(self.main_stack)

    def setup_toolbar(self):
        """Configura la barra de herramientas superior."""
        toolbar = QToolBar("Herramientas Rápidas")
        self.addToolBar(toolbar)
        # (Aquí podríamos añadir un botón global para 'Gestionar Variables' si quisiéramos)

    def setup_docks(self):
        """Configura los Docks izquierdo y derecho."""
        # --- Dock Izquierdo (Categorías) ---
        self.left_dock = QDockWidget("Categorías", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        
        # Widget contenedor del dock izquierdo
        left_dock_container = QWidget()
        ld_layout = QVBoxLayout(left_dock_container)
        ld_layout.setContentsMargins(0, 0, 0, 0)
        ld_layout.setSpacing(2)

        # Barra de herramientas para categorías
        cat_toolbar = QToolBar()
        cat_toolbar.setObjectName("DockToolBar")
        
        self.add_cat_button = QToolButton()
        self.add_cat_button.setText("Añadir Categoría (+)")
        self.add_cat_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.add_cat_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.del_cat_button = QToolButton()
        self.del_cat_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.del_cat_button.setToolTip("Eliminar Categoría Seleccionada")

        cat_toolbar.addWidget(self.add_cat_button)
        cat_toolbar.addWidget(self.del_cat_button)
        ld_layout.addWidget(cat_toolbar)

        # Lista de categorías
        self.category_list = QListWidget()
        self.category_list.addItems(self.commands_db.keys())
        ld_layout.addWidget(self.category_list)
        
        self.left_dock.setWidget(left_dock_container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # --- Dock Derecho (Info en Vivo y Banco de Variables) ---
        self.right_dock = QDockWidget("Vistas en Vivo", self)
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        right_dock_widget = QWidget()
        right_layout = QVBoxLayout(right_dock_widget)
        self.refresh_button = QPushButton("Actualizar Vistas")
        right_layout.addWidget(self.refresh_button)

        self.info_tabs = QTabWidget()
        self.info_tabs.setTabsClosable(True) # Permitir cerrar pestañas dinámicas
        
        self.containers_view = QTextEdit()
        self.containers_view.setReadOnly(True)
        self.images_view = QTextEdit()
        self.images_view.setReadOnly(True)
        
        # --- NUEVO: Pestaña de Variables (Fase 4) ---
        self.variables_tab_widget = QWidget()
        variables_layout = QVBoxLayout(self.variables_tab_widget)
        
        self.variable_bank_list = QListWidget()
        self.variable_bank_list.setToolTip("Doble clic para insertar variable en plantilla.\nSelecciona una para gestionar sus valores.")
        self.variable_bank_list.addItems(sorted(self.variables_db.keys())) # Poblar
        
        self.manage_values_button = QPushButton("Gestionar Valores de Variable")
        self.manage_values_button.setEnabled(False) # Desactivado hasta seleccionar
        
        variables_layout.addWidget(self.variable_bank_list)
        variables_layout.addWidget(self.manage_values_button)
        # ---------------------------------------------
        
        self.info_tabs.addTab(self.containers_view, "Contenedores")
        self.info_tabs.addTab(self.images_view, "Imágenes")
        self.info_tabs.addTab(self.variables_tab_widget, "Variables")
        # Asegurarnos de que las pestañas base no se puedan cerrar
        self.info_tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)
        self.info_tabs.tabBar().setTabButton(1, QTabBar.ButtonPosition.RightSide, None)
        self.info_tabs.tabBar().setTabButton(2, QTabBar.ButtonPosition.RightSide, None)
        
        right_layout.addWidget(self.info_tabs)
        self.right_dock.setWidget(right_dock_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

    def setup_execution_ui(self, parent_widget):
        """Configura la vista de ejecución de comandos."""
        main_layout = QVBoxLayout(parent_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Barra de herramientas de Comandos ---
        cmd_toolbar = QToolBar()
        cmd_toolbar.setObjectName("CommandToolBar")
        
        self.add_cmd_button = QToolButton()
        self.add_cmd_button.setText("Añadir (+)")
        self.add_cmd_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.add_cmd_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        
        self.edit_cmd_button = QToolButton()
        self.edit_cmd_button.setText("Editar (E)")
        self.edit_cmd_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.edit_cmd_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        
        self.del_cmd_button = QToolButton()
        self.del_cmd_button.setText("Eliminar (-)")
        self.del_cmd_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.del_cmd_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        cmd_toolbar.addWidget(self.add_cmd_button)
        cmd_toolbar.addWidget(self.edit_cmd_button)
        cmd_toolbar.addWidget(spacer)
        cmd_toolbar.addWidget(self.del_cmd_button)
        main_layout.addWidget(cmd_toolbar)
        # ----------------------------------------------

        # 1. StackedWidget
        self.command_stack = QStackedWidget()
        self.rebuild_command_stack() # Rellenar el stack desde la DB
        main_layout.addWidget(self.command_stack)

        # 2. Área de información
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setFixedHeight(120)
        self.info_display.setHtml("<h3>Selecciona un comando...</h3>")
        main_layout.addWidget(self.info_display)

        # 3. Panel de Configuración de Variables
        self.setup_variable_config_panel()
        main_layout.addWidget(self.variable_config_panel)

        # 4. Campo de entrada (Vista Previa) y Botones
        input_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Selecciona un comando para ver la vista previa...")
        self.command_input.setReadOnly(True)

        self.config_button = QToolButton()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        self.config_button.setIcon(icon)
        self.config_button.setToolTip("Configurar variables del comando")
        self.config_button.setVisible(False) 

        self.run_button = QPushButton("Ejecutar")
        
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.config_button)
        input_layout.addWidget(self.run_button)
        main_layout.addLayout(input_layout)

        # 5. Consola de salida
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        main_layout.addWidget(self.console_output)

    def setup_editor_ui(self, parent_widget):
        """Configura la vista del editor de comandos."""
        editor_layout = QVBoxLayout(parent_widget)
        
        self.editor_title = QLabel("<h2>Añadir Nuevo Comando</h2>")
        self.editor_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        editor_layout.addWidget(self.editor_title)
        
        form_layout = QFormLayout()
        
        self.editor_cmd_name = QLineEdit()
        self.editor_cmd_template = QLineEdit()
        self.editor_cmd_template.setPlaceholderText("Ej: docker ps -a --format '[FORMATO]'")
        self.editor_cmd_info = QTextEdit()
        self.editor_cmd_info.setFixedHeight(100)
        
        form_layout.addRow("Nombre del Comando:", self.editor_cmd_name)
        form_layout.addRow("Plantilla (Template):", self.editor_cmd_template)
        form_layout.addRow("Información (Ayuda):", self.editor_cmd_info)
        
        editor_layout.addLayout(form_layout)
        
        # Botones de Guardar/Cancelar
        button_layout = QHBoxLayout()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.editor_save_button = QPushButton("Guardar")
        self.editor_cancel_button = QPushButton("Cancelar")
        
        button_layout.addWidget(spacer)
        button_layout.addWidget(self.editor_cancel_button)
        button_layout.addWidget(self.editor_save_button)
        
        editor_layout.addLayout(button_layout)
        editor_layout.addStretch() # Empuja todo hacia arriba

    def rebuild_command_stack(self):
        """Limpia y reconstruye el command_stack desde self.commands_db."""
        # Limpiar stack actual
        while self.command_stack.count() > 0:
            widget = self.command_stack.widget(0)
            self.command_stack.removeWidget(widget)
            if widget:
                widget.deleteLater()
                
        # Reconstruir
        for category in self.commands_db:
            command_list_widget = QListWidget()
            for cmd_name in self.commands_db[category]:
                item = QListWidgetItem(cmd_name)
                # Guardamos la plantilla, ya no es necesario, pero lo dejamos
                item.setData(Qt.ItemDataRole.UserRole, self.commands_db[category][cmd_name]["template"])
                command_list_widget.addItem(item)
            self.command_stack.addWidget(command_list_widget)
            # Conectamos la señal
            command_list_widget.itemClicked.connect(self.on_command_selected)
            command_list_widget.itemDoubleClicked.connect(self.on_command_double_clicked)

    def init_signals(self):
        """Conecta todas las señales y slots."""
        # Señales de Ejecución
        self.category_list.currentRowChanged.connect(self.command_stack.setCurrentIndex)
        self.run_button.clicked.connect(self.execute_command)
        self.command_input.returnPressed.connect(self.execute_command)
        self.refresh_button.clicked.connect(self.refresh_right_dock)
        self.config_button.clicked.connect(self.toggle_variable_panel)

        # Señales de Edición de Comandos (Fase 3)
        self.add_cat_button.clicked.connect(self.on_add_category)
        self.del_cat_button.clicked.connect(self.on_delete_category)
        self.add_cmd_button.clicked.connect(self.on_add_command)
        self.edit_cmd_button.clicked.connect(self.on_edit_command)
        self.del_cmd_button.clicked.connect(self.on_delete_command)
        self.editor_save_button.clicked.connect(self.on_save_command)
        self.editor_cancel_button.clicked.connect(self.on_cancel_edit)
        self.variable_bank_list.itemDoubleClicked.connect(self.on_variable_bank_double_clicked)

        # --- NUEVAS SEÑALES (Fase 4) ---
        
        # Activa el botón "Gestionar" cuando se selecciona una variable
        self.variable_bank_list.currentItemChanged.connect(
            lambda: self.manage_values_button.setEnabled(self.variable_bank_list.currentItem() is not None)
        )
        # Abre la pestaña de edición de valores
        self.manage_values_button.clicked.connect(self.on_manage_variable_values)
        
        # Maneja el cierre de pestañas (tanto por 'x' como por botón)
        self.info_tabs.tabCloseRequested.connect(self.on_editor_tab_closed)
        
        # Conecta la señal personalizada para la actualización en vivo
        self.value_editor_signals.valueChanged.connect(self.on_variable_value_changed)


    # --- Slots de Edición (Fase 3) ---

    def on_command_selected(self, item):
        """Se activa al hacer clic en un comando de la lista central."""
        if not item:
            self.info_display.clear()
            self.command_input.clear()
            self.variable_config_panel.hide()
            self.config_button.setVisible(False)
            return

        cmd_name = item.text()
        current_category_index = self.command_stack.currentIndex()
        if current_category_index < 0: return
        category_name = self.category_list.item(current_category_index).text()
        
        # Verificar que el comando todavía existe (puede haber sido eliminado)
        if category_name not in self.commands_db or cmd_name not in self.commands_db[category_name]:
            return # El comando ya no existe, probablemente se está eliminando

        cmd_data = self.commands_db[category_name][cmd_name]
        
        self.info_display.setHtml(f"<h3>{cmd_name}</h3><p>{cmd_data['info']}</p>")
        self.current_template = cmd_data["template"]
        
        self.build_variable_widgets() 
        self.update_command_preview() 
        self.variable_config_panel.hide()

    def on_command_double_clicked(self, item):
        """Doble clic en un comando es un atajo para Editar."""
        self.on_edit_command()

    def on_add_category(self):
        """Añade un QLineEdit temporal a la lista de categorías."""
        # Creamos el editor in-place
        editor = QLineEdit()
        editor.setPlaceholderText("Nombre de la nueva categoría...")
        
        # Creamos un item temporal en la lista
        item = QListWidgetItem()
        self.category_list.addItem(item)
        self.category_list.setItemWidget(item, editor)
        
        # Ponemos el foco y nos preparamos para el "Enter"
        editor.setFocus()
        
        # Conectamos la señal de "edición terminada" (Enter o perder foco)
        editor.editingFinished.connect(lambda: self.on_finish_category_add(item, editor))

    def on_finish_category_add(self, item, editor):
        """Se llama cuando el usuario pulsa Enter en el editor de categoría."""
        new_name = editor.text().strip()
        
        # Quitar el widget editor del item
        self.category_list.removeItemWidget(item)
        
        if not new_name:
            # Si está vacío, simplemente eliminamos el item temporal
            self.category_list.takeItem(self.category_list.row(item))
            return
        
        if new_name in self.commands_db:
            QMessageBox.warning(self, "Error", "Esa categoría ya existe.")
            self.category_list.takeItem(self.category_list.row(item))
            return

        # Es un éxito:
        item.setText(new_name) # Establecemos el texto final del item
        self.commands_db[new_name] = {} # Añadir a la DB
        self.save_data(COMMANDS_FILE, self.commands_db) # Guardar en JSON
        
        # Añadir un nuevo QListWidget vacío al command_stack
        new_list = QListWidget()
        new_list.itemClicked.connect(self.on_command_selected)
        new_list.itemDoubleClicked.connect(self.on_command_double_clicked)
        self.command_stack.addWidget(new_list)
        
        # Seleccionar la nueva categoría
        self.category_list.setCurrentItem(item)

    def on_delete_category(self):
        """Elimina la categoría seleccionada."""
        item = self.category_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para eliminar.")
            return
        
        cat_name = item.text()
        
        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar la categoría '{cat_name}' y todos sus comandos?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Eliminar de la DB
            del self.commands_db[cat_name]
            self.save_data(COMMANDS_FILE, self.commands_db)
            
            # Eliminar de la UI
            index = self.category_list.row(item)
            self.category_list.takeItem(index)
            widget = self.command_stack.widget(index)
            self.command_stack.removeWidget(widget)
            if widget:
                widget.deleteLater()
            
            # Limpiar la vista si no quedan categorías
            if self.category_list.count() == 0:
                self.on_command_selected(None)

    def on_add_command(self):
        """Prepara el editor para añadir un nuevo comando."""
        current_cat_item = self.category_list.currentItem()
        if not current_cat_item:
            QMessageBox.warning(self, "Error", "Selecciona una categoría primero.")
            return

        self.is_editing_command = False
        self.current_edit_category = current_cat_item.text()

        # Limpiar campos del editor
        self.editor_title.setText(f"<h2>Añadir Comando a '{self.current_edit_category}'</h2>")
        self.editor_cmd_name.setText("")
        self.editor_cmd_template.setText("")
        self.editor_cmd_info.setText("")
        
        self.editor_cmd_name.setFocus()
        
        # Cambiar a la vista de edición
        self.main_stack.setCurrentWidget(self.editor_widget)

    def on_edit_command(self):
        """Prepara el editor para modificar un comando existente."""
        # Obtener comando actual
        current_list = self.command_stack.currentWidget()
        if not current_list: return
        current_cmd_item = current_list.currentItem()
        
        current_cat_item = self.category_list.currentItem()
        
        if not current_cmd_item or not current_cat_item:
            QMessageBox.warning(self, "Error", "Selecciona un comando para editar.")
            return
            
        self.is_editing_command = True
        self.current_edit_category = current_cat_item.text()
        self.current_edit_command_name = current_cmd_item.text()
        
        # Obtener datos de la DB
        cmd_data = self.commands_db[self.current_edit_category][self.current_edit_command_name]

        # Rellenar campos del editor
        self.editor_title.setText(f"<h2>Editando '{self.current_edit_command_name}'</h2>")
        self.editor_cmd_name.setText(self.current_edit_command_name)
        self.editor_cmd_template.setText(cmd_data["template"])
        self.editor_cmd_info.setText(cmd_data["info"])
        
        self.editor_cmd_name.setFocus()
        
        # Cambiar a la vista de edición
        self.main_stack.setCurrentWidget(self.editor_widget)

    def on_delete_command(self):
        """Elimina el comando seleccionado."""
        current_list = self.command_stack.currentWidget()
        if not current_list: return
        current_cmd_item = current_list.currentItem()
        
        current_cat_item = self.category_list.currentItem()
        
        if not current_cmd_item or not current_cat_item:
            QMessageBox.warning(self, "Error", "Selecciona un comando para eliminar.")
            return
            
        cat_name = current_cat_item.text()
        cmd_name = current_cmd_item.text()
        
        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar el comando '{cmd_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Eliminar de la DB
            del self.commands_db[cat_name][cmd_name]
            self.save_data(COMMANDS_FILE, self.commands_db)
            
            # Eliminar de la UI
            row = current_list.row(current_cmd_item)
            current_list.takeItem(row)
            
            # Limpiar la vista
            self.on_command_selected(None)

    def on_save_command(self):
        """Guarda los cambios del editor en la DB y la UI."""
        new_name = self.editor_cmd_name.text().strip()
        new_template = self.editor_cmd_template.text().strip()
        new_info = self.editor_cmd_info.toPlainText().strip()
        
        if not new_name or not new_template:
            QMessageBox.warning(self, "Error", "El 'Nombre' y la 'Plantilla' no pueden estar vacíos.")
            return
            
        category_name = self.current_edit_category
        
        # Si estamos editando y el nombre ha cambiado, verificar que no exista
        if self.is_editing_command and new_name != self.current_edit_command_name:
            if new_name in self.commands_db[category_name]:
                QMessageBox.warning(self, "Error", "Ya existe un comando con ese nombre.")
                return
            # Eliminar el registro antiguo
            del self.commands_db[category_name][self.current_edit_command_name]
            
        # Si estamos añadiendo, verificar que no exista
        if not self.is_editing_command and new_name in self.commands_db[category_name]:
            QMessageBox.warning(self, "Error", "Ya existe un comando con ese nombre.")
            return

        # Crear/Actualizar la entrada en la DB
        self.commands_db[category_name][new_name] = {
            "template": new_template,
            "info": new_info
        }
        self.save_data(COMMANDS_FILE, self.commands_db)

        # --- Actualizar la UI en vivo ---
        current_list = self.command_stack.widget(self.category_list.currentRow())
        if not current_list: return # No debería pasar
        
        if self.is_editing_command:
            # Encontrar el item y actualizarlo
            for i in range(current_list.count()):
                item = current_list.item(i)
                if item.text() == self.current_edit_command_name:
                    item.setText(new_name)
                    break
        else:
            # Añadir nuevo item
            item = QListWidgetItem(new_name)
            current_list.addItem(item)
            
        # Ordenar alfabéticamente la lista de comandos en la UI
        current_list.sortItems()

        # Reordenar la DB (para consistencia, aunque no es estrictamente necesario)
        sorted_cmds = dict(sorted(self.commands_db[category_name].items()))
        self.commands_db[category_name] = sorted_cmds
        self.save_data(COMMANDS_FILE, self.commands_db)

        # Volver a la vista de ejecución
        self.main_stack.setCurrentWidget(self.execution_widget)
        
        # Seleccionar el comando que acabamos de guardar
        items = current_list.findItems(new_name, Qt.MatchFlag.MatchExactly)
        if items:
            current_list.setCurrentItem(items[0])
            self.on_command_selected(items[0])


    def on_cancel_edit(self):
        """Cancela la edición y vuelve a la vista de ejecución."""
        self.main_stack.setCurrentWidget(self.execution_widget)

    def on_variable_bank_double_clicked(self, item):
        """Inserta la variable seleccionada en el editor de plantillas."""
        # Solo funciona si estamos en la vista de edición
        if self.main_stack.currentWidget() != self.editor_widget:
            return
            
        var_name = item.text()
        self.editor_cmd_template.insert(f"[{var_name}]")
        self.editor_cmd_template.setFocus()


    # --- Slots de Ejecución (Fase 2) ---

    def setup_variable_config_panel(self):
        """Crea el QWidget y QFormLayout para las variables (inicialmente vacío)."""
        self.variable_config_panel = QWidget()
        self.variable_config_layout = QFormLayout(self.variable_config_panel)
        self.variable_config_layout.setContentsMargins(0, 10, 0, 10)
        # Establece un fondo para distinguirlo visualmente
        self.variable_config_panel.setStyleSheet("background-color: #333333; border-radius: 4px;")
        self.variable_config_panel.hide() # Oculto por defecto

    def execute_command(self):
        """Ejecuta el comando de la vista previa."""
        command_str = self.command_input.text().strip()
        if not command_str:
            return

        self.console_output.append(f"<b style='color: #00aaff;'>&gt; {command_str}</b>")

        parts = command_str.split()
        program = parts[0]
        arguments = parts[1:]

        if "docker login" in command_str:
            self.console_output.append("<i style='color: #ffcc00;'>AVISO: 'docker login' es interactivo. "
                                       "Pega tu Token (PAT) cuando pida la contraseña.</i>")
        
        self.process.start(program, arguments)

    def toggle_variable_panel(self):
        """Muestra u oculta el panel de configuración de variables."""
        self.variable_config_panel.setVisible(not self.variable_config_panel.isVisible())

    def build_variable_widgets(self):
        """Limpia y reconstruye el panel de variables basado en el self.current_template."""
        # Limpiar widgets anteriores
        self.clear_layout(self.variable_config_layout)
        self.dynamic_variable_widgets.clear()

        # Encontrar todas las variables (ej: [VAR_NAME])
        variables = re.findall(r'\[([^\]]+)\]', self.current_template)
        unique_variables = sorted(list(set(variables))) # Eliminar duplicados

        if not unique_variables:
            self.config_button.setVisible(False) # Ocultar botón si no hay variables
            return

        self.config_button.setVisible(True) # Mostrar botón
        
        # Crear widgets para cada variable
        for var_name in unique_variables:
            label = QLabel(f"{var_name}:")
            
            # Comprobar si la variable existe en la DB de variables y tiene valores
            if var_name in self.variables_db and self.variables_db[var_name]["valores"]:
                widget = QComboBox()
                widget.addItems(self.variables_db[var_name]["valores"])
                widget.setEditable(True) # Permitir al usuario escribir un valor no listado
                # Conectar señal
                widget.currentTextChanged.connect(self.update_command_preview)
            else:
                # Si no está en la DB o no tiene valores, usar un QLineEdit
                widget = QLineEdit()
                widget.setPlaceholderText(f"Valor para {var_name}")
                # Conectar señal
                widget.textChanged.connect(self.update_command_preview)
            
            # Añadir al layout y al diccionario de seguimiento
            self.variable_config_layout.addRow(label, widget)
            self.dynamic_variable_widgets[var_name] = widget

    def update_command_preview(self):
        """Actualiza el QLineEdit de vista previa (self.command_input) con los valores actuales."""
        resolved_command = self.current_template
        
        for var_name, widget in self.dynamic_variable_widgets.items():
            # Obtener el valor, ya sea de QComboBox o QLineEdit
            value = ""
            if isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QLineEdit):
                value = widget.text()
            
            # Si el valor está vacío, mantenemos el placeholder en el comando
            if not value:
                value_to_replace = f"[{var_name}]"
            else:
                value_to_replace = value

            # Reemplazar todas las instancias de la variable en la plantilla
            # Usamos una forma un poco más segura para evitar reemplazos parciales
            resolved_command = resolved_command.replace(f"[{var_name}]", value_to_replace)
            
        self.command_input.setText(resolved_command)

    def clear_layout(self, layout):
        """Utilidad para eliminar todos los widgets de un layout."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                # Manejar layouts anidados si los hubiera
                self.clear_layout(item.layout())
    
    # --- Funciones de QProcess y Dock ---
    def read_stdout(self):
        """Lee la salida estándar del proceso."""
        data = self.process.readAllStandardOutput().data().decode()
        self.console_output.append(data.strip())

    def read_stderr(self):
        """Lee la salida de error del proceso y la pone en rojo."""
        data = self.process.readAllStandardError().data().decode()
        self.console_output.append(f"<span style='color: #ff4444;'>{data.strip()}</span>")

    def refresh_right_dock(self):
        """Actualiza los paneles de contenedores e imágenes."""
        self.containers_view.setText("Actualizando contenedores...")
        self.images_view.setText("Actualizando imágenes...")

        # --- Ejecutar 'docker ps' ---
        process_ps = QProcess()
        process_ps.start("docker", ["ps", "--no-trunc"]) 
        process_ps.waitForFinished()
        output_ps = process_ps.readAllStandardOutput().data().decode()
        error_ps = process_ps.readAllStandardError().data().decode()
        
        if error_ps:
            self.containers_view.setText(f"<span style='color: #ff4444;'>Error:\n{error_ps}</span>")
        else:
            self.containers_view.setText(output_ps)

        # --- Ejecutar 'docker images' ---
        process_img = QProcess()
        process_img.start("docker", ["images", "--no-trunc"])
        process_img.waitForFinished()
        output_img = process_img.readAllStandardOutput().data().decode()
        error_img = process_img.readAllStandardError().data().decode()

        if error_img:
            self.images_view.setText(f"<span style='color: #ff4444;'>Error:\n{error_img}</span>")
        else:
            self.images_view.setText(output_img)

    # --- NUEVAS FUNCIONES (Fase 4) ---

    def on_manage_variable_values(self):
        """Abre la pestaña de edición de valores para la variable seleccionada."""
        current_item = self.variable_bank_list.currentItem()
        if not current_item:
            return
        
        var_name = current_item.text()
        
        # Evitar abrir la misma pestaña de edición varias veces
        if var_name in self.editor_tabs:
            self.info_tabs.setCurrentWidget(self.editor_tabs[var_name])
            return

        # Crear el widget editor
        editor_widget = self.create_value_editor_widget(var_name)
        
        # Añadir la nueva pestaña
        index = self.info_tabs.addTab(editor_widget, f"Editando: {var_name}")
        self.info_tabs.setCurrentIndex(index)
        
        # Guardar referencia a la pestaña
        self.editor_tabs[var_name] = editor_widget

    def create_value_editor_widget(self, var_name):
        """Crea el widget que va dentro de la pestaña de edición de valores."""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Barra de herramientas para añadir/quitar valores
        toolbar = QToolBar()
        toolbar.setObjectName("DockToolBar")
        
        add_button = QToolButton()
        add_button.setText("Añadir Valor (+)")
        add_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        del_button = QToolButton()
        del_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        del_button.setToolTip("Eliminar Valor Seleccionado")
        
        toolbar.addWidget(add_button)
        toolbar.addWidget(del_button)
        
        # Lista de valores
        value_list = QListWidget()
        if var_name in self.variables_db and "valores" in self.variables_db[var_name]:
            value_list.addItems(self.variables_db[var_name]["valores"])
        
        # Botón de cerrar
        close_button = QPushButton("Confirmar y Cerrar")
        
        layout.addWidget(toolbar)
        layout.addWidget(value_list)
        layout.addWidget(close_button)
        
        # Conectar señales
        add_button.clicked.connect(lambda: self.on_add_variable_value(var_name, value_list))
        del_button.clicked.connect(lambda: self.on_delete_variable_value(var_name, value_list))
        
        # Conectar el botón de cerrar para que cierre la pestaña
        tab_index = lambda: self.info_tabs.indexOf(container) # Encontrar su propio índice
        close_button.clicked.connect(lambda: self.info_tabs.removeTab(tab_index()))

        return container

    def on_add_variable_value(self, var_name, value_list):
        """Añade un QLineEdit temporal a la lista de valores."""
        editor = QLineEdit()
        editor.setPlaceholderText("Nuevo valor...")
        
        item = QListWidgetItem()
        value_list.addItem(item)
        value_list.setItemWidget(item, editor)
        editor.setFocus()
        
        # Conectar la señal de "edición terminada"
        editor.editingFinished.connect(lambda: self.on_finish_value_add(var_name, item, editor, value_list))

    def on_finish_value_add(self, var_name, item, editor, value_list):
        """Guarda el nuevo valor en la DB y actualiza la UI."""
        new_value = editor.text().strip()
        
        value_list.removeItemWidget(item)
        
        if not new_value:
            value_list.takeItem(value_list.row(item))
            return
            
        if new_value in self.variables_db[var_name]["valores"]:
            QMessageBox.warning(self, "Duplicado", "Ese valor ya existe para esta variable.")
            value_list.takeItem(value_list.row(item))
            return

        # Éxito:
        item.setText(new_value) # Poner el texto en el item
        self.variables_db[var_name]["valores"].append(new_value)
        self.variables_db[var_name]["valores"].sort() # Mantener ordenado
        self.save_data(VARIABLES_FILE, self.variables_db)
        
        # Re-poblar la lista para que esté ordenada
        value_list.clear()
        value_list.addItems(self.variables_db[var_name]["valores"])
        
        # Emitir señal para la actualización en vivo
        self.value_editor_signals.valueChanged.emit(var_name, new_value, True)

    def on_delete_variable_value(self, var_name, value_list):
        """Elimina el valor seleccionado de la DB y la UI."""
        current_item = value_list.currentItem()
        if not current_item:
            return
            
        value_to_delete = current_item.text()
        
        # Eliminar de la DB
        self.variables_db[var_name]["valores"].remove(value_to_delete)
        self.save_data(VARIABLES_FILE, self.variables_db)
        
        # Eliminar de la UI
        value_list.takeItem(value_list.row(current_item))
        
        # Emitir señal para la actualización en vivo
        self.value_editor_signals.valueChanged.emit(var_name, value_to_delete, False)

    def on_editor_tab_closed(self, index):
        """Se llama cuando se cierra una pestaña (con 'x' o botón)."""
        widget = self.info_tabs.widget(index)
        
        # Encontrar qué variable era esta pestaña
        var_name_to_remove = None
        for var_name, tab_widget in self.editor_tabs.items():
            if tab_widget == widget:
                var_name_to_remove = var_name
                break
                
        if var_name_to_remove:
            # Eliminar la pestaña y limpiarla de nuestro seguimiento
            self.info_tabs.removeTab(index)
            del self.editor_tabs[var_name_to_remove]

    def on_variable_value_changed(self, var_name, value, is_added):
        """Slot para la señal de actualización en vivo. Actualiza el QComboBox."""
        
        # Buscar el QComboBox correspondiente en el panel de configuración central
        if var_name in self.dynamic_variable_widgets:
            widget = self.dynamic_variable_widgets[var_name]
            
            if isinstance(widget, QComboBox):
                if is_added:
                    # Añadir el nuevo valor si no está ya (por si acaso)
                    if widget.findText(value) == -1:
                        widget.addItem(value)
                        widget.model().sort(0) # Ordenar el combobox
                else:
                    # Eliminar el valor
                    index = widget.findText(value)
                    if index != -1:
                        widget.removeItem(index)

    # --- Fin de Funciones de Fase 4 ---
    
    def closeEvent(self, event):
        """Asegura que el proceso termine al cerrar la app."""
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.terminate()
            self.process.waitForFinished()
        event.accept()


# --- Punto de entrada de la Aplicación ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    
    window = CommandManagerGUI()
    window.show()
    sys.exit(app.exec())