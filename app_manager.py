import sys
import os
import uuid
import shutil
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QStackedWidget, QPlainTextEdit, QTabWidget, QLineEdit, QTabBar, QGridLayout,
    QMessageBox, QInputDialog, QLabel, QFrame, QListWidgetItem,
    QSizePolicy
)
from PySide6.QtCore import Qt, QProcess, QSettings, QSize, QByteArray, Signal, QTimer
from PySide6.QtGui import QIcon, QFontDatabase, QPainter, QPixmap, QTextCursor
from PySide6.QtSvg import QSvgRenderer

# --- Iconos SVG (sin cambios) ---
def get_icon(name):
    svg_data = {
        "add": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>""",
        "edit": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4L18.5 2.5z"></path></svg>""",
        "play": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>""",
        "stop": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>""",
        "save": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>""",
        "edit_txt": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>""",
        "trash": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>""",
        "external-link": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>""",
        "gallery": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>"""
    }
    if name not in svg_data: return QIcon()
    icon_bytes = QByteArray(svg_data[name].encode('utf-8'))
    renderer = QSvgRenderer(icon_bytes)
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    icon = QIcon()
    icon.addPixmap(pixmap)
    return icon

try:
    USE_ICONS = True
except ImportError:
    USE_ICONS = False

def get_icon_or_text(icon_name, text):
    if USE_ICONS:
        return get_icon(icon_name), ""
    return QIcon(), text


# --- Estilo QSS (CSS de Qt) para el Tema Oscuro ---
DARK_STYLESHEET = """
QWidget {
    background-color: #2b2b2b;
    color: #f0f0f0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
}
QMainWindow::separator {
    background-color: #3c3c3c;
    width: 1px;
    height: 1px;
}
/* --- Menú Lateral Izquierdo --- */
#LeftMenu {
    background-color: #3c3c3c;
    border-right: 1px solid #4a4a4a;
}
#LeftMenu QLabel {
    font-size: 12pt;
    font-weight: bold;
    padding: 10px;
    margin-bottom: 5px;
    background-color: #454545;
    border-radius: 5px;
}
QListWidget {
    background-color: #3c3c3c;
    border: none;
    padding: 5px;
}
QListWidget::item {
    padding: 0px; /* El padding ahora está en el widget interno */
    margin-bottom: 5px; /* Aumentar margen inferior para separación vertical */
    border-radius: 5px;
    color: #f0f0f0; /* Asegurar que el texto del item sea visible */
}
/* Estilo para el widget personalizado dentro del item */
QWidget#InstanceItem {
    background-color: transparent;
    border-radius: 5px;
    padding: 5px 10px;
}
QListWidget::item:hover QWidget#InstanceItem {
    background-color: #4a4a4a;
}
QListWidget::item:selected QWidget#InstanceItem {
    background-color: #0078d7; /* Color principal vivo */
}
QListWidget::item:selected QLabel#InstanceName {
    color: #ffffff;
}

/* --- NUEVO: Indicador LED --- */
QLabel#LedIndicator {
    background-color: #6a6a6a; /* Gris (detenido) */
    border: 1px solid #777;
    border-radius: 6px; /* Círculo perfecto */
    min-width: 12px;
    max-width: 12px;
    min-height: 12px;
    max-height: 12px;
}
QLabel#LedIndicator[running="true"] {
    background-color: #4CAF50; /* Verde (ejecutando) */
    border: 1px solid #5cbf60;
}
QLabel#InstanceName {
    background-color: transparent;
    color: #f0f0f0; /* Color de texto explícito */
    font-size: 11pt;
    padding-left: 5px;
}

/* --- Pestañas de Consola (QTabWidget) --- */
QTabWidget::pane {
    border: 1px solid #4a4a4a;
    border-top: 1px solid #5a5a5a;
}
QTabBar::tab {
    background-color: #3c3c3c;
    color: #aaaaaa; /* Color de pestaña inactiva */
    padding: 8px 15px;
    border: 1px solid #4a4a4a;
    border-bottom: none; /* La pestaña seleccionada lo maneja */
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:hover {
    background-color: #4a4a4a;
    color: #f0f0f0;
}
QTabBar::tab:selected {
    background-color: #0078d7; /* Azul para pestaña activa */
    color: #ffffff; /* Color de pestaña activa */
    border-color: #4a4a4a;
    border-bottom-color: #0078d7; /* Para que se funda con el pane */
}
QTabBar::close-button {
    padding: 2px;
    border-radius: 2px;
}
QTabBar::close-button:hover {
    background: #5a5a5a;
}

/* --- NUEVO: Botón Play/Stop en la lista --- */
QListWidget QPushButton {
    background-color: #5a5a5a;
    border: none;
    border-radius: 5px;
    padding: 0px; /* Eliminar padding */
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}
QListWidget QPushButton:hover {
    background-color: #6a6a6a;
}
QListWidget::item:selected QPushButton {
    background-color: #008bf8; /* Azul más claro al seleccionar */
}

/* --- Botones (Generales) --- */
QPushButton {
    background-color: #0078d7;
    color: #ffffff;
    border: none;
    padding: 10px 15px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #008bf8;
}
QPushButton:pressed {
    background-color: #006ac1;
}
QPushButton#SecondaryButton {
    background-color: #5a5a5a;
}
QPushButton#SecondaryButton:hover {
    background-color: #6a6a6a;
}
QPushButton#SecondaryButton:pressed {
    background-color: #4a4a4a;
}
/* --- Área Principal --- */
#MainContent { background-color: #2b2b2b; }
QStackedWidget { background-color: #2b2b2b; }
QPlainTextEdit {
    background-color: #003366; /* Azul oscuro para el editor */
    color: #dcdcdc;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10pt;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 10px;
}
QFrame[isHeader="true"] {
    background-color: #3c3c3c;
    border-bottom: 1px solid #4a4a4a;
    border-radius: 0px;
}

/* --- Styles for Console-Specific Widgets --- */
#ConsoleToolbar {
    background-color: #3c3c3c;
    border-bottom: 1px solid #4a4a4a;
}
#ConsoleToolbar QPushButton {
    padding: 5px 10px;
    min-width: 28px;
}
#OutputConsole {
    background-color: #1e1e1e;
    border: none;
    padding: 5px;
}
#CommandEditor {
    background-color: #002b4d; /* Dark Blue */
    color: #e0e0e0;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11pt;
    padding: 10px;
    border-radius: 5px;
}

