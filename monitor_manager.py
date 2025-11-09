import sys
import os
import uuid
import shutil
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QStackedWidget, QPlainTextEdit, QTabWidget, QLineEdit, QTabBar, QGridLayout,
    QMessageBox, QInputDialog, QLabel, QFrame, QListWidgetItem,
    QSizePolicy, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QProcess, QSettings, QSize, QByteArray, Signal, QProcessEnvironment
from PySide6.QtGui import QIcon, QFontDatabase, QPainter, QPixmap, QTextCursor
from PySide6.QtSvg import QSvgRenderer

# --- Script monitor.py (para copiarlo en nuevas instancias) ---
MONITOR_SCRIPT_CONTENT = """
import time
import shutil
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

# --- CONFIGURACIÓN ---
CONFIG_FILE = "config.txt"
# Diccionario para almacenar: {archivo_completo: (archivo_nombre, ruta_destino, ruta_backup)}
monitoreo_rutas = {}

def cargar_configuracion():
    \"\"\"Carga las reglas de monitoreo desde el archivo de configuración.\"\"\"
    global monitoreo_rutas
    monitoreo_rutas = {}
    
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Archivo de configuración '{CONFIG_FILE}' no encontrado.")
        print("Creando archivo de ejemplo...")
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write("# Formato: archivo.py | C:\\\\ruta\\\\origen | C:\\\\ruta\\\\destino | C:\\\\ruta\\\\backup\\n")
                f.write("ejemplo.txt | . | .\\\\destino | .\\\\backup\\n")
            print("Archivo de ejemplo creado. Edítalo y reinicia el monitor.")
        except Exception as e:
            print(f"No se pudo crear el config.txt: {e}")
        return False # Indicar que la carga falló

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                try:
                    # **Se esperan 4 valores**
                    archivo_nombre, ruta_origen, ruta_destino, ruta_backup = [p.strip() for p in line.split('|')]
                    
                    # Convertimos a objetos Path
                    ruta_origen = Path(ruta_origen)
                    ruta_destino = Path(ruta_destino)
                    ruta_backup = Path(ruta_backup)
                    
                    if not ruta_origen.is_dir():
                        print(f"Advertencia: Carpeta de origen no encontrada: {ruta_origen}")
                        continue
                        
                    # Creamos carpetas de destino y backup si no existen
                    ruta_destino.mkdir(parents=True, exist_ok=True)
                    ruta_backup.mkdir(parents=True, exist_ok=True)
                    
                    archivo_completo = ruta_origen / archivo_nombre
                    
                    if not archivo_completo.exists():
                        print(f"Advertencia: Archivo de origen no encontrado: {archivo_completo}")
                        continue

                    monitoreo_rutas[str(archivo_completo)] = (archivo_nombre, ruta_destino, ruta_backup)
                    print(f"Regla cargada: {archivo_nombre} -> Destino: {ruta_destino.name} | Backup: {ruta_backup.name}")
                    
                except ValueError:
                    print(f"Error de formato en la línea: '{line}'. Formato esperado: archivo.py | origen | destino | backup")
                    
    except Exception as e:
        print(f"Error inesperado al leer {CONFIG_FILE}: {e}")
        return False
        
    return True # Carga exitosa

def realizar_backup_inicial():
    \"\"\"Copia el archivo de origen a la carpeta de backup al inicio.\"\"\"
    print("\\n--- 💾 Iniciando Copia de Seguridad Inicial (Backup) ---")
    
    for src_path_str, (archivo_nombre, _, ruta_backup) in monitoreo_rutas.items():
        dst_path = ruta_backup / archivo_nombre
        src_path = Path(src_path_str)
        
        try:
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                print(f"   Backup Creado/Actualizado: {archivo_nombre} -> {dst_path}")
            else:
                print(f"   ❌ Error Backup: No se encontró el archivo de origen: {src_path}")
        except Exception as e:
            print(f"   ❌ Error al realizar el backup de {archivo_nombre}: {e}")

# ----------------------------------------------------

class FileChangeHandler(FileSystemEventHandler):
    \"\"\"Manejador de eventos que copia el archivo si detecta una modificación.\"\"\"

    def on_modified(self, event):
        if event.is_directory:
            return

        src_path_str = str(Path(event.src_path).resolve())
        
        # Normalizar las claves del diccionario para comparación
        claves_normalizadas = {str(Path(k).resolve()): k for k in monitoreo_rutas.keys()}
        
        if src_path_str in claves_normalizadas:
            key_original = claves_normalizadas[src_path_str]
            archivo_nombre, ruta_destino, _ = monitoreo_rutas[key_original]
            
            # --- Proceso de Copia a Destino ---
            dst_path = ruta_destino / archivo_nombre
            print(f"\\n⚙️ Cambio detectado en: {archivo_nombre}")
            
            try:
                # 1. Copiar y Reemplazar en la carpeta de DESTINO
                shutil.copy2(src_path_str, dst_path)
                
                # 2. Forzar actualización de marca de tiempo (para Uvicorn/reload)
                time.sleep(0.1) 
                os.utime(dst_path, None) 
                
                print(f"🎉 **Copiado a Destino exitoso**.")
                print(f"   Destino: {dst_path}")
                
            except Exception as e:
                print(f"❌ Error al copiar/actualizar la marca de tiempo a destino: {e}")

# ----------------------------------------------------

if __name__ == "__main__":
    print("--- Iniciando Monitor de Archivos ---")
    if not cargar_configuracion():
        print("Error al cargar la configuración. El monitor no se iniciará.")
        input("Presiona Enter para salir.")
        exit(1)
    
    if not monitoreo_rutas:
        print("El diccionario de monitoreo está vacío. Revisa tu config.txt.")
        input("Presiona Enter para salir.")
        exit(0)

    realizar_backup_inicial()
    
    event_handler = FileChangeHandler()
    observer = Observer()
    
    carpetas_a_observar = set()
    for ruta_completa in monitoreo_rutas.keys():
        carpetas_a_observar.add(str(Path(ruta_completa).parent.resolve()))

    print(f"\\nObservando {len(carpetas_a_observar)} carpetas:")
    for carpeta in carpetas_a_observar:
        print(f"  - {carpeta}")
        observer.schedule(event_handler, carpeta, recursive=True)

    print("\\n--- 🤖 Iniciando monitoreo... Presiona CTRL+C para detener. ---")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()
    print("--- Monitoreo detenido. ---")
"""


