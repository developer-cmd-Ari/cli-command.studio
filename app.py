import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QStackedWidget, QPlainTextEdit,
    QMessageBox, QLabel, QFrame, QListWidgetItem
)
from PySide6.QtCore import Qt, QSettings, QSize, QByteArray
from PySide6.QtGui import QIcon, QFontDatabase, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# --- Importar los widgets de los otros archivos ---
# (Asegúrate de que los archivos 'app_manager.py' y 
# 'monitor_manager.py' estén en la misma carpeta)
try:
    from app_manager import InstanceManager
    from monitor_manager import MonitorManager
    from docker_manager import DockerManagerWidget, ConfigManager, DockerService, LoginDialog
    from github_manager import GitHubManagerWidget
    from file_manager import FileManagerWidget
except ImportError as e:
    print(f"Error: No se pudieron importar los gestores.")
    print(f"Asegúrate de que 'app_manager.py' y 'monitor_manager.py' existan.")
    print(f"Detalle: {e}")
    sys.exit(1)


# --- Iconos SVG (Incluyendo los nuevos para la navegación) ---

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
        "folder": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>""",
        "file": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>""",
        "edit_config": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>""",
        # --- Nuevos iconos para el HUB ---
        "apps": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>""",
        "monitor": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>""",
        "docker": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.3 13.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5s-2.8-1.1-2.8-2.5c0-.5.1-.9.4-1.3l-2.2-1.2c-.3.4-.7.7-1.2.9v2.2c.5.2 1 .6 1.4 1.1.4.5.6 1.1.6 1.7 0 1.4-1.3 2.5-2.8 2.5s-2.8-1.1-2.8-2.5c0-.6.2-1.2.6-1.7.4-.5.9-.9 1.4-1.1v-2.2c-.5-.2-1-.5-1.2-.9L9.3 13.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3""",
        "github": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>""",
        "file_manager": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-file-text"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>"""
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
# --- ¡¡NUEVO TEMA TURQUESA (Y COMPLETO)!! ---
# Este QSS contiene TODOS los estilos para el Hub y los dos gestores.
# El color principal es #00acc1 (Turquesa)
TURQUOISE_STYLESHEET = """
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

/* --- NUEVO: Menú de Navegación Principal --- */
#NavMenuWidget {
    background-color: #3c3c3c;
    border-right: 1px solid #4a4a4a;
}
#NavMenuWidget QLabel {
    font-size: 14pt;
    font-weight: bold;
    padding: 10px;
    margin: 5px;
    background-color: #454545;
    border-radius: 5px;
}
QListWidget#NavMenu {
    background-color: #3c3c3c;
    border: none;
    padding: 5px;
}
QListWidget#NavMenu::item {
    padding: 15px 20px; /* Más altos */
    margin: 5px 0;
    border-radius: 5px;
    color: #f0f0f0;
    font-size: 11pt;
    font-weight: bold;
}
QListWidget#NavMenu::item:hover {
    background-color: #4a4a4a;
}
QListWidget#NavMenu::item:selected {
    background-color: #00acc1; /* Color principal TURQUESA */
    color: #ffffff;
}

/* --- Estilos para Gestores (Azul y Rosa) --- */
/* (Todos unificados al tema Turquesa) */

/* --- Menú Lateral (Interno de Gestores) --- */
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
    background-color: #00acc1; /* TURQUESA */
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
    background-color: #00acc1; /* TURQUESA para pestaña activa */
    color: #ffffff;
    border-color: #4a4a4a;
    border-bottom-color: #00acc1;
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
    background-color: #26c6da; /* TURQUESA más claro al seleccionar */
}

/* --- Botones (Generales) --- */
QPushButton {
    background-color: #00acc1; /* TURQUESA */
    color: #ffffff;
    border: none;
    padding: 10px 15px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #26c6da; /* TURQUESA hover */
}
QPushButton:pressed {
    background-color: #0097a7; /* TURQUESA pressed */
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

/* --- Editores --- */
/* Editor de Texto (Gestor de Instancias) */
QPlainTextEdit {
    background-color: #1e1e1e;
    color: #dcdcdc;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10pt;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 10px;
}

/* Consola de Salida (Gestor de Monitor) */
/* (Usa el QPlainTextEdit de arriba) */

/* Cabecera */
QFrame[isHeader="true"] {
    background-color: #3c3c3c;
    border-bottom: 1px solid #4a4a4a;
    border-radius: 0px;
}

/* --- Editor de Configuración (Gestor de Monitor) --- */
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
    background-color: #0097a7; /* TURQUESA oscuro para borrar */
}
QPushButton#AddButton {
    font-size: 14pt;
    font-weight: bold;
    min-height: 40px;
}

/* --- NUEVO: Estilos para el Gestor de Archivos --- */

/* Divisor */
QSplitter::handle {
    background-color: #4a4a4a;
    width: 3px;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QSplitter::handle:vertical {
    height: 3px;
}
QSplitter::handle:hover {
    background-color: #00acc1;
}

/* Árbol de archivos */
QTreeWidget {
    background-color: #2b2b2b;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    color: #f0f0f0;
}
QHeaderView::section {
    background-color: #3c3c3c;
    color: #f0f0f0;
    padding: 8px;
    border: 1px solid #4a4a4a;
    font-weight: bold;
}
QTreeWidget::item {
    padding: 8px;
    border-radius: 4px;
}
QTreeWidget::item:hover {
    background-color: #3c3c3c;
}
QTreeWidget::item:selected {
    background-color: #0097a7; /* Un turquesa más oscuro para el árbol */
    color: #ffffff;
}
/* Flechas de expansión */
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>);
    width: 24px;
    height: 24px;
}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>);
    width: 24px;
    height: 24px;
}

/* Botones dentro del árbol */
#TreeButtonWidget QPushButton {
    background-color: transparent;
    border: none;
    padding: 4px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    margin: 0 2px;
}
#TreeButtonWidget QPushButton:hover {
    background-color: #5a5a5a;
}
#TreeButtonWidget QPushButton:pressed {
    background-color: #00acc1;
}
#TreeButtonWidget QPushButton:disabled {
    background-color: #3a3a3a;
}
"""


