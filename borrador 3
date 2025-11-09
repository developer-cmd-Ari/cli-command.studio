import sys
import json
import os
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QTextEdit, QLineEdit, QPushButton,
    QDockWidget, QToolBar, QToolButton, QMessageBox, QInputDialog,
    QTabWidget, QListWidgetItem, QStyle, QFormLayout, QComboBox, QLabel,
    QSizePolicy, QSplitter, QTabBar, QMenu, QButtonGroup, QRadioButton,
    QScrollArea
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
MONITOR_CONFIG_FILE = "monitor_config.json"


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

        # Proceso para comandos de ejecución
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)

        # Proceso para el monitor en vivo
        self.monitor_process = QProcess(self)
        self.monitor_process.readyReadStandardOutput.connect(self.read_monitor_stdout)
        self.monitor_process.readyReadStandardError.connect(self.read_monitor_stderr)

        self.variables_db = self.load_data(VARIABLES_FILE, self.get_default_variables)
        self.commands_db = self.load_data(COMMANDS_FILE, self.get_default_commands)
        self.monitor_config = self.load_data(MONITOR_CONFIG_FILE, lambda: {"monitor_command": "docker ps"})

        self.current_template = ""
        self.dynamic_variable_widgets = {}
        
        self.is_editing_command = False
        self.current_edit_category = ""
        self.current_edit_command_name = ""
        
        # --- NUEVO: Estado de edición de variables ---
        self.currently_editing_variable = None
        self.value_editor_signals = ValueEditorSignals()
        self.current_command_filter_vars = None # Para el filtro de variables por comando
        # -------------------------------------------

        self.setup_ui()
        self.init_signals()
        
        # Seleccionar la primera categoría y comando si existen
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)
            list_widget = self.command_stack.widget(0)
            if list_widget and list_widget.count() > 0:
                list_widget.setCurrentRow(0)
                self.on_command_selected(list_widget.item(0))
        
        self.run_monitor_command() # Iniciar monitor al arrancar


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
            "TU_USUARIO": {"descripcion": "Usuario de GitHub o Docker Hub", "valores": ["ariel", "juan", "pedro"], "default": "ariel"},
            "IMAGEN_REPO": {"descripcion": "Nombre del repositorio en el registry", "valores": ["mi-app", "mi-backend"], "default": "mi-app"},
            "IMAGEN_LOCAL": {"descripcion": "Nombre de la imagen local (ej: app:tag)", "valores": ["mi-app:latest", "backend:1.0"], "default": ""},
            "CONTENEDOR_ID": {"descripcion": "ID o Nombre de un contenedor", "valores": ["contenedor_1", "db_postgres"], "default": ""},
            "ID_O_TAG": {"descripcion": "ID o Tag de una imagen", "valores": ["imagen_id", "mi-app:latest"], "default": ""}
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
        
        left_dock_container = QWidget()
        ld_layout = QVBoxLayout(left_dock_container)
        ld_layout.setContentsMargins(0, 0, 0, 0)
        ld_layout.setSpacing(2)

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

        self.category_list = QListWidget()
        self.category_list.addItems(self.commands_db.keys())
        ld_layout.addWidget(self.category_list)
        
        self.left_dock.setWidget(left_dock_container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # --- Dock Derecho (Monitor y Variables) ---
        self.right_dock = QDockWidget("Vistas en Vivo", self)
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        right_dock_widget = QWidget()
        right_layout = QVBoxLayout(right_dock_widget)
        
        self.info_tabs = QTabWidget()
        self.info_tabs.setTabsClosable(True)
        
        # --- Pestaña de Monitor (NUEVA) ---
        self.monitor_tab_widget = QWidget()
        monitor_layout = QVBoxLayout(self.monitor_tab_widget)
        
        monitor_input_layout = QHBoxLayout()
        self.monitor_command_input = QLineEdit(self.monitor_config["monitor_command"])
        self.monitor_command_input.setPlaceholderText("Comando a monitorear...")
        self.save_monitor_cmd_button = QPushButton("Aplicar")
        monitor_input_layout.addWidget(self.monitor_command_input)
        monitor_input_layout.addWidget(self.save_monitor_cmd_button)
        
        self.monitor_output = QTextEdit()
        self.monitor_output.setReadOnly(True)
        self.monitor_output.setFont(QFont("Consolas", 9))
        
        monitor_layout.addLayout(monitor_input_layout)
        monitor_layout.addWidget(self.monitor_output)
        
        # --- Pestaña de Variables (Existente) ---
        self.variables_tab_widget = QWidget()
        variables_layout = QVBoxLayout(self.variables_tab_widget)
        variables_layout.setContentsMargins(0, 0, 0, 0)

        self.variable_splitter = QSplitter(Qt.Orientation.Vertical)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)

        var_toolbar = QToolBar()
        var_toolbar.setObjectName("DockToolBar")
        
        self.add_var_button = QToolButton()
        self.add_var_button.setText("Añadir (+)")
        self.add_var_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

        self.show_all_vars_button = QToolButton()
        self.show_all_vars_button.setText("Mostrar Todas")
        self.show_all_vars_button.setVisible(False) # Oculto por defecto
        self.show_all_vars_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        
        self.del_var_button = QToolButton()
        self.del_var_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.del_var_button.setToolTip("Eliminar Variable Seleccionada")

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        var_toolbar.addWidget(self.add_var_button)
        var_toolbar.addWidget(self.show_all_vars_button)
        var_toolbar.addWidget(spacer)
        var_toolbar.addWidget(self.del_var_button)
        top_layout.addWidget(var_toolbar)

        self.variable_search_bar = QLineEdit()
        self.variable_search_bar.setPlaceholderText("Buscar variable...")
        top_layout.addWidget(self.variable_search_bar)

        self.variable_bank_list = QListWidget()
        self.variable_bank_list.setToolTip("Selecciona una variable para ver/editar sus opciones.")
        self.variable_bank_list.addItems(sorted(self.variables_db.keys()))
        top_layout.addWidget(self.variable_bank_list)

        self.edit_variable_button = QToolButton()
        self.edit_variable_button.setText("Editar Valores / Descripción")
        self.edit_variable_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.edit_variable_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.edit_variable_button.setVisible(False) 
        top_layout.addWidget(self.edit_variable_button)

        self.variable_editor_container = QWidget()
        self.variable_editor_container.setLayout(QVBoxLayout()) 
        self.variable_editor_container.setVisible(False)

        self.variable_splitter.addWidget(top_widget)
        self.variable_splitter.addWidget(self.variable_editor_container)
        self.variable_splitter.setSizes([300, 500]) 

        variables_layout.addWidget(self.variable_splitter)
        
        # --- Añadir Pestañas ---
        self.info_tabs.addTab(self.monitor_tab_widget, "Monitor")
        self.info_tabs.addTab(self.variables_tab_widget, "Variables")

        # Asegurarnos de que las pestañas base no se puedan cerrar
        self.info_tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)
        self.info_tabs.tabBar().setTabButton(1, QTabBar.ButtonPosition.RightSide, None)
        
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
        
        self.command_search_bar = QLineEdit()
        self.command_search_bar.setPlaceholderText("Buscar comando...")
        
        self.del_cmd_button = QToolButton()
        self.del_cmd_button.setText("Eliminar (-)")
        self.del_cmd_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.del_cmd_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        cmd_toolbar.addWidget(self.add_cmd_button)
        cmd_toolbar.addWidget(self.edit_cmd_button)
        cmd_toolbar.addWidget(self.command_search_bar)
        cmd_toolbar.addWidget(spacer)
        cmd_toolbar.addWidget(self.del_cmd_button)
        main_layout.addWidget(cmd_toolbar)
        # ----------------------------------------------

        # --- Contenedor central para cambiar entre vista normal y búsqueda ---
        self.central_display_stack = QStackedWidget()

        # 1. StackedWidget para la vista normal por categorías
        self.command_stack = QStackedWidget()
        self.rebuild_command_stack() # Rellenar el stack desde la DB
        
        # 2. Lista para los resultados de búsqueda
        self.search_results_list = QListWidget()

        self.central_display_stack.addWidget(self.command_stack)
        self.central_display_stack.addWidget(self.search_results_list)
        main_layout.addWidget(self.central_display_stack)

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
        # self.command_input.setReadOnly(True) # Ahora es editable


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
        self.config_button.clicked.connect(self.toggle_variable_panel)

        # --- Señales del Monitor ---
        self.save_monitor_cmd_button.clicked.connect(self.on_save_monitor_command)
        self.monitor_command_input.returnPressed.connect(self.on_save_monitor_command)

        # Señales de Edición de Comandos (Fase 3)
        self.add_cat_button.clicked.connect(self.on_add_category)
        self.del_cat_button.clicked.connect(self.on_delete_category)
        self.add_cmd_button.clicked.connect(self.on_add_command)
        self.edit_cmd_button.clicked.connect(self.on_edit_command)
        self.del_cmd_button.clicked.connect(self.on_delete_command)
        self.editor_save_button.clicked.connect(self.on_save_command)
        self.editor_cancel_button.clicked.connect(self.on_cancel_edit)
        self.variable_bank_list.itemDoubleClicked.connect(self.on_variable_bank_double_clicked)

        # --- Señales de Búsqueda de Comandos ---
        self.command_search_bar.textChanged.connect(self.on_command_search_changed)
        self.search_results_list.itemClicked.connect(self.on_search_result_selected)

        # --- NUEVAS SEÑALES (Fase 4 - Refactorizado) ---
        self.variable_bank_list.currentItemChanged.connect(self.on_variable_selected)
        self.edit_variable_button.clicked.connect(self.show_variable_editor)
        self.add_var_button.clicked.connect(self.on_add_variable)
        self.del_var_button.clicked.connect(self.on_delete_variable)
        self.show_all_vars_button.clicked.connect(self.on_show_all_variables)
        self.variable_search_bar.textChanged.connect(self.on_variable_search_changed)
        
        # Conecta la señal personalizada para la actualización en vivo
        self.value_editor_signals.valueChanged.connect(self.on_variable_value_changed)
    
    # --- Slots de Búsqueda y Filtro de Variables ---
    def on_variable_search_changed(self):
        """Se activa cuando el texto de búsqueda de variables cambia."""
        self.apply_variable_filters()

    def apply_variable_filters(self):
        """Aplica los filtros de comando y búsqueda a la lista de variables."""
        search_text = self.variable_search_bar.text().lower()
        
        is_command_filtering = self.current_command_filter_vars is not None

        for i in range(self.variable_bank_list.count()):
            item = self.variable_bank_list.item(i)
            var_name = item.text()

            if is_command_filtering:
                command_filter_passed = var_name in self.current_command_filter_vars
            else:
                command_filter_passed = True

            search_filter_passed = search_text in var_name.lower()

            item.setHidden(not (command_filter_passed and search_filter_passed))

    def filter_variable_list(self, variables_to_show):
        """
        Establece el filtro de variables por comando y aplica todos los filtros.
        - Si `variables_to_show` es una lista, filtra por esas variables.
        - Si `variables_to_show` es None, quita el filtro de comando.
        """
        self.current_command_filter_vars = variables_to_show
        self.show_all_vars_button.setVisible(variables_to_show is not None)
        self.apply_variable_filters()

    def on_show_all_variables(self):
        """Quita todos los filtros de la lista de variables."""
        self.variable_search_bar.blockSignals(True)
        self.variable_search_bar.clear()
        self.variable_search_bar.blockSignals(False)
        
        self.filter_variable_list(None)

    # --- Slots de Búsqueda de Comandos ---
    def on_command_search_changed(self, text):
        """Filtra los comandos en todas las categorías basado en el texto de búsqueda."""
        text = text.strip()
        if not text:
            # Si no hay texto, mostrar la vista normal de comandos
            self.central_display_stack.setCurrentWidget(self.command_stack)
            return

        # Si hay texto, cambiar a la vista de resultados de búsqueda
        self.central_display_stack.setCurrentWidget(self.search_results_list)
        self.search_results_list.clear()

        # Buscar en toda la base de datos de comandos
        for cat_name, commands in self.commands_db.items():
            for cmd_name, cmd_data in commands.items():
                if text.lower() in cmd_name.lower():
                    # Añadir item al resultado de búsqueda
                    display_text = f"{cmd_name}  ({cat_name})" # Mostrar comando y categoría
                    item = QListWidgetItem(display_text)
                    # Guardar la información necesaria para encontrar el comando original
                    item.setData(Qt.ItemDataRole.UserRole, {"category": cat_name, "command": cmd_name})
                    self.search_results_list.addItem(item)

    def on_search_result_selected(self, item):
        """Se activa al hacer clic en un resultado de búsqueda."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        cat_name = data["category"]
        cmd_name = data["command"]

        # 1. Encontrar y seleccionar la categoría en la lista de categorías
        cat_items = self.category_list.findItems(cat_name, Qt.MatchFlag.MatchExactly)
        if not cat_items:
            return
        self.category_list.setCurrentItem(cat_items[0])
        
        # El setCurrentItem anterior ya cambió el índice del command_stack
        current_list_widget = self.command_stack.currentWidget()

        # 2. Encontrar y seleccionar el comando en la lista de comandos de esa categoría
        cmd_items = current_list_widget.findItems(cmd_name, Qt.MatchFlag.MatchExactly)
        if not cmd_items:
            return
        current_list_widget.setCurrentItem(cmd_items[0])
        
        # 3. Disparar la selección normal para actualizar el resto de la UI
        self.on_command_selected(cmd_items[0])

        # 4. Limpiar la búsqueda y volver a la vista normal
        # Bloquear señales para evitar un bucle/comportamiento no deseado
        self.command_search_bar.blockSignals(True)
        self.command_search_bar.clear()
        self.command_search_bar.blockSignals(False)
        self.central_display_stack.setCurrentWidget(self.command_stack)

    # --- Slots de Edición (Fase 3) ---

    def on_command_selected(self, item):
        """Se activa al hacer clic en un comando de la lista central."""
        if not item:
            self.info_display.clear()
            self.command_input.clear()
            self.variable_config_panel.hide()
            self.config_button.setVisible(False)
            self.filter_variable_list(None) # Limpiar filtro
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

        # Filtrar la lista de variables según el comando seleccionado
        variables_in_template = re.findall(r'\[([^\]]+)\]', self.current_template)
        unique_variables = sorted(list(set(variables_in_template)))
        self.filter_variable_list(unique_variables)
        
        self.build_variable_widgets() 
        self.update_command_preview() 
        
        # Mostrar el panel si hay variables, ocultarlo si no
        if self.dynamic_variable_widgets:
            self.variable_config_panel.show()
        else:
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

        self.filter_variable_list(None) # Quitar filtros de variables al añadir comando

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
            
        self.filter_variable_list(None) # Quitar filtros de variables al editar comando

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

    def on_duplicate_variable_clicked(self, index_to_duplicate):
        """Duplica un placeholder de variable en la plantilla de comando."""
        matches = list(re.finditer(r'\[([^\]]+)\]', self.current_template))
        
        if index_to_duplicate >= len(matches):
            return

        match_to_duplicate = matches[index_to_duplicate]
        placeholder_text = match_to_duplicate.group(0)
        insert_pos = match_to_duplicate.end()

        self.current_template = (self.current_template[:insert_pos] + 
                                 " " + placeholder_text + 
                                 self.current_template[insert_pos:])

        # Guardar los valores actuales para restaurarlos después de reconstruir la UI
        current_values = [widget.text() for widget in self.dynamic_variable_widgets]
        
        self.build_variable_widgets()
        
        # Restaurar los valores y añadir uno vacío para el nuevo duplicado
        new_values = current_values[:index_to_duplicate+1] + [""] + current_values[index_to_duplicate+1:]
        for widget, value in zip(self.dynamic_variable_widgets, new_values):
            widget.setText(value)

        self.update_command_preview()

    def build_variable_widgets(self):
        """Limpia y reconstruye el panel de variables basado en el self.current_template, permitiendo duplicados."""
        self.clear_layout(self.variable_config_layout)
        self.dynamic_variable_widgets = [] # Cambiado a una lista

        variables = re.findall(r'\[([^\]]+)\]', self.current_template)

        if not variables:
            self.config_button.setVisible(False)
            return

        self.config_button.setVisible(True)
        
        seen_vars = set()
        for i, var_name in enumerate(variables):
            label = QLabel(f"{var_name}:")
            
            input_container = QWidget()
            container_layout = QHBoxLayout(input_container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)

            widget = QLineEdit()
            widget.textChanged.connect(self.update_command_preview)
            container_layout.addWidget(widget)
            self.dynamic_variable_widgets.append(widget)

            has_values = var_name in self.variables_db and self.variables_db[var_name].get("valores")

            if has_values:
                var_info = self.variables_db[var_name]
                
                # Aplicar valor por defecto solo a la primera aparición de la variable
                if var_name not in seen_vars:
                    default_value = var_info.get("default", "")
                    if default_value:
                        widget.setText(default_value)
                    elif var_info["valores"]:
                        widget.setPlaceholderText(f"Ej: {var_info['valores'][0]}")
                    seen_vars.add(var_name)
                elif var_info["valores"]:
                     widget.setPlaceholderText(f"Ej: {var_info['valores'][0]}")

                picker_button = QToolButton()
                picker_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
                picker_button.setToolTip("Seleccionar un valor predefinido")
                
                value_menu = QMenu(self)
                for value in var_info["valores"]:
                    action = value_menu.addAction(value)
                    action.triggered.connect(lambda checked=False, w=widget, v=value: w.setText(v))
                
                picker_button.setMenu(value_menu)
                picker_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
                container_layout.addWidget(picker_button)
            else:
                widget.setPlaceholderText(f"Valor para {var_name}")

            # Botón para duplicar
            duplicate_button = QToolButton()
            duplicate_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
            duplicate_button.setToolTip(f"Duplicar argumento [{var_name}]")
            duplicate_button.clicked.connect(lambda checked=False, index=i: self.on_duplicate_variable_clicked(index))
            container_layout.addWidget(duplicate_button)

            self.variable_config_layout.addRow(label, input_container)

    def update_command_preview(self):
        """Actualiza el QLineEdit de vista previa, manejando placeholders duplicados."""
        widget_iter = iter(self.dynamic_variable_widgets)
        
        def replacer(match):
            try:
                widget = next(widget_iter)
                value = widget.text()
                return value if value else match.group(0)
            except StopIteration:
                return match.group(0)

        resolved_command = re.sub(r'\[([^\]]+)\]', replacer, self.current_template)
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

    def read_monitor_stdout(self):
        """Lee la salida estándar del proceso del monitor."""
        data = self.monitor_process.readAllStandardOutput().data().decode()
        self.monitor_output.append(data.strip())

    def read_monitor_stderr(self):
        """Lee la salida de error del proceso del monitor y la pone en rojo."""
        data = self.monitor_process.readAllStandardError().data().decode()
        self.monitor_output.append(f"<span style='color: #ff4444;'>{data.strip()}</span>")

    def run_monitor_command(self):
        """Ejecuta o reinicia el comando de monitoreo."""
        if self.monitor_process.state() == QProcess.ProcessState.Running:
            self.monitor_process.kill()
            self.monitor_process.waitForFinished()

        self.monitor_output.clear()
        command_str = self.monitor_command_input.text().strip()
        if not command_str:
            self.monitor_output.setText("No se ha especificado un comando de monitoreo.")
            return

        self.monitor_output.append(f"<i style='color: #00aaff;'>Ejecutando: {command_str}</i>\n")
        
        parts = command_str.split()
        program = parts[0]
        arguments = parts[1:]
        self.monitor_process.start(program, arguments)

    def on_save_monitor_command(self):
        """Guarda el nuevo comando de monitoreo y lo ejecuta."""
        new_command = self.monitor_command_input.text().strip()
        self.monitor_config["monitor_command"] = new_command
        self.save_data(MONITOR_CONFIG_FILE, self.monitor_config)
        self.run_monitor_command()

    # --- NUEVAS FUNCIONES (Fase 4 - Refactorizado con QScrollArea) ---

    def on_variable_selected(self, current, previous):
        """
        Se activa al cambiar la selección en la lista de variables.
        Guarda automáticamente los cambios del editor anterior antes de preparar el nuevo.
        """
        if self.variable_editor_container.isVisible():
            self.save_current_variable_editor()

        self.variable_editor_container.setVisible(False)
        self.clear_layout(self.variable_editor_container.layout())
        self.currently_editing_variable = None
        self.selected_value_widget = None # Limpiar selección

        if current:
            self.edit_variable_button.setVisible(True)
        else:
            self.edit_variable_button.setVisible(False)

    def save_current_variable_editor(self):
        """Lee los valores del editor actual y los guarda en la DB y el JSON."""
        if not self.currently_editing_variable or not hasattr(self, 'values_layout'):
            return

        new_values = []
        default_value = ""

        # Iterar sobre los widgets para encontrar valores y el default
        for i in range(self.values_layout.count()):
            widget = self.values_layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget): # Ignorar el 'stretch' al final
                line_edit = widget.findChild(QLineEdit)
                radio_button = widget.findChild(QRadioButton)
                
                if line_edit:
                    current_text = line_edit.text()
                    new_values.append(current_text)
                    if radio_button and radio_button.isChecked():
                        default_value = current_text

        if self.currently_editing_variable in self.variables_db:
            # Preservar la descripción existente
            desc = self.variables_db[self.currently_editing_variable].get("descripcion", "")
            
            unique_values = sorted(list(set(new_values)))
            
            self.variables_db[self.currently_editing_variable] = {
                "descripcion": desc,
                "valores": unique_values,
                "default": default_value
            }
            
            self.save_data(VARIABLES_FILE, self.variables_db)
            print(f"Variable '{self.currently_editing_variable}' guardada con {len(unique_values)} valores (Default: '{default_value}').")

    def show_variable_editor(self):
        """Puebla y muestra el panel de edición para la variable seleccionada usando QScrollArea."""
        current_item = self.variable_bank_list.currentItem()
        if not current_item: return

        var_name = current_item.text()
        self.currently_editing_variable = var_name
        self.selected_value_widget = None # Reset selection
        self.clear_layout(self.variable_editor_container.layout())

        editor_layout = self.variable_editor_container.layout()

        # --- Barra de herramientas ---
        toolbar = QToolBar()
        toolbar.setObjectName("DockToolBar")
        del_button = QToolButton()
        del_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        del_button.setText("Eliminar Valor Seleccionado")
        del_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        del_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        toolbar.addWidget(del_button)

        # --- Área de Scroll para los valores ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        self.values_layout = QVBoxLayout(scroll_widget)
        self.values_layout.setContentsMargins(5, 5, 5, 5)
        self.values_layout.setSpacing(3)
        
        scroll_area.setWidget(scroll_widget)

        # --- Grupo de botones para gestionar el 'default' ---
        self.current_editor_button_group = QButtonGroup(self)
        self.current_editor_button_group.setExclusive(True)

        var_data = self.variables_db.get(var_name, {})
        valores = var_data.get("valores", [])
        default_value = var_data.get("default", "")

        for value in sorted(valores):
            self.add_value_widget_to_layout(value, default_value, self.values_layout, self.current_editor_button_group)
        
        self.values_layout.addStretch() # Empuja los widgets hacia arriba

        # --- Layout para añadir nuevos valores ---
        add_layout = QHBoxLayout()
        new_value_input = QLineEdit()
        new_value_input.setPlaceholderText("Escriba un nuevo valor y pulse Enter...")
        add_button = QPushButton("Añadir")
        add_layout.addWidget(new_value_input)
        add_layout.addWidget(add_button)

        # --- Ensamblar el editor ---
        editor_layout.addWidget(toolbar)
        editor_layout.addWidget(scroll_area, 1) # El '1' permite que el scroll se expanda
        editor_layout.addLayout(add_layout)
        
        # --- Conexiones ---
        add_button.clicked.connect(lambda: self.on_add_variable_value(var_name, self.values_layout, self.current_editor_button_group, new_value_input))
        new_value_input.returnPressed.connect(lambda: self.on_add_variable_value(var_name, self.values_layout, self.current_editor_button_group, new_value_input))
        del_button.clicked.connect(self.on_delete_variable_value)

        self.variable_editor_container.setVisible(True)
        new_value_input.setFocus()

    def add_value_widget_to_layout(self, value_text, default_value, layout, button_group):
        """Crea y añade un widget de valor directamente a un layout."""
        widget = QWidget()
        widget_layout = QHBoxLayout(widget)
        widget_layout.setContentsMargins(4, 4, 4, 4)

        radio_button = QRadioButton()
        if value_text == default_value:
            radio_button.setChecked(True)
        
        line_edit = QLineEdit(value_text)
        
        widget_layout.addWidget(radio_button)
        widget_layout.addWidget(line_edit)
        
        button_group.addButton(radio_button)
        
        # Conectar para poder saber cuál está seleccionado para borrar
        radio_button.toggled.connect(self.on_value_widget_selected)

        # Insertar el nuevo widget antes del 'stretch'
        layout.insertWidget(layout.count() - 1, widget)

    def on_value_widget_selected(self, is_checked):
        """Almacena una referencia al widget cuyo radio button ha sido seleccionado."""
        if is_checked:
            radio_button = self.sender()
            self.selected_value_widget = radio_button.parentWidget()

    def on_add_variable_value(self, var_name, layout, button_group, input_field):
        """Añade un nuevo valor desde el QLineEdit en línea."""
        new_value = input_field.text().strip()
        if not new_value:
            return

        # Comprobar duplicados
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget:
                line_edit = widget.findChild(QLineEdit)
                if line_edit and line_edit.text() == new_value:
                    QMessageBox.warning(self, "Duplicado", "Ese valor ya existe para esta variable.")
                    input_field.selectAll()
                    input_field.setFocus()
                    return
        
        self.add_value_widget_to_layout(new_value, "", layout, button_group)
        self.value_editor_signals.valueChanged.emit(var_name, new_value, True)
        input_field.clear()
        input_field.setFocus()

    def on_delete_variable_value(self):
        """Elimina el valor seleccionado del layout."""
        if not self.selected_value_widget:
            QMessageBox.warning(self, "Atención", "Selecciona un valor de la lista para eliminar.")
            return

        radio_button = self.selected_value_widget.findChild(QRadioButton)
        line_edit = self.selected_value_widget.findChild(QLineEdit)
        value_to_delete = line_edit.text()
        var_name = self.currently_editing_variable

        # Eliminar de la UI
        self.current_editor_button_group.removeButton(radio_button)
        self.selected_value_widget.deleteLater()
        
        # Limpiar selección
        self.selected_value_widget = None
        
        # Emitir señal
        self.value_editor_signals.valueChanged.emit(var_name, value_to_delete, False)
        print(f"Valor '{value_to_delete}' eliminado de la UI para '{var_name}'.")

    def on_variable_value_changed(self, var_name, value, is_added):
        """Slot para la señal de actualización en vivo."""
        # La lógica de actualización de ComboBox en vivo se mantiene por si acaso,
        # aunque la reconstrucción al seleccionar comando es el método principal.
        pass

    def on_add_variable(self):
        """Muestra un diálogo para crear una nueva variable global."""
        text, ok = QInputDialog.getText(self, 'Crear Nueva Variable', 
                                          'Nombre de la variable (ej: MI_NUEVA_VARIABLE):')
        if ok and text:
            var_name = text.strip().upper().replace(" ", "_")
            
            if not re.match(r'^[A-Z0-9_]+$', var_name) or not var_name:
                QMessageBox.warning(self, "Nombre Inválido", "El nombre no puede estar vacío y solo puede contener letras mayúsculas, números y guiones bajos.")
                return

            if var_name in self.variables_db:
                QMessageBox.warning(self, "Error", f"La variable '{var_name}' ya existe.")
                return

            # Añadir a la DB
            self.variables_db[var_name] = {
                "descripcion": "", 
                "valores": [], 
                "default": ""
            }
            self.save_data(VARIABLES_FILE, self.variables_db)

            # Añadir a la UI, ordenar y seleccionar
            new_item = QListWidgetItem(var_name)
            self.variable_bank_list.addItem(new_item)
            self.variable_bank_list.sortItems()
            self.variable_bank_list.setCurrentItem(new_item)
            
            # Abrir el editor para la nueva variable
            self.show_variable_editor()

    def on_delete_variable(self):
        """Elimina la variable global seleccionada."""
        current_item = self.variable_bank_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Selecciona una variable para eliminar.")
            return

        var_name = current_item.text()
        
        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar la variable '[{var_name}]' permanentemente? Esta acción no se puede deshacer.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Eliminar de la DB
            del self.variables_db[var_name]
            self.save_data(VARIABLES_FILE, self.variables_db)

            # Eliminar de la UI
            self.variable_bank_list.takeItem(self.variable_bank_list.row(current_item))

    def filter_variable_list(self, variables_to_show):
        """
        Filtra la lista de variables.
        - Si `variables_to_show` es una lista, muestra solo esas variables.
        - Si `variables_to_show` es None, muestra todas las variables (quita el filtro).
        """
        is_filtering = variables_to_show is not None

        for i in range(self.variable_bank_list.count()):
            item = self.variable_bank_list.item(i)
            if is_filtering:
                item.setHidden(item.text() not in variables_to_show)
            else:
                item.setHidden(False) # Mostrar todo

        self.show_all_vars_button.setVisible(is_filtering)

    def on_show_all_variables(self):
        """Quita el filtro de la lista de variables."""
        self.filter_variable_list(None)

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