/* --- NUEVO: Estilos de Alarma --- */
#OutputConsole[alarm="true"] {
    background-color: #cc0000; /* Rojo oscuro */
}
QLabel#LedIndicator[alarm="true"] {
    background-color: #ff4500; /* Naranja-Rojo */
    border: 1px solid #ff6347;
}

"""

# --- NUEVO: Widget Personalizado para la Lista ---
class InstanceListItemWidget(QWidget):
    """
    Widget personalizado para mostrar en QListWidget.
    Contiene: [LED] [Nombre de Instancia] [Botón Play/Stop]
    """
    edit_requested = Signal(str) # instance_id
    delete_requested = Signal(str) # instance_id
    def __init__(self, instance_name, instance_id, manager_window):
        super().__init__()
        self.instance_id = instance_id
        self.manager = manager_window
        self.setObjectName("InstanceItem")
        self.setMinimumHeight(38) # Altura fija para consistencia
        
        self.alarm_timer = QTimer(self)
        self.alarm_timer.setInterval(500)
        self.alarm_timer.timeout.connect(self._toggle_alarm_style)
        self.active_alarms = set()

        grid_layout = QGridLayout(self)
        grid_layout.setContentsMargins(5, 2, 5, 2)
        grid_layout.setHorizontalSpacing(8)

        self.led = QLabel()
        self.led.setObjectName("LedIndicator")
        grid_layout.addWidget(self.led, 0, 0)

        self.name_label = QLabel(instance_name)
        self.name_label.setObjectName("InstanceName")
        grid_layout.addWidget(self.name_label, 0, 1)

        self.start_stop_button = QPushButton()
        self.start_stop_button.setFocusPolicy(Qt.NoFocus)
        self.start_stop_button.clicked.connect(self.on_button_clicked)
        grid_layout.addWidget(self.start_stop_button, 0, 2)

        self.delete_button = QPushButton()
        self.delete_button.setFocusPolicy(Qt.NoFocus)
        icon, _ = get_icon_or_text("trash", "X")
        self.delete_button.setIcon(icon)
        self.delete_button.setToolTip("Eliminar instancia")
        self.delete_button.clicked.connect(self.on_delete_clicked)
        grid_layout.addWidget(self.delete_button, 0, 3)

        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnMinimumWidth(0, 12)
        grid_layout.setColumnMinimumWidth(2, 28)
        grid_layout.setColumnMinimumWidth(3, 28)

        self.set_running_state(False)

    def set_running_state(self, is_running):
        self.led.setProperty("running", is_running)
        self.style().polish(self.led)
        if not is_running:
            self.set_alarm_state(0, False) # Clear all alarms when stopped
        
        if is_running:
            icon, _ = get_icon_or_text("stop", "S")
            self.start_stop_button.setIcon(icon)
            self.start_stop_button.setToolTip("Detener instancia")
        else:
            icon, _ = get_icon_or_text("play", "P")
            self.start_stop_button.setIcon(icon)
            self.start_stop_button.setToolTip("Iniciar instancia")

    def set_alarm_state(self, command_index, is_alarming):
        if is_alarming:
            self.active_alarms.add(command_index)
            if not self.alarm_timer.isActive():
                self.alarm_timer.start()
        else:
            self.active_alarms.discard(command_index)
            if not self.active_alarms and self.alarm_timer.isActive():
                self.alarm_timer.stop()
                self.led.setProperty("alarm", False)
                self.style().polish(self.led)

    def _toggle_alarm_style(self):
        is_alarm_on = self.led.property("alarm")
        self.led.setProperty("alarm", not is_alarm_on)
        self.style().polish(self.led)

    def on_button_clicked(self):
        """Maneja el clic en el botón Play/Stop."""
        is_running = self.manager.is_instance_running(self.instance_id)
        
        # Seleccionar este item en la lista principal
        self.manager.select_instance_by_id(self.instance_id)

        if is_running:
            self.manager.stop_instance() # stop_instance usa el current_instance_id
        else:
            self.manager.start_instance() # start_instance usa el current_instance_id

    def on_delete_clicked(self):
        """Maneja el clic en el botón de eliminar."""
        self.delete_requested.emit(self.instance_id)

    def set_name(self, new_name):
        self.name_label.setText(new_name)


# --- NUEVO: Widget de Pestaña de Consola Interactiva ---
class ConsoleTabWidget(QWidget):
    """
    Widget for a single console, with its own controls and editor.
    """
    command_entered = Signal(str)
    open_externally_requested = Signal()
    stop_requested = Signal(int)
    start_requested = Signal(int)
    restart_requested = Signal(int, str)
    alarm_triggered = Signal(str, int, bool) # instance_id, command_index, is_alarming

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_in_alarm_state = False
        self.alarm_timer = QTimer(self)
        self.alarm_timer.setInterval(500)
        self.alarm_timer.timeout.connect(self._toggle_alarm_style)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Toolbar
        toolbar = QWidget()
        toolbar.setObjectName("ConsoleToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(10)

        self.btn_start_stop = QPushButton()
        self.btn_start_stop.setCheckable(True)
        self.btn_start_stop.clicked.connect(self.on_start_stop_clicked)
        
        self.btn_edit = QPushButton("Editar")
        self.btn_edit.setCheckable(True)
        self.btn_edit.clicked.connect(self.toggle_edit_mode)
        self.btn_edit.setObjectName("SecondaryButton")

        self.btn_disable_alarm = QPushButton("Desactivar Alarma")
        self.btn_disable_alarm.setObjectName("SecondaryButton")
        self.btn_disable_alarm.clicked.connect(self.disable_alarm)
        self.btn_disable_alarm.hide()

        self.btn_save = QPushButton("Guardar")
        self.btn_save.setIcon(get_icon("save"))
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self.on_cancel_clicked)

        toolbar_layout.addWidget(self.btn_start_stop)
        toolbar_layout.addWidget(self.btn_edit)
        toolbar_layout.addWidget(self.btn_disable_alarm)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_cancel)
        toolbar_layout.addWidget(self.btn_save)

        main_layout.addWidget(toolbar)

        # 2. Stacked Widget for Console/Editor
        self.stack = QStackedWidget()
        
        # Page 0: Console View
        console_page = QWidget()
        console_layout = QVBoxLayout(console_page)
        console_layout.setContentsMargins(0,0,0,0)
        console_layout.setSpacing(2)
        self.output_console = QPlainTextEdit()
        self.output_console.setObjectName("OutputConsole") # For specific styling
        self.output_console.setReadOnly(True)
        
        bottom_bar = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(0,0,0,0)
        bottom_layout.setSpacing(2)
        self.input_line = QLineEdit()
        self.input_line.returnPressed.connect(self.handle_input)
        self.external_button = QPushButton()
        self.external_button.setIcon(get_icon("external-link"))
        self.external_button.setToolTip("Abrir en una ventana de CMD externa")
        self.external_button.setFixedSize(32, 32)
        self.external_button.setObjectName("SecondaryButton")
        self.external_button.clicked.connect(self.open_externally_requested.emit)
        bottom_layout.addWidget(self.input_line)
        bottom_layout.addWidget(self.external_button)

        console_layout.addWidget(self.output_console)
        console_layout.addWidget(bottom_bar)
        
        # Page 1: Editor View
        self.command_editor = QPlainTextEdit()
        self.command_editor.setObjectName("CommandEditor")
        
        self.stack.addWidget(console_page)
        self.stack.addWidget(self.command_editor)

        main_layout.addWidget(self.stack)

        self.toggle_edit_mode(False)

    def on_start_stop_clicked(self):
        command_index = self.property("command_index")
        if self.btn_start_stop.isChecked():
            self.stop_requested.emit(command_index)
        else:
            self.reset_alarm_state() # Reset alarm on manual start
            self.start_requested.emit(command_index)

    def toggle_edit_mode(self, edit_on):
        self.btn_edit.setChecked(edit_on)
        if edit_on:
            original_command = self.property("command")
            self.command_editor.setPlainText(original_command if original_command else "")
            self.stack.setCurrentIndex(1)
            self.btn_save.show()
            self.btn_cancel.show()
            self.btn_start_stop.hide()
            self.btn_edit.setText("Ver Consola")
        else:
            self.stack.setCurrentIndex(0)
            self.btn_save.hide()
            self.btn_cancel.hide()
            self.btn_start_stop.show()
            self.btn_edit.setText("Editar")

    def on_save_clicked(self):
        command_index = self.property("command_index")
        new_command = self.command_editor.toPlainText().strip()
        self.restart_requested.emit(command_index, new_command)
        self.toggle_edit_mode(False)

    def on_cancel_clicked(self):
        self.toggle_edit_mode(False)

    def handle_input(self):
        command = self.input_line.text().strip()
        if command:
            self.command_entered.emit(command)
            self.input_line.clear()

    def add_output(self, text):
        self.output_console.insertPlainText(text)
        self.output_console.moveCursor(QTextCursor.End)

    def set_focus_on_input(self):
        self.input_line.setFocus()

    def set_running_state(self, is_running):
        self.btn_start_stop.setChecked(is_running)
        if is_running:
            self.btn_start_stop.setIcon(get_icon("stop"))
            self.btn_start_stop.setText("Detener")
            self.input_line.setReadOnly(False)
            self.input_line.setPlaceholderText("Escriba un comando y presione Enter...")
            self.btn_edit.setEnabled(True)
        else:
            self.btn_start_stop.setIcon(get_icon("play"))
            self.btn_start_stop.setText("Iniciar")
            self.input_line.setReadOnly(True)
            self.input_line.setPlaceholderText("Proceso terminado. Presione Iniciar para reactivar.")
            self.btn_edit.setEnabled(True) # Allow editing even when stopped

    def trigger_alarm(self):
        if self.is_in_alarm_state: return
        self.is_in_alarm_state = True
        self.alarm_timer.start()
        self.btn_disable_alarm.show()
        self.alarm_triggered.emit(self.property("instance_id"), self.property("command_index"), True)

    def disable_alarm(self):
        if not self.is_in_alarm_state: return
        self.is_in_alarm_state = False
        self.alarm_timer.stop()
        self.output_console.setProperty("alarm", False)
        self.style().polish(self.output_console)
        self.btn_disable_alarm.hide()
        self.alarm_triggered.emit(self.property("instance_id"), self.property("command_index"), False)

    def reset_alarm_state(self):
        self.disable_alarm()

    def _toggle_alarm_style(self):
        is_alarm_on = self.output_console.property("alarm")
        self.output_console.setProperty("alarm", not is_alarm_on)
        self.style().polish(self.output_console)


# --- Ventana Principal (Modificada) ---
class InstanceManager(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Instance Manager")
        self.setGeometry(100, 100, 1200, 700)
        self.settings = QSettings("MyCompany", "InstanceManager")
        self.base_instances_dir = os.path.join(os.getcwd(), "instances")
        if not os.path.exists(self.base_instances_dir):
            os.makedirs(self.base_instances_dir)

        self.running_processes = {}
        self.console_widgets = {}
        self.instance_widgets = {}
        self.current_instance_id = None
        self.is_gallery_mode = False

        self.init_ui()
        self.load_instances()
        
        self.setStyleSheet(DARK_STYLESHEET)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left Menu
        left_menu = QWidget()
        left_menu.setObjectName("LeftMenu")
        left_menu.setMaximumWidth(300)
        left_menu_layout = QVBoxLayout(left_menu)
        left_menu_layout.setContentsMargins(10, 10, 10, 10)
        left_menu_layout.setSpacing(10)

        title_label = QLabel("INSTANCIAS")
        title_label.setAlignment(Qt.AlignCenter)
        left_menu_layout.addWidget(title_label)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton()
        icon, text = get_icon_or_text("add", "Crear")
        self.btn_add.setIcon(icon)
        self.btn_add.setText(text)
        self.btn_add.setToolTip("Crear nueva instancia")
        self.btn_add.clicked.connect(self.create_new_instance)
        
        self.btn_rename = QPushButton()
        icon, text = get_icon_or_text("edit", "Renombrar")
        self.btn_rename.setIcon(icon)
        self.btn_rename.setText(text)
        self.btn_rename.setToolTip("Renombrar instancia seleccionada")
        self.btn_rename.setObjectName("SecondaryButton")
        self.btn_rename.clicked.connect(self.rename_instance)

        self.btn_delete = QPushButton()
        icon, text = get_icon_or_text("trash", "Eliminar")
        self.btn_delete.setIcon(icon)
        self.btn_delete.setText(text)
        self.btn_delete.setToolTip("Eliminar instancia seleccionada")
        self.btn_delete.setObjectName("SecondaryButton")
        self.btn_delete.clicked.connect(lambda: self.delete_instance(self.current_instance_id))
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_rename)
        btn_layout.addWidget(self.btn_delete)
        left_menu_layout.addLayout(btn_layout)
        
        self.instance_list = QListWidget()
        self.instance_list.setIconSize(QSize(20, 20))
        self.instance_list.itemClicked.connect(self.on_instance_selected_by_click)
        left_menu_layout.addWidget(self.instance_list)
        
        main_layout.addWidget(left_menu)

        # Main Content Area
        main_content = QWidget()
        main_content.setObjectName("MainContent")
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)
        
        # Header
        self.content_header = QFrame()
        self.content_header.setProperty("isHeader", True)
        self.content_header.setFixedHeight(60)
        header_layout = QHBoxLayout(self.content_header)
        header_layout.setContentsMargins(15, 5, 15, 5)

        self.instance_title_label = QLabel("Seleccione una instancia")
        self.instance_title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        
        self.btn_edit_txt = QPushButton()
        icon, text = get_icon_or_text("edit_txt", "Editar .txt")
        self.btn_edit_txt.setIcon(icon)
        self.btn_edit_txt.setText(text)
        self.btn_edit_txt.setToolTip("Editar comandos.txt")
        self.btn_edit_txt.setObjectName("SecondaryButton")
        self.btn_edit_txt.clicked.connect(self.edit_txt_file)

        self.btn_gallery_mode = QPushButton()
        icon, text = get_icon_or_text("gallery", "Galería")
        self.btn_gallery_mode.setIcon(icon)
        self.btn_gallery_mode.setText(text)
        self.btn_gallery_mode.setToolTip("Activar/Desactivar modo galería")
        self.btn_gallery_mode.setObjectName("SecondaryButton")
        self.btn_gallery_mode.setCheckable(True)
        self.btn_gallery_mode.clicked.connect(self.toggle_gallery_mode)

        header_layout.addWidget(self.instance_title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_gallery_mode)
        header_layout.addWidget(self.btn_edit_txt)
        
        self.btn_edit_txt.hide()
        self.btn_gallery_mode.hide()
        self.btn_rename.setEnabled(False)
        self.btn_delete.setEnabled(False)

        main_content_layout.addWidget(self.content_header)

        # Command Detail Label
        self.command_detail_label = QLabel("")
        self.command_detail_label.setStyleSheet("color: #aaaaaa; padding: 0 15px 5px 15px; font-style: italic;")
        self.command_detail_label.hide()
        main_content_layout.addWidget(self.command_detail_label)

        # Main Stack (for switching between views)
        self.main_stack = QStackedWidget()
        
        # View 0: Console View (which itself is a stack of tabs vs gallery)
        console_view_widget = QWidget()
        console_view_layout = QVBoxLayout(console_view_widget)
        console_view_layout.setContentsMargins(0,0,0,0)
        self.view_stack = QStackedWidget()
        
        self.console_tabs = QTabWidget()
        self.console_tabs.setTabsClosable(True)
        self.console_tabs.tabCloseRequested.connect(self.close_console_tab)
        self.console_tabs.setTabShape(QTabWidget.Rounded)
        self.console_tabs.currentChanged.connect(self.on_tab_changed)
        
        self.gallery_widget = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_widget)

        self.view_stack.addWidget(self.console_tabs)
        self.view_stack.addWidget(self.gallery_widget)
        console_view_layout.addWidget(self.view_stack)
        
        # View 1: Text Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(15, 15, 15, 15)
        editor_layout.setSpacing(10)
        
        self.editor_input = QPlainTextEdit()
        self.editor_input.setPlaceholderText("Escribe aquí tus comandos, uno por línea.")
        editor_layout.addWidget(self.editor_input)
        
        self.btn_save_restart = QPushButton()
        icon, text = get_icon_or_text("save", "Guardar y Reiniciar")
        self.btn_save_restart.setIcon(icon)
        self.btn_save_restart.setText(text)
        self.btn_save_restart.clicked.connect(self.save_and_restart)
        
        self.btn_cancel_edit = QPushButton("Cancelar")
        self.btn_cancel_edit.setObjectName("SecondaryButton")
        self.btn_cancel_edit.clicked.connect(self.cancel_edit)
        
        editor_btn_layout = QHBoxLayout()
        editor_btn_layout.addStretch()
        editor_btn_layout.addWidget(self.btn_cancel_edit)
        editor_btn_layout.addWidget(self.btn_save_restart)
        editor_layout.addLayout(editor_btn_layout)

        # View 2: Placeholder
        placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_label = QLabel("← Selecciona o crea una instancia para comenzar")
        placeholder_label.setStyleSheet("font-size: 16pt; color: #7a7a7a;")
        placeholder_layout.addWidget(placeholder_label)

        self.main_stack.addWidget(console_view_widget) # Index 0
        self.main_stack.addWidget(editor_widget)      # Index 1
        self.main_stack.addWidget(placeholder_widget) # Index 2
        
        self.main_stack.setCurrentIndex(2) 
        
        main_content_layout.addWidget(self.main_stack)
        main_layout.addWidget(main_content)

        self.setCentralWidget(main_widget)

    # --- Lógica de Gestión de Instancias ---

    def create_new_instance(self):
        instance_name, ok = QInputDialog.getText(self, "Crear Instancia", "Nombre de la nueva instancia:")
        if ok and instance_name:
            instance_id = str(uuid.uuid4())
            instance_path = os.path.join(self.base_instances_dir, instance_id)
            try:
                os.makedirs(instance_path)
                default_cmd_file = os.path.join(instance_path, "comandos.txt")
                with open(default_cmd_file, 'w', encoding='utf-8') as f:
                    f.write("# Ejemplo de comando:\n")
                    f.write("echo Hola! Esta es tu nueva instancia.\n")
                    f.write("ping 127.0.0.1 -n 5\n") 
                self.settings.setValue(f"instances/{instance_id}", instance_name)
                self.add_instance_to_list(instance_name, instance_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la instancia: {e}")

    def rename_instance(self):
        item = self.instance_list.currentItem()
        if not item: return
            
        instance_id = item.data(Qt.UserRole)
        widget = self.instance_widgets[instance_id]
        old_name = widget.name_label.text()
        
        new_name, ok = QInputDialog.getText(self, "Renombrar Instancia", "Nuevo nombre:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            self.settings.setValue(f"instances/{instance_id}", new_name)
            widget.set_name(new_name) # Actualizar el nombre en el widget
            if self.current_instance_id == instance_id:
                self.instance_title_label.setText(new_name)

    def delete_instance(self, instance_id):
        widget = self.instance_widgets.get(instance_id)
        if not widget:
            return

        instance_name = widget.name_label.text()
        reply = QMessageBox.question(self, "Eliminar Instancia",
                                     f"¿Estás seguro de que quieres eliminar la instancia '{instance_name}'?\n¡Esta acción no se puede deshacer!",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 1. Detener si se está ejecutando
            if self.is_instance_running(instance_id):
                self.stop_instance_by_id(instance_id)

            # 2. Eliminar de la lista y del diccionario de widgets
            for i in range(self.instance_list.count()):
                item = self.instance_list.item(i)
                if item.data(Qt.UserRole) == instance_id:
                    self.instance_list.takeItem(i)
                    break
            
            if instance_id in self.instance_widgets:
                del self.instance_widgets[instance_id]

            # 3. Eliminar de QSettings
            self.settings.remove(f"instances/{instance_id}")

            # 4. Eliminar la carpeta de la instancia
            instance_path = os.path.join(self.base_instances_dir, instance_id)
            if os.path.exists(instance_path):
                try:
                    shutil.rmtree(instance_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar la carpeta de la instancia: {e}")

            # 5. Resetear la vista si la instancia eliminada era la actual
            if self.current_instance_id == instance_id:
                self.current_instance_id = None
                self.instance_title_label.setText("Seleccione una instancia")
                self.main_stack.setCurrentIndex(2) # Placeholder
                self.btn_edit_txt.hide()
                self.btn_rename.setEnabled(False)
                self.btn_delete.setEnabled(False)


    def load_instances(self):
        for key in self.settings.allKeys():
            if key.startswith("instances/"):
                instance_id = key.split('/', 1)[1]
                instance_name = self.settings.value(key)
                instance_dir = os.path.join(self.base_instances_dir, instance_id)
                if os.path.exists(instance_dir):
                    self.add_instance_to_list(instance_name, instance_id)
                else:
                    # Si la carpeta no existe, eliminamos la entrada de la configuración
                    self.settings.remove(key)

    def add_instance_to_list(self, name, instance_id):
        item = QListWidgetItem(self.instance_list)
        item.setData(Qt.UserRole, instance_id)
        
        widget = InstanceListItemWidget(name, instance_id, self)
        widget.delete_requested.connect(self.delete_instance)
        
        item.setSizeHint(widget.sizeHint())
        self.instance_list.addItem(item)
        self.instance_list.setItemWidget(item, widget)
        
        self.instance_widgets[instance_id] = widget

    def on_instance_selected_by_click(self, item):
        """Se llama cuando el usuario hace clic en un item de la lista."""
        instance_id = item.data(Qt.UserRole)
        self.set_current_instance(instance_id)

    def set_current_instance(self, instance_id):
        """Actualiza la UI para mostrar la instancia seleccionada."""
        if instance_id not in self.instance_widgets:
            return
            
        self.current_instance_id = instance_id
        widget = self.instance_widgets[instance_id]
        instance_name = widget.name_label.text()
        
        self.instance_title_label.setText(instance_name)
        
        self.btn_edit_txt.show()
        self.btn_gallery_mode.show()
        self.btn_rename.setEnabled(True)
        self.btn_delete.setEnabled(True)
        
        if self.main_stack.currentIndex() == 1:
            self.cancel_edit()
            
        self.main_stack.setCurrentIndex(0)
        self.rebuild_console_view()

    def close_console_tab(self, index):
        # This now needs to find the widget from the tab bar
        widget = self.console_tabs.widget(index)
        if not isinstance(widget, ConsoleTabWidget):
            self.console_tabs.removeTab(index)
            return

        instance_id = widget.property("instance_id")
        command_index = widget.property("command_index")

        if instance_id in self.running_processes and command_index in self.running_processes[instance_id]:
            process = self.running_processes[instance_id][command_index]
            process.kill()

        # The actual removal from dictionaries and UI is handled by on_process_finished
        # which will call rebuild_console_view
        self.console_tabs.removeTab(index)

    def toggle_gallery_mode(self):
        self.is_gallery_mode = self.btn_gallery_mode.isChecked()
        self.rebuild_console_view()

    def rebuild_console_view(self):
        """Clears and rebuilds the console area based on the current mode (tabs or gallery)."""
        # Clear both layouts
        self.console_tabs.clear()
        while self.gallery_layout.count():
            child = self.gallery_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

        if not self.current_instance_id:
            self.main_stack.setCurrentIndex(2) # Show placeholder
            return

        instance_id = self.current_instance_id
        console_widgets = self.console_widgets.get(instance_id, {})

        if not self.is_instance_running(instance_id):
            placeholder = QLabel(f"Instancia '{self.instance_widgets[instance_id].name_label.text()}' seleccionada. Presiona 'Play' para ejecutar.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("font-size: 14pt; color: #7a7a7a;")
            self.console_tabs.addTab(placeholder, "Info")
            self.console_tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)
            self.view_stack.setCurrentWidget(self.console_tabs)
            return

        if not console_widgets:
             self.view_stack.setCurrentWidget(self.console_tabs)
             return

        if self.is_gallery_mode:
            num_widgets = len(console_widgets)
            cols = 2 if num_widgets > 1 else 1
            rows = (num_widgets + cols - 1) // cols
            
            positions = [(row, col) for row in range(rows) for col in range(cols)]
            for (row, col), (idx, widget) in zip(positions, sorted(console_widgets.items())):
                self.gallery_layout.addWidget(widget, row, col)
            self.view_stack.setCurrentWidget(self.gallery_widget)
        else:
            for index in sorted(console_widgets.keys()):
                widget = console_widgets[index]
                title = widget.property("tab_title")
                self.console_tabs.addTab(widget, title)
            self.view_stack.setCurrentWidget(self.console_tabs)
            if self.console_tabs.count() > 0:
                self.console_tabs.currentWidget().set_focus_on_input()

    # --- Lógica de Ejecución de Instancias ---

    def start_instance(self):
        if not self.current_instance_id: return
        instance_id = self.current_instance_id
        widget = self.instance_widgets[instance_id]

        if self.is_instance_running(instance_id):
            QMessageBox.warning(self, "Aviso", "Esta instancia ya está en ejecución. Deténgala primero.")
            return

        instance_path = os.path.join(self.base_instances_dir, instance_id)
        cmd_file = os.path.join(instance_path, "comandos.txt")
        
        commands = []
        if os.path.exists(cmd_file):
            try:
                with open(cmd_file, 'r', encoding='utf-8') as f:
                    commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al leer comandos.txt: {e}")
                return

        if not commands:
            commands.append("")

        self.running_processes[instance_id] = {}
        self.console_widgets[instance_id] = {}

        for i, command in enumerate(commands):
            self.start_single_command(instance_id, i, command)

        widget.set_running_state(True)
        self.rebuild_console_view()
        self.on_tab_changed(self.console_tabs.currentIndex())

    def start_single_command(self, instance_id, command_index, command):
        """Inicia un único proceso de comando."""
        instance_path = os.path.join(self.base_instances_dir, instance_id)

        console_widget = ConsoleTabWidget()
        console_widget.setProperty("instance_id", instance_id)
        console_widget.setProperty("command_index", command_index)
        console_widget.setProperty("command", command)
        
        # Conectar todas las señales
        console_widget.command_entered.connect(self.on_command_entered)
        console_widget.open_externally_requested.connect(self.on_open_externally)
        console_widget.stop_requested.connect(self.handle_stop_requested)
        console_widget.start_requested.connect(self.handle_start_requested)
        console_widget.restart_requested.connect(self.handle_restart_requested)
        console_widget.alarm_triggered.connect(self.handle_alarm_triggered)

        console_widget.reset_alarm_state()

        self.console_widgets.setdefault(instance_id, {})[command_index] = console_widget

        if command:
            last_cmd = command.split('&&')[-1].strip()
            tab_title = self.get_short_command_name(last_cmd)
        else:
            tab_title = f"Consola {command_index+1}"
        console_widget.setProperty("tab_title", tab_title)

        process = QProcess()
        process.setProperty("instance_id", instance_id)
        process.setProperty("command_index", command_index)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(self.handle_stdout)
        process.finished.connect(self.on_process_finished)
        process.setWorkingDirectory(instance_path)
        
        self.running_processes.setdefault(instance_id, {})[command_index] = process
        
        process.start("cmd")
        if command:
            process.write((command + "\n").encode('utf-8'))
        
        console_widget.set_running_state(True)

    def handle_alarm_triggered(self, instance_id, command_index, is_alarming):
        if instance_id in self.instance_widgets:
            instance_widget = self.instance_widgets[instance_id]
            instance_widget.set_alarm_state(command_index, is_alarming)

    def handle_stop_requested(self, command_index):
        if self.current_instance_id and command_index in self.running_processes.get(self.current_instance_id, {}):
            process = self.running_processes[self.current_instance_id][command_index]
            process.kill()
            # on_process_finished se encargará del resto

    def handle_start_requested(self, command_index):
        if not self.current_instance_id: return
        instance_id = self.current_instance_id

        # Obtener el comando original del archivo
        instance_path = os.path.join(self.base_instances_dir, instance_id)
        cmd_file = os.path.join(instance_path, "comandos.txt")
        commands = []
        if os.path.exists(cmd_file):
            with open(cmd_file, 'r', encoding='utf-8') as f:
                commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        if command_index < len(commands):
            command_to_start = commands[command_index]
            # Eliminar el widget de consola viejo antes de crear uno nuevo
            if command_index in self.console_widgets.get(instance_id, {}):
                old_widget = self.console_widgets[instance_id].pop(command_index)
                old_widget.deleteLater()

            self.start_single_command(instance_id, command_index, command_to_start)
            self.rebuild_console_view()
        else:
            self.log_to_console_by_id(instance_id, f"Error: No se encontró el comando en el índice {command_index}.")

    def handle_restart_requested(self, command_index, new_command):
        if not self.current_instance_id: return
        instance_id = self.current_instance_id

        # 1. Actualizar el archivo comandos.txt
        self.update_command_in_file(instance_id, command_index, new_command)

        # 2. Detener el proceso actual si está corriendo
        if command_index in self.running_processes.get(instance_id, {}):
            process = self.running_processes[instance_id][command_index]
            process.kill() # Esto disparará on_process_finished

        # 3. Iniciar el nuevo comando
        self.handle_start_requested(command_index)

    def update_command_in_file(self, instance_id, command_index, new_command):
        instance_path = os.path.join(self.base_instances_dir, instance_id)
        cmd_file = os.path.join(instance_path, "comandos.txt")
        
        commands = []
        if os.path.exists(cmd_file):
            with open(cmd_file, 'r', encoding='utf-8') as f:
                commands = [line.strip() for line in f.readlines()] # Leer todas las líneas

        # Encontrar la línea de comando correcta para reemplazar
        current_command_idx = -1
        real_line_idx = -1
        for i, line in enumerate(commands):
            if line.strip() and not line.strip().startswith('#'):
                current_command_idx += 1
                if current_command_idx == command_index:
                    real_line_idx = i
                    break
        
        if real_line_idx != -1:
            commands[real_line_idx] = new_command
            try:
                with open(cmd_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(commands))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar comandos.txt: {e}")

    def on_command_entered(self, command):
        sender_widget = self.sender()
        if not sender_widget or not isinstance(sender_widget, ConsoleTabWidget):
            return

        instance_id = sender_widget.property("instance_id")
        command_index = sender_widget.property("command_index")

        if instance_id in self.running_processes and command_index in self.running_processes[instance_id]:
            process = self.running_processes[instance_id][command_index]
            process.write((command + "\n").encode('utf-8'))

    def on_open_externally(self):
        sender_widget = self.sender()
        if not isinstance(sender_widget, ConsoleTabWidget):
            return

        instance_id = sender_widget.property("instance_id")
        command = sender_widget.property("command")
        instance_path = os.path.join(self.base_instances_dir, instance_id)

        full_command = ["cmd.exe", "/k", command] if command else ["cmd.exe"]

        try:
            subprocess.Popen(full_command, cwd=instance_path, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la consola externa: {e}")
            return

        index = self.console_tabs.indexOf(sender_widget)
        if index != -1:
            self.close_console_tab(index)

    def on_tab_changed(self, index):
        if self.is_gallery_mode or index == -1:
            self.command_detail_label.hide()
            return

        current_widget = self.console_tabs.widget(index)
        if isinstance(current_widget, ConsoleTabWidget):
            command = current_widget.property("command")
            if command:
                self.command_detail_label.setText(f"Comando: {command}")
                self.command_detail_label.show()
            else:
                self.command_detail_label.hide()
        else:
            self.command_detail_label.hide()

    def stop_instance(self):
        if not self.current_instance_id: return
        self.stop_instance_by_id(self.current_instance_id)

    def stop_instance_by_id(self, instance_id):
        if instance_id in self.running_processes:
            for process in list(self.running_processes[instance_id].values()):
                process.kill()
            self.log_to_console_by_id(instance_id, "\n--- Señal de detención enviada a todos los procesos ---")
        else:
            self.log_to_console_by_id(instance_id, "La instancia no estaba en ejecución.")

    def handle_stdout(self):
        process = self.sender()
        if not process: return

        instance_id = process.property("instance_id")
        command_index = process.property("command_index")

        if instance_id in self.console_widgets and command_index in self.console_widgets[instance_id]:
            console_widget = self.console_widgets[instance_id][command_index]
            try:
                data = process.readAllStandardOutput()
                text = data.data().decode('cp850', errors='replace') 
            except Exception:
                text = data.data().decode('utf-8', errors='replace')
            
            console_widget.add_output(text)

            # --- Detección de Alarma ---
            lower_text = text.lower()
            if 'traceback' in lower_text or 'error' in lower_text:
                console_widget.trigger_alarm()

    def on_process_finished(self):
        process = self.sender()
        if not process: return

        instance_id = process.property("instance_id")
        command_index = process.property("command_index")

        if instance_id in self.console_widgets and command_index in self.console_widgets[instance_id]:
            console_widget = self.console_widgets[instance_id][command_index]
            console_widget.add_output(f"\n--- Proceso finalizado (Código: {process.exitCode()}) ---")
            console_widget.set_running_state(False)

        if instance_id in self.running_processes and command_index in self.running_processes[instance_id]:
            del self.running_processes[instance_id][command_index]
            
            if not self.running_processes[instance_id]:
                del self.running_processes[instance_id]
                if instance_id in self.instance_widgets:
                    self.instance_widgets[instance_id].set_running_state(False)
        
        process.deleteLater()

    def log_to_console(self, message, newline=True):
        # Este método necesita ser rediseñado para un entorno con pestañas.
        # Por ahora, no hacemos nada para evitar errores.
        pass

    def log_to_console_by_id(self, instance_id, message, newline=True):
        # Este método necesita ser rediseñado para un entorno con pestañas.
        # Por ahora, no hacemos nada para evitar errores.
        pass

    # --- Lógica de Edición de .txt ---

    def edit_txt_file(self):
        if not self.current_instance_id: return
        self.stop_instance()
        
        instance_id = self.current_instance_id
        instance_path = os.path.join(self.base_instances_dir, instance_id)
        cmd_file = os.path.join(instance_path, "comandos.txt")
        try:
            with open(cmd_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor_input.setPlainText(content)
            self.main_stack.setCurrentIndex(1)
            self.btn_edit_txt.setEnabled(False) # Deshabilitar mientras se edita
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo 'comandos.txt': {e}")

    def save_and_restart(self):
        if not self.current_instance_id: return
        instance_id = self.current_instance_id
        instance_path = os.path.join(self.base_instances_dir, instance_id)
        cmd_file = os.path.join(instance_path, "comandos.txt")
        content = self.editor_input.toPlainText()
        try:
            with open(cmd_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.main_stack.setCurrentIndex(0) 
            self.btn_edit_txt.setEnabled(True)
            self.start_instance()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo 'comandos.txt': {e}")

    def cancel_edit(self):
        self.main_stack.setCurrentIndex(0) 
        self.btn_edit_txt.setEnabled(True)

    # --- Funciones de Ayuda ---
    
    def is_instance_running(self, instance_id):
        """Comprueba si una instancia está en ejecución."""
        return instance_id in self.running_processes

    def select_instance_by_id(self, instance_id):
        """Selecciona un item en la lista basado en su ID."""
        for i in range(self.instance_list.count()):
            item = self.instance_list.item(i)
            if item.data(Qt.UserRole) == instance_id:
                self.instance_list.setCurrentItem(item)
                self.set_current_instance(instance_id) # Actualizar la UI
                return

    def get_short_command_name(self, command, max_len=25):
        """Acorta un comando para usarlo como título de pestaña."""
        if len(command) > max_len:
            return command[:max_len-3] + "..."
        return command

    def is_any_process_running(self):
        return bool(self.running_processes)

    def stop_all_processes(self):
        for instance_id in list(self.running_processes.keys()):
            self.stop_instance_by_id(instance_id)

    def closeEvent(self, event):
        if self.running_processes:
            reply = QMessageBox.question(self, "Procesos en ejecución",
                                         "Hay instancias en ejecución. ¿Desea detenerlas y salir?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                for process in self.running_processes.values():
                    process.kill()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    # Manejo de error de iconos
    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"Error al iniciar QApplication: {e}")
        print("Asegúrate de tener PySide6 instalado: pip install PySide6")
        sys.exit(1)
        
    window = InstanceManager()
    window.show()
    sys.exit(app.exec())