# --- Iconos SVG (Mismos iconos) ---
def get_icon(name):
    svg_data = {
        "add": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>""",
        "edit": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4L18.5 2.5z"></path></svg>""",
        "play": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>""",
        "stop": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>""",
        "save": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>""",
        # Renombrado para claridad
        "edit_config": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>""",
        "trash": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>""",
        "external-link": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>""",
        # Icono para buscar carpetas
        "folder": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>""",
        # Icono para buscar archivos
        "file": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>""",
        "copy": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>"""
    }
    # ... (código de get_icon sin cambios)
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
# --- ¡¡NUEVO TEMA ROSA!! ---
PINK_STYLESHEET = """
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
    padding: 0px; 
    margin-bottom: 5px;
    border-radius: 5px;
    color: #f0f0f0;
}
QWidget#InstanceItem {
    background-color: transparent;
    border-radius: 5px;
    padding: 5px 10px;
}
QListWidget::item:hover QWidget#InstanceItem {
    background-color: #4a4a4a;
}
QListWidget::item:selected QWidget#InstanceItem {
    background-color: #E91E63; /* Color principal ROSA */
}
QListWidget::item:selected QLabel#InstanceName {
    color: #ffffff;
}

/* --- Indicador LED --- */
QLabel#LedIndicator {
    background-color: #6a6a6a; /* Gris (detenido) */
    border: 1px solid #777;
    border-radius: 6px;
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
    color: #f0f0f0;
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
    color: #aaaaaa;
    padding: 8px 15px;
    border: 1px solid #4a4a4a;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:hover {
    background-color: #4a4a4a;
    color: #f0f0f0;
}
QTabBar::tab:selected {
    background-color: #E91E63; /* ROSA para pestaña activa */
    color: #ffffff;
    border-color: #4a4a4a;
    border-bottom-color: #E91E63;
}
QTabBar::close-button { padding: 2px; border-radius: 2px; }
QTabBar::close-button:hover { background: #5a5a5a; }

/* --- Botón Play/Stop en la lista --- */
QListWidget QPushButton {
    background-color: #5a5a5a;
    border: none;
    border-radius: 5px;
    padding: 0px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}
QListWidget QPushButton:hover {
    background-color: #6a6a6a;
}
QListWidget::item:selected QPushButton {
    background-color: #EC407A; /* ROSA más claro al seleccionar */
}

/* --- Botones (Generales) --- */
QPushButton {
    background-color: #E91E63; /* ROSA */
    color: #ffffff;
    border: none;
    padding: 10px 15px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #EC407A; /* ROSA hover */
}
QPushButton:pressed {
    background-color: #C2185B; /* ROSA pressed */
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

/* Consola de Salida (solo lectura) */
QPlainTextEdit {
    background-color: #1e1e1e;
    color: #dcdcdc;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10pt;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 10px;
}
/* Cabecera */
QFrame[isHeader="true"] {
    background-color: #3c3c3c;
    border-bottom: 1px solid #4a4a4a;
    border-radius: 0px;
}

/* --- NUEVO: Editor de Configuración --- */
#ConfigEditor {
    background-color: #2b2b2b;
    padding: 10px;
}
QScrollArea {
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    background-color: #1e1e1e;
}
#LinesContainer {
    background-color: #1e1e1e;
}
QFrame#ConfigLine {
    background-color: #3c3c3c;
    border: 1px solid #5a5a5a;
    border-radius: 5px;
    padding: 8px;
    margin-bottom: 5px;
}
QFrame#ConfigLine QLabel {
    font-size: 9pt;
    font-weight: bold;
    color: #aaaaaa;
    background-color: transparent;
    padding: 0;
}
QFrame#ConfigLine QLineEdit {
    background-color: #2b2b2b;
    border: 1px solid #5a5a5a;
    border-radius: 3px;
    padding: 5px;
    color: #f0f0f0;
}
QFrame#ConfigLine QPushButton {
    background-color: #5a5a5a;
    padding: 5px;
    min-width: 30px;
}
QFrame#ConfigLine QPushButton#DeleteButton {
    background-color: #C2185B; /* ROSA oscuro para borrar */
}
QPushButton#AddButton {
    font-size: 14pt;
    font-weight: bold;
    min-height: 40px;
}
"""

# --- Widget Personalizado de la Lista (Modificado para Delete) ---
class InstanceListItemWidget(QWidget):
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    def __init__(self, instance_name, instance_id, manager_window):
        # ... (código sin cambios de app_manager.py) ...
        super().__init__()
        self.instance_id = instance_id
        self.manager = manager_window
        self.setObjectName("InstanceItem")
        self.setMinimumHeight(38)
        
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
        # ... (código sin cambios de app_manager.py) ...
        self.led.setProperty("running", is_running)
        self.style().polish(self.led)
        
        if is_running:
            icon, _ = get_icon_or_text("stop", "S")
            self.start_stop_button.setIcon(icon)
            self.start_stop_button.setToolTip("Detener instancia")
        else:
            icon, _ = get_icon_or_text("play", "P")
            self.start_stop_button.setIcon(icon)
            self.start_stop_button.setToolTip("Iniciar instancia")

    def on_button_clicked(self):
        # ... (código sin cambios de app_manager.py) ...
        is_running = self.manager.is_instance_running(self.instance_id)
        self.manager.select_instance_by_id(self.instance_id)
        if is_running:
            self.manager.stop_instance()
        else:
            self.manager.start_instance()

    def on_delete_clicked(self):
        self.delete_requested.emit(self.instance_id)

    def set_name(self, new_name):
        self.name_label.setText(new_name)


# --- Widget de Pestaña de Consola (Modificado para solo salida) ---
class ConsoleTabWidget(QWidget):
    """
    Widget para una única pestaña de consola, AHORA SOLO MUESTRA SALIDA.
    """
    open_externally_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0) # Sin espacio

        self.output_console = QPlainTextEdit()
        self.output_console.setReadOnly(True)
        # El estilo se aplica desde el QSS global
        
        # Botón para abrir externamente (opcional)
        self.external_button = QPushButton()
        icon, _ = get_icon_or_text("external-link", "Ext")
        self.external_button.setIcon(icon)
        self.external_button.setToolTip("Abrir en una ventana de CMD externa")
        self.external_button.setFixedSize(28, 28)
        self.external_button.setStyleSheet("background-color: #4a4a4a; border-radius: 3px; margin: 3px;")
        self.external_button.clicked.connect(self.open_externally_requested.emit)
        
        # Layout para poner el botón en la esquina
        top_right_layout = QHBoxLayout()
        top_right_layout.addStretch()
        top_right_layout.addWidget(self.external_button)

        main_layout.addLayout(top_right_layout)
        main_layout.addWidget(self.output_console, 1) # Dar todo el espacio al output

    def add_output(self, text):
        self.output_console.insertPlainText(text)
        self.output_console.moveCursor(QTextCursor.End)


# --- NUEVO: Widget para una línea de Configuración ---
class ConfigLineWidget(QFrame):
    """
    Widget para editar una línea del config.txt:
    Archivo | Origen | Destino | Backup
    """
    delete_requested = Signal(object) # Envía una referencia a sí mismo
    duplicate_requested = Signal(object) # Envía una referencia a sí mismo

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConfigLine")
        
        layout = QGridLayout(self)
        layout.setSpacing(10)
        
        # --- Widgets ---
        self.file_label = QLabel("Archivo:")
        self.file_edit = QLineEdit()
        self.file_browse = QPushButton()
        self.file_browse.setIcon(get_icon("file"))
        
        self.origin_label = QLabel("Origen:")
        self.origin_edit = QLineEdit()
        self.origin_browse = QPushButton()
        self.origin_browse.setIcon(get_icon("folder"))

        self.dest_label = QLabel("Destino:")
        self.dest_edit = QLineEdit()
        self.dest_browse = QPushButton()
        self.dest_browse.setIcon(get_icon("folder"))
        
        self.backup_label = QLabel("Backup:")
        self.backup_edit = QLineEdit()
        self.backup_browse = QPushButton()
        self.backup_browse.setIcon(get_icon("folder"))
        
        self.delete_button = QPushButton()
        self.delete_button.setObjectName("DeleteButton")
        self.delete_button.setIcon(get_icon("trash"))
        self.delete_button.setToolTip("Eliminar esta línea")

        self.duplicate_button = QPushButton()
        self.duplicate_button.setIcon(get_icon("copy"))
        self.duplicate_button.setToolTip("Duplicar esta línea")

        # --- Layout ---
        # Fila 0: Archivo
        layout.addWidget(self.file_label, 0, 0)
        layout.addWidget(self.file_edit, 0, 1, 1, 3)
        layout.addWidget(self.file_browse, 0, 4)
        
        # Fila 0 y 1 para botones de acción
        action_button_layout = QVBoxLayout()
        action_button_layout.addWidget(self.delete_button)
        action_button_layout.addWidget(self.duplicate_button)
        layout.addLayout(action_button_layout, 0, 5, 2, 1, alignment=Qt.AlignTop)

        # Fila 1: Origen
        layout.addWidget(self.origin_label, 1, 0)
        layout.addWidget(self.origin_edit, 1, 1)
        layout.addWidget(self.origin_browse, 1, 2)
        
        # Fila 2: Destino y Backup
        layout.addWidget(self.dest_label, 2, 0)
        layout.addWidget(self.dest_edit, 2, 1)
        layout.addWidget(self.dest_browse, 2, 2)
        layout.addWidget(self.backup_label, 2, 3)
        layout.addWidget(self.backup_edit, 2, 4)
        layout.addWidget(self.backup_browse, 2, 5)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(4, 1)

        # --- Conexiones ---
        self.file_browse.clicked.connect(self.browse_file)
        self.origin_browse.clicked.connect(self.browse_origin)
        self.dest_browse.clicked.connect(self.browse_dest)
        self.backup_browse.clicked.connect(self.browse_backup)
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self))
        self.duplicate_button.clicked.connect(lambda: self.duplicate_requested.emit(self))
        
    def browse_file(self):
        # Usar el directorio de origen si ya está puesto, si no, el actual
        start_dir = self.origin_edit.text() if os.path.isdir(self.origin_edit.text()) else "."
        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo", start_dir)
        if filepath:
            # Intentar hacer la ruta relativa si es posible
            if start_dir != ".":
                try:
                    rel_path = os.path.relpath(filepath, start_dir)
                    self.file_edit.setText(rel_path)
                    self.origin_edit.setText(start_dir) # Asegurar que el origen está puesto
                    return
                except ValueError:
                    pass # Ocurre si están en discos diferentes
            
            # Fallback: poner ruta absoluta y path
            self.file_edit.setText(os.path.basename(filepath))
            self.origin_edit.setText(os.path.dirname(filepath))

    def browse_origin(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Origen")
        if dir_path:
            self.origin_edit.setText(dir_path)

    def browse_dest(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino")
        if dir_path:
            self.dest_edit.setText(dir_path)
            
    def browse_backup(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Backup")
        if dir_path:
            self.backup_edit.setText(dir_path)

    def get_config_line(self):
        """Devuelve la línea de configuración como string."""
        parts = [
            self.file_edit.text().strip(),
            self.origin_edit.text().strip(),
            self.dest_edit.text().strip(),
            self.backup_edit.text().strip()
        ]
        # Solo devolver si todos los campos están completos
        if all(parts):
            return " | ".join(parts)
        return None # Devolver None si está incompleta

    def set_config_line(self, line):
        """Rellena los campos desde un string."""
        try:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) == 4:
                self.file_edit.setText(parts[0])
                self.origin_edit.setText(parts[1])
                self.dest_edit.setText(parts[2])
                self.backup_edit.setText(parts[3])
        except Exception as e:
            print(f"Error al parsear línea de config: {e}")

# --- NUEVO: Widget Editor de Configuración ---
class ConfigEditorWidget(QWidget):
    """
    Widget que reemplaza al editor de texto.
    Muestra una lista de ConfigLineWidget.
    """
    save_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConfigEditor")
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # 1. Botón de Añadir
        self.btn_add_line = QPushButton("Añadir Nueva Línea de Monitoreo")
        self.btn_add_line.setObjectName("AddButton")
        self.btn_add_line.setIcon(get_icon("add"))
        self.btn_add_line.clicked.connect(self.add_config_line)
        main_layout.addWidget(self.btn_add_line)
        
        # 2. Área de Scroll para las líneas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.lines_container = QWidget() # Widget dentro del scroll
        self.lines_container.setObjectName("LinesContainer")
        self.lines_layout = QVBoxLayout(self.lines_container) # Layout de ese widget
        self.lines_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.lines_container)
        main_layout.addWidget(scroll_area, 1) # Darle todo el espacio
        
        # 3. Botones de Guardar/Cancelar
        self.btn_save_restart = QPushButton()
        icon, text = get_icon_or_text("save", "Guardar y Reiniciar")
        self.btn_save_restart.setIcon(icon)
        self.btn_save_restart.setText(text)
        self.btn_save_restart.setToolTip("Guarda config.txt y reinicia la instancia")
        self.btn_save_restart.clicked.connect(self.save_requested)
        
        self.btn_cancel_edit = QPushButton("Cancelar")
        self.btn_cancel_edit.setObjectName("SecondaryButton")
        self.btn_cancel_edit.clicked.connect(self.cancel_requested)
        
        editor_btn_layout = QHBoxLayout()
        editor_btn_layout.addStretch()
        editor_btn_layout.addWidget(self.btn_cancel_edit)
        editor_btn_layout.addWidget(self.btn_save_restart)
        main_layout.addLayout(editor_btn_layout)

    def add_config_line(self, line_content=None):
        """Añade un nuevo widget de línea, opcionalmente con contenido."""
        line_widget = ConfigLineWidget()
        if line_content:
            line_widget.set_config_line(line_content)
            
        line_widget.delete_requested.connect(self.remove_config_line)
        line_widget.duplicate_requested.connect(self.duplicate_config_line)
        self.lines_layout.addWidget(line_widget)
        
    def duplicate_config_line(self, line_widget_to_duplicate):
        """Duplica un widget de línea de configuración."""
        config_content = line_widget_to_duplicate.get_config_line()
        
        # Encontrar el índice del widget actual
        index = -1
        for i in range(self.lines_layout.count()):
            if self.lines_layout.itemAt(i).widget() == line_widget_to_duplicate:
                index = i
                break
                
        if index != -1:
            # Crear y configurar el nuevo widget
            new_line_widget = ConfigLineWidget()
            if config_content:
                new_line_widget.set_config_line(config_content)
            
            # Conectar señales
            new_line_widget.delete_requested.connect(self.remove_config_line)
            new_line_widget.duplicate_requested.connect(self.duplicate_config_line)
            
            # Insertar el nuevo widget debajo del original
            self.lines_layout.insertWidget(index + 1, new_line_widget)
        
    def remove_config_line(self, line_widget):
        """Elimina un widget de línea."""
        self.lines_layout.removeWidget(line_widget)
        line_widget.deleteLater()
        
    def load_config(self, file_path):
        """Lee el config.txt y puebla la lista."""
        # Limpiar líneas existentes
        while self.lines_layout.count():
            child = self.lines_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if not os.path.exists(file_path):
            print(f"No se encontró {file_path}, se creará al guardar.")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.add_config_line(line)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el config.txt: {e}")

    def save_config(self, file_path):
        """Recorre los widgets y guarda el config.txt."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Archivo de configuración del Monitor de Cambios\n")
                f.write("# Formato: archivo.py | C:\\ruta\\origen | C:\\ruta\\destino | C:\\ruta\\backup\n\n")
                
                for i in range(self.lines_layout.count()):
                    widget = self.lines_layout.itemAt(i).widget()
                    if widget:
                        line = widget.get_config_line()
                        if line: # Solo guardar si la línea es válida
                            f.write(line + "\n")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el config.txt: {e}")
            return False