# --- Widget de Carga/Error y Launchers ---
class StatusWidget(QWidget):
    """Un widget simple para mostrar un mensaje de estado o error."""
    def __init__(self, message, color="#7a7a7a", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel(message)
        label.setStyleSheet(f"font-size: 16pt; color: {color};")
        layout.addWidget(label)

class DockerManagerLauncher(QWidget):
    """Lanza el Docker Manager, manejando la conexión y el login."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.setup_and_launch()

    def setup_and_launch(self):
        # 1. Inicializar servicios
        config_manager = ConfigManager()
        docker_service = DockerService()

        # 2. Verificar conexión
        connected, error_msg = docker_service.check_connection()
        if not connected:
            self.layout().addWidget(StatusWidget(f"Error de Conexión:\n{error_msg}", "#ffcccc"))
            return

        # 3. Autenticar
        creds = config_manager.load_credentials()
        if creds:
            success, msg = docker_service.login_to_docker_hub(creds['username'], creds['token'])
            if not success:
                creds = None
        
        if not creds:
            login_dialog = LoginDialog(docker_service, config_manager, self)
            if login_dialog.exec() != login_dialog.DialogCode.Accepted:
                self.layout().addWidget(StatusWidget("Login cancelado.\nNo se puede iniciar Docker Manager.", "#ffcccc"))
                return
        
        # 4. Lanzar el widget principal
        docker_widget = DockerManagerWidget(docker_service, config_manager, self)
        self.layout().addWidget(docker_widget)

# --- Ventana Principal del HUB ---
class MainHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Central de Aplicaciones")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(TURQUOISE_STYLESHEET)

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.init_nav_menu()
        main_layout.addWidget(self.nav_menu_widget)

        self.init_main_stack()
        main_layout.addWidget(self.main_stack, 1)

        self.setCentralWidget(main_widget)
        self.nav_list.setCurrentRow(0)

    def init_nav_menu(self):
        self.nav_menu_widget = QWidget()
        self.nav_menu_widget.setObjectName("NavMenuWidget")
        self.nav_menu_widget.setMaximumWidth(250)
        
        nav_layout = QVBoxLayout(self.nav_menu_widget)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(10)

        title_label = QLabel("NAVEGACIÓN")
        title_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(title_label)
        
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavMenu")
        self.nav_list.setIconSize(QSize(24, 24))
        self.nav_list.itemClicked.connect(self.on_nav_item_selected)
        
        item_apps = QListWidgetItem("Gestor de Instancias")
        item_apps.setIcon(get_icon("apps"))
        item_apps.setData(Qt.UserRole, 1)
        self.nav_list.addItem(item_apps)
        
        item_monitor = QListWidgetItem("Gestor de Monitores")
        item_monitor.setIcon(get_icon("monitor"))
        item_monitor.setData(Qt.UserRole, 2)
        self.nav_list.addItem(item_monitor)

        item_docker = QListWidgetItem("Docker Hub")
        item_docker.setIcon(get_icon("docker"))
        item_docker.setData(Qt.UserRole, 3)
        self.nav_list.addItem(item_docker)

        item_github = QListWidgetItem("GitHub Hub")
        item_github.setIcon(get_icon("github"))
        item_github.setData(Qt.UserRole, 4)
        self.nav_list.addItem(item_github)

        item_file_manager = QListWidgetItem("Administrador de Archivos")
        item_file_manager.setIcon(get_icon("file_manager"))
        item_file_manager.setData(Qt.UserRole, 5)
        self.nav_list.addItem(item_file_manager)
        
        nav_layout.addWidget(self.nav_list)

    def init_main_stack(self):
        self.main_stack = QStackedWidget()
        
        # Index 0: Placeholder inicial
        self.main_stack.addWidget(StatusWidget("← Selecciona una aplicación del menú"))
        
        # Index 1: Gestor de Instancias
        self.instance_manager = InstanceManager(self)
        self.main_stack.addWidget(self.instance_manager)
        
        # Index 2: Gestor de Monitores
        self.monitor_manager = MonitorManager(self)
        self.main_stack.addWidget(self.monitor_manager)

        # Index 3: Docker Manager
        self.docker_manager = DockerManagerLauncher(self)
        self.main_stack.addWidget(self.docker_manager)

        # Index 4: GitHub Manager
        self.github_manager = GitHubManagerWidget(self)
        self.main_stack.addWidget(self.github_manager)

        # Index 5: File Manager
        self.file_manager = FileManagerWidget(self)
        self.main_stack.addWidget(self.file_manager)

    def on_nav_item_selected(self, item):
        """Cambia la vista en el QStackedWidget."""
        index = item.data(Qt.UserRole)
        if index is not None:
            self.main_stack.setCurrentIndex(index)

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana principal."""
        running_instances = self.instance_manager.is_any_process_running()
        running_monitors = self.monitor_manager.is_any_process_running()
        
        if running_instances or running_monitors:
            reply = QMessageBox.question(self, "Procesos en ejecución",
                                         "Hay instancias o monitores en ejecución.\n"
                                         "¿Desea detenerlos todos y salir?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.instance_manager.stop_all_processes()
                self.monitor_manager.stop_all_processes()
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
        
    window = MainHub()
    window.show()
    sys.exit(app.exec())