# --- Ventana Principal (Modificada para el Monitor) ---
class MonitorManager(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitor Manager")
        self.setGeometry(100, 100, 1200, 700)
        self.settings = QSettings("MyCompany", "MonitorManager") # Nuevo nombre
        self.base_instances_dir = os.path.join(os.getcwd(), "monitor_instances") # Nueva carpeta
        if not os.path.exists(self.base_instances_dir):
            os.makedirs(self.base_instances_dir)

        self.running_processes = {} 
        self.console_widgets = {} 
        self.instance_widgets = {}  
        self.current_instance_id = None

        self.init_ui()
        self.load_instances()
        
        self.setStyleSheet(PINK_STYLESHEET) # ¡NUEVO TEMA!

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- 1. Menú Lateral Izquierdo ---
        left_menu = QWidget()
        left_menu.setObjectName("LeftMenu")
        left_menu.setMaximumWidth(300)
        left_menu_layout = QVBoxLayout(left_menu)
        left_menu_layout.setContentsMargins(10, 10, 10, 10)
        left_menu_layout.setSpacing(10)

        title_label = QLabel("INSTANCIAS (Monitor)") # Título cambiado
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
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_rename)
        left_menu_layout.addLayout(btn_layout)
        
        self.instance_list = QListWidget()
        self.instance_list.setIconSize(QSize(20, 20))
        self.instance_list.itemClicked.connect(self.on_instance_selected_by_click)
        left_menu_layout.addWidget(self.instance_list)
        
        main_layout.addWidget(left_menu)

        # --- 2. Área de Contenido Principal ---
        main_content = QWidget()
        main_content.setObjectName("MainContent")
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)
        
        # --- 2a. Cabecera del Contenido ---
        self.content_header = QFrame()
        self.content_header.setProperty("isHeader", True)
        self.content_header.setFixedHeight(60)
        header_layout = QHBoxLayout(self.content_header)
        header_layout.setContentsMargins(15, 5, 15, 5)

        self.instance_title_label = QLabel("Seleccione una instancia")
        self.instance_title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        
        # NUEVO Botón de Editar Config
        self.btn_edit_config = QPushButton()
        icon, text = get_icon_or_text("edit_config", "Editar Config")
        self.btn_edit_config.setIcon(icon)
        self.btn_edit_config.setText(text)
        self.btn_edit_config.setToolTip("Editar config.txt")
        self.btn_edit_config.setObjectName("SecondaryButton")
        self.btn_edit_config.clicked.connect(self.edit_config_file) # Conexión cambiada

        header_layout.addWidget(self.instance_title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_edit_config) # Botón cambiado
        
        self.btn_edit_config.hide()
        self.btn_rename.setEnabled(False)
        # El botón de eliminar está en el propio widget

        main_content_layout.addWidget(self.content_header)

        # --- 2ab. Etiqueta para Detalle de Comando ---
        self.command_detail_label = QLabel("")
        self.command_detail_label.setStyleSheet("color: #aaaaaa; padding: 0 15px 5px 15px; font-style: italic;")
        self.command_detail_label.hide()
        main_content_layout.addWidget(self.command_detail_label)

        # --- 2b. Stack de Vistas (Consola vs Editor) ---
        self.main_stack = QStackedWidget()
        
        # Vista 0: Consolas en Pestañas (igual)
        self.console_tabs = QTabWidget()
        self.console_tabs.setTabsClosable(True)
        self.console_tabs.tabCloseRequested.connect(self.close_console_tab)
        self.console_tabs.setTabShape(QTabWidget.Rounded)
        self.console_tabs.currentChanged.connect(self.on_tab_changed)
        
        # Vista 1: NUEVO Editor de Configuración
        self.config_editor = ConfigEditorWidget()
        self.config_editor.save_requested.connect(self.save_and_restart)
        self.config_editor.cancel_requested.connect(self.cancel_edit)

        # Placeholder inicial (Vista 2) (igual)
        placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_label = QLabel("← Selecciona o crea una instancia para comenzar")
        placeholder_label.setStyleSheet("font-size: 16pt; color: #7a7a7a;")
        placeholder_layout.addWidget(placeholder_label)

        self.main_stack.addWidget(self.console_tabs)   # Index 0
        self.main_stack.addWidget(self.config_editor) # Index 1
        self.main_stack.addWidget(placeholder_widget) # Index 2
        
        self.main_stack.setCurrentIndex(2) 
        
        main_content_layout.addWidget(self.main_stack)
        main_layout.addWidget(main_content)

        self.setCentralWidget(main_widget)

    # --- Lógica de Gestión de Instancias (MODIFICADA) ---

    def create_new_instance(self):
        instance_name, ok = QInputDialog.getText(self, "Crear Instancia de Monitor", "Nombre de la nueva instancia:")
        if ok and instance_name:
            instance_id = str(uuid.uuid4())
            instance_path = os.path.join(self.base_instances_dir, instance_id)
            try:
                os.makedirs(instance_path)
                
                # 1. Crear comandos.txt (para ejecutar el monitor)
                cmd_file = os.path.join(instance_path, "comandos.txt")
                with open(cmd_file, 'w', encoding='utf-8') as f:
                    # -u es CRÍTICO para que la salida de Python no se guarde en buffer
                    f.write("python -u monitor.py\n") 

                # 2. Crear el script monitor.py
                monitor_script_file = os.path.join(instance_path, "monitor.py")
                with open(monitor_script_file, 'w', encoding='utf-8') as f:
                    f.write(MONITOR_SCRIPT_CONTENT)
                
                # 3. Crear config.txt (el que se va a editar)
                config_file = os.path.join(instance_path, "config.txt")
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write("# Formato: archivo.py | C:\\ruta\\origen | C:\\ruta\\destino | C:\\ruta\\backup\n")
                    f.write("ejemplo.txt | . | .\\destino | .\\backup\n")

                self.settings.setValue(f"instances/{instance_id}", instance_name)
                self.add_instance_to_list(instance_name, instance_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la instancia: {e}")

    def rename_instance(self):
        # ... (código sin cambios de app_manager.py) ...
        item = self.instance_list.currentItem()
        if not item: return
        instance_id = item.data(Qt.UserRole)
        widget = self.instance_widgets[instance_id]
        old_name = widget.name_label.text()
        new_name, ok = QInputDialog.getText(self, "Renombrar Instancia", "Nuevo nombre:", text=old_name)
        if ok and new_name and new_name != old_name:
            self.settings.setValue(f"instances/{instance_id}", new_name)
            widget.set_name(new_name)
            if self.current_instance_id == instance_id:
                self.instance_title_label.setText(new_name)

    def delete_instance(self, instance_id):
        # ... (código sin cambios de app_manager.py) ...
        widget = self.instance_widgets.get(instance_id)
        if not widget: return
        instance_name = widget.name_label.text()
        reply = QMessageBox.question(self, "Eliminar Instancia",
                                     f"¿Estás seguro de que quieres eliminar '{instance_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.is_instance_running(instance_id):
                self.stop_instance_by_id(instance_id)
            for i in range(self.instance_list.count()):
                item = self.instance_list.item(i)
                if item.data(Qt.UserRole) == instance_id:
                    self.instance_list.takeItem(i)
                    break
            if instance_id in self.instance_widgets: del self.instance_widgets[instance_id]
            self.settings.remove(f"instances/{instance_id}")
            instance_path = os.path.join(self.base_instances_dir, instance_id)
            if os.path.exists(instance_path):
                try:
                    shutil.rmtree(instance_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar la carpeta: {e}")
            if self.current_instance_id == instance_id:
                self.current_instance_id = None
                self.instance_title_label.setText("Seleccione una instancia")
                self.main_stack.setCurrentIndex(2)
                self.btn_edit_config.hide()
                self.btn_rename.setEnabled(False)

    def load_instances(self):
        # ... (código sin cambios de app_manager.py) ...
        self.settings.beginGroup("instances")
        instance_ids = self.settings.childKeys()
        self.settings.endGroup()
        for instance_id in instance_ids:
            instance_name = self.settings.value(f"instances/{instance_id}")
            instance_dir = os.path.join(self.base_instances_dir, instance_id)
            if os.path.exists(instance_dir):
                self.add_instance_to_list(instance_name, instance_id)
            else:
                self.settings.remove(f"instances/{instance_id}")

    def add_instance_to_list(self, name, instance_id):
        # ... (código sin cambios de app_manager.py) ...
        item = QListWidgetItem(self.instance_list)
        item.setData(Qt.UserRole, instance_id)
        widget = InstanceListItemWidget(name, instance_id, self)
        widget.delete_requested.connect(self.delete_instance)
        item.setSizeHint(widget.sizeHint())
        self.instance_list.addItem(item)
        self.instance_list.setItemWidget(item, widget)
        self.instance_widgets[instance_id] = widget

    def on_instance_selected_by_click(self, item):
        instance_id = item.data(Qt.UserRole)
        self.set_current_instance(instance_id)

    def set_current_instance(self, instance_id):
        # ... (código sin cambios de app_manager.py) ...
        if instance_id not in self.instance_widgets:
            return
        self.current_instance_id = instance_id
        widget = self.instance_widgets[instance_id]
        instance_name = widget.name_label.text()
        self.instance_title_label.setText(instance_name)
        self.btn_edit_config.show() # Botón cambiado
        self.btn_rename.setEnabled(True)
        if self.main_stack.currentIndex() == 1:
            self.cancel_edit()
        self.main_stack.setCurrentIndex(0)
        try: self.console_tabs.tabCloseRequested.disconnect(self.close_console_tab) 
        except RuntimeError: pass
        self.console_tabs.clear()
        self.console_tabs.tabCloseRequested.connect(self.close_console_tab)
        if self.is_instance_running(instance_id):
            for index in sorted(self.console_widgets.get(instance_id, {}).keys()):
                tab_widget = self.console_widgets[instance_id][index]
                title = tab_widget.property("tab_title")
                self.console_tabs.addTab(tab_widget, title)
        else:
            placeholder = QLabel(f"Instancia '{instance_name}' lista. Presiona 'Play' para iniciar monitor.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("font-size: 14pt; color: #7a7a7a;")
            self.console_tabs.addTab(placeholder, "Info")
            self.console_tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

    def close_console_tab(self, index):
        # ... (código sin cambios de app_manager.py, adaptado para ConsoleTabWidget sin input) ...
        widget = self.console_tabs.widget(index)
        if not isinstance(widget, ConsoleTabWidget):
            self.console_tabs.removeTab(index)
            return
        instance_id = widget.property("instance_id")
        command_index = widget.property("command_index")
        if instance_id in self.running_processes and command_index in self.running_processes[instance_id]:
            process = self.running_processes[instance_id][command_index]
            process.kill()
        self.console_tabs.removeTab(index)

    # --- Lógica de Ejecución (MODIFICADA) ---

    def start_instance(self):
        # ... (lógica de app_manager.py, pero ConsoleTabWidget es el modificado) ...
        if not self.current_instance_id: return
        instance_id = self.current_instance_id
        widget = self.instance_widgets[instance_id]
        if self.is_instance_running(instance_id):
            QMessageBox.warning(self, "Aviso", "Esta instancia ya está en ejecución.")
            return

        instance_path = os.path.join(self.base_instances_dir, instance_id)
        cmd_file = os.path.join(instance_path, "comandos.txt")
        
        self.console_tabs.clear()
        commands = []
        if os.path.exists(cmd_file):
            try:
                with open(cmd_file, 'r', encoding='utf-8') as f:
                    commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al leer comandos.txt: {e}")
                return

        if not commands:
            QMessageBox.critical(self, "Error", "No hay comandos en comandos.txt. No se puede iniciar.")
            return

        self.running_processes[instance_id] = {}
        self.console_widgets[instance_id] = {}

        # Solo ejecutaremos el primer comando (debería ser 'python -u monitor.py')
        # Mantenemos la lógica de pestañas por si el usuario quiere añadir más comandos.
        for i, command in enumerate(commands):
            tab_widget = ConsoleTabWidget() # Usando el widget de solo salida
            tab_widget.setProperty("instance_id", instance_id)
            tab_widget.setProperty("command_index", i)
            tab_widget.setProperty("command", command)
            tab_widget.open_externally_requested.connect(self.on_open_externally)
            
            self.console_widgets[instance_id][i] = tab_widget
            
            # Título de la pestaña
            tab_title = "Monitor" if "monitor.py" in command else f"Proceso {i+1}"
            tab_widget.setProperty("tab_title", tab_title)
            self.console_tabs.addTab(tab_widget, tab_title)

            process = QProcess()
            process.setProperty("instance_id", instance_id)
            process.setProperty("command_index", i)
            process.setProcessChannelMode(QProcess.MergedChannels)
            process.readyReadStandardOutput.connect(self.handle_stdout)
            process.finished.connect(self.on_process_finished)
            process.setWorkingDirectory(instance_path)

            # Forzar UTF-8 para la salida del proceso de Python para evitar errores de códec
            env = QProcessEnvironment.systemEnvironment()
            env.insert("PYTHONIOENCODING", "utf-8")
            process.setProcessEnvironment(env)
            
            self.running_processes[instance_id][i] = process
            
            # Iniciar cmd y ejecutar comando
            process.start("cmd", ["/c", command]) # Usar /c para que cmd ejecute y se mantenga
            
            if not process.waitForStarted(3000):
                tab_widget.add_output(f"Error: No se pudo iniciar el proceso: {command}")

        widget.set_running_state(True)
        self.on_tab_changed(self.console_tabs.currentIndex())

    def on_open_externally(self):
        # ... (código sin cambios de app_manager.py) ...
        sender_widget = self.sender()
        if not isinstance(sender_widget, ConsoleTabWidget): return
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
        # ... (código sin cambios de app_manager.py) ...
        if index == -1:
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
        # ... (código sin cambios de app_manager.py) ...
        if instance_id in self.running_processes:
            for process in list(self.running_processes[instance_id].values()):
                # Enviar CTRL+C para detener monitor.py limpiamente
                # Esto es más complejo que kill(), pero lo intentamos
                # process.write(b'\\x03') # Simular CTRL+C
                process.kill() # Más simple y seguro
        else:
            pass # No hacer nada si no está corriendo

    def handle_stdout(self):
        # ... (código sin cambios de app_manager.py, pero usa ConsoleTabWidget modificado) ...
        process = self.sender()
        if not process: return
        instance_id = process.property("instance_id")
        command_index = process.property("command_index")
        if instance_id in self.console_widgets and command_index in self.console_widgets[instance_id]:
            tab_widget = self.console_widgets[instance_id][command_index]
            try:
                data = process.readAllStandardOutput()
                text = data.data().decode('utf-8', errors='replace')
            except Exception:
                text = data.data().decode('latin-1', errors='replace')
            tab_widget.add_output(text)

    def on_process_finished(self):
        # ... (código sin cambios de app_manager.py, pero usa ConsoleTabWidget modificado) ...
        process = self.sender()
        if not process: return
        instance_id = process.property("instance_id")
        command_index = process.property("command_index")
        if instance_id in self.console_widgets and command_index in self.console_widgets[instance_id]:
            tab_widget = self.console_widgets[instance_id][command_index]
            tab_widget.add_output(f"\n--- Proceso finalizado (Código: {process.exitCode()}) ---")
        if instance_id in self.running_processes and command_index in self.running_processes[instance_id]:
            del self.running_processes[instance_id][command_index]
            if not self.running_processes[instance_id]:
                del self.running_processes[instance_id]
                if instance_id in self.instance_widgets:
                    self.instance_widgets[instance_id].set_running_state(False)
        process.deleteLater()

    # --- Lógica de Edición (¡MODIFICADA!) ---

    def edit_config_file(self):
        """Abre el editor de config.txt."""
        if not self.current_instance_id: return
        
        # Detener la instancia antes de editar
        if self.is_instance_running(self.current_instance_id):
            self.stop_instance()
        
        instance_id = self.current_instance_id
        instance_path = os.path.join(self.base_instances_dir, instance_id)
        config_file = os.path.join(instance_path, "config.txt")
        
        try:
            self.config_editor.load_config(config_file)
            self.main_stack.setCurrentIndex(1) # Cambiar al editor
            self.btn_edit_config.setEnabled(False) 
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar 'config.txt': {e}")

    def save_and_restart(self):
        """Guarda desde el ConfigEditor y reinicia."""
        if not self.current_instance_id: return
        
        instance_id = self.current_instance_id
        instance_path = os.path.join(self.base_instances_dir, instance_id)
        config_file = os.path.join(instance_path, "config.txt")
        
        if self.config_editor.save_config(config_file):
            self.main_stack.setCurrentIndex(0) 
            self.btn_edit_config.setEnabled(True)
            self.start_instance() # Reiniciar
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar la configuración. No se reiniciará.")

    def cancel_edit(self):
        self.main_stack.setCurrentIndex(0) 
        self.btn_edit_config.setEnabled(True)

    # --- Funciones de Ayuda (sin cambios) ---
    
    def is_instance_running(self, instance_id):
        return instance_id in self.running_processes

    def select_instance_by_id(self, instance_id):
        for i in range(self.instance_list.count()):
            item = self.instance_list.item(i)
            if item.data(Qt.UserRole) == instance_id:
                self.instance_list.setCurrentItem(item)
                self.set_current_instance(instance_id)
                return

    def is_any_process_running(self):
        return bool(self.running_processes)

    def stop_all_processes(self):
        for instance_id in list(self.running_processes.keys()):
            self.stop_instance_by_id(instance_id)

    def closeEvent(self, event):
        if self.running_processes:
            reply = QMessageBox.question(self, "Procesos en ejecución",
                                         "Hay monitores en ejecución. ¿Desea detenerlos y salir?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Usar list() para evitar error de tamaño de diccionario cambiado
                for instance_id in list(self.running_processes.keys()):
                    self.stop_instance_by_id(instance_id)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"Error al iniciar QApplication: {e}")
        print("Asegúrate de tener PySide6 instalado: pip install PySide6")
        sys.exit(1)
        
    window = MonitorManager()
    window.show()
    sys.exit(app.exec())