import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QStackedWidget, QPlainTextEdit,
    QMessageBox, QLabel, QFrame, QListWidgetItem, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QSplitter, QDialog,
    QTextEdit, QSizePolicy, QTabWidget
)
from PySide6.QtCore import Qt, QSettings, QSize, QByteArray, QDir, QTimer
from PySide6.QtGui import QIcon, QFontDatabase, QPainter, QPixmap, QClipboard
from PySide6.QtSvg import QSvgRenderer

# --- Sistema de Iconos SVG ---
# (Extraído de tu app.py y expandido para el gestor de archivos)

def get_icon(name):
    svg_data = {
        # --- Iconos de tu app.py ---
        "add": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>""",
        "edit": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4L18.5 2.5z"></path></svg>""",
        "play": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>""",
        "stop": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>""",
        "save": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>""",
        "trash": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>""",
        "external-link": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>""",
        "folder": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>""",
        "file": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>""",
        "apps": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>""",
        "monitor": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>""",
        "docker": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.3 13.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5s-2.8-1.1-2.8-2.5c0-.5.1-.9.4-1.3l-2.2-1.2c-.3.4-.7.7-1.2.9v2.2c.5.2 1 .6 1.4 1.1.4.5.6 1.1.6 1.7 0 1.4-1.3 2.5-2.8 2.5s-2.8-1.1-2.8-2.5c0-.6.2-1.2.6-1.7.4-.5.9-.9 1.4-1.1v-2.2c-.5-.2-1-.5-1.2-.9L9.3 13.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3 0 1.4-1.3 2.5-2.8 2.5S4 15.9 4 14.5c0-.5.1-.9.4-1.3L2.2 12c-.2.5-.2 1.1-.2 1.6 0 2.8 2.5 5.1 5.6 5.1s5.6-2.3 5.6-5.1c0-.5 0-1.1-.2-1.6L11 12l-2.2-1.2c.3.4.4.8.4 1.3""",
        "github": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>""",
        
        # --- Nuevos iconos para el Gestor de Archivos ---
        "copy": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>""",
        "file-py": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#306998" stroke="#f0f0f0" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><path d="M13.4 4.3c-.6 0-1.2.1-1.7.4-.5.3-.9.7-1.2 1.2-.3.5-.4 1.1-.4 1.7 0 .4.1.9.2 1.3.1.4.3.8.5 1.1.2.3.5.6.8.8.3.2.7.4 1.1.5.4.1.9.2 1.3.2s.9-.1 1.3-.2c.4-.1.8-.3 1.1-.5.3-.2.6-.5.8-.8.2-.3.4-.7.5-1.1.1-.4.2-.9.2-1.3 0-.6-.1-1.2-.4-1.7-.3-.5-.7-.9-1.2-1.2-.5-.3-1.1-.4-1.7-.4zm-2.8 15.4c-.6 0-1.2-.1-1.7-.4-.5-.3-.9-.7-1.2-1.2-.3-.5-.4-1.1-.4-1.7 0-.4.1-.9.2-1.3.1-.4.3-.8.5-1.1.2-.3.5-.6.8-.8.3-.2.7-.4 1.1-.5.4-.1.9-.2 1.3-.2s.9.1 1.3.2c.4.1.8.3 1.1.5.3.2.6.5.8.8.2.3.4.7.5-1.1.1-.4.2-.9.2-1.3 0-.6-.1-1.2-.4-1.7-.3-.5-.7-.9-1.2-1.2-.5-.3-1.1-.4-1.7-.4z" fill="#FFD43B"/><path d="M13.4 4.3c-.6 0-1.2.1-1.7.4-.5.3-.9.7-1.2 1.2-.3.5-.4 1.1-.4 1.7 0 .4.1.9.2 1.3.1.4.3.8.5 1.1.2.3.5.6.8.8.3.2.7.4 1.1.5.4.1.9.2 1.3.2V0h-2.1v4.3zm-2.8 15.4c-.6 0-1.2-.1-1.7-.4-.5-.3-.9-.7-1.2-1.2-.3-.5-.4-1.1-.4-1.7 0-.4.1-.9.2-1.3.1-.4.3-.8.5-1.1.2-.3.5.6.8-.8.3-.2.7-.4 1.1-.5.4-.1.9-.2 1.3-.2v-4.3h2.1v4.3c.6 0 1.2.1 1.7.4.5.3.9.7 1.2 1.2.3.5.4 1.1.4 1.7 0 .4-.1.9-.2 1.3-.1.4-.3.8-.5 1.1-.2.3-.5.6-.8.8-.3.2-.7.4-1.1.5-.4.1-.9.2-1.3.2z"/></svg>""",
        "file-js": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#F7DF1E" stroke="#2b2b2b" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v18H3V3z"/><path d="M17.4 14.8c-.8.8-1.8 1.2-3.1 1.2-1.9 0-3.3-1.1-3.3-2.7 0-1.3.9-2.2 2.4-2.6l1.3-.4c-.1-.3-.3-.5-.6-.5-.5 0-.9.2-1.3.7l-1-1.1c.6-.5 1.4-.8 2.3-.8 1.4 0 2.3.7 2.3 2.1V17h-1.6v-2.2zm-2.4-.6c.7 0 1.1.3 1.1 1 0 .6-.4 1-1.1 1-.6 0-1-.3-1-.9 0-.5.4-.9 1-.9zM9.3 10.4c.5-.4 1.2-.6 2-.6.7 0 1.3.1 1.8.4l-.8 1.3c-.3-.2-.6-.3-1-.3-.5 0-.9.2-1.1.5-.3.3-.4.7-.4 1.1s.1 1 .4 1.3c.3.3.6.4 1.1.4.4 0 .8-.1 1.1-.3l.8 1.3c-.5.3-1.1.5-1.9.5-1.1 0-1.9-.4-2.5-1.2-.6-.8-.9-1.8-.9-3 0-1.1.3-2.1.9-2.9z" fill="#000000"/></svg>""",
        "file-html": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#E34F26"><path d="M2.3 2.1l1.8 20.3L12 24l7.9-1.6L21.7 2.1z"/><path d="M12 21.8l-6.2-1.6L6 2.1h12l-.2 18.1z" fill="#F06529"/><path d="M12 5.1v15.2l5.1-1.4.1-1.3 1.2-14H12zm5 10.3l-2.6.7v-2.1l2.5-.1.1-1.7-2.6-.1v-2l2.6-.1z" fill="#EBEBEB"/><path d="M12 5.1v15.2l-5.1-1.4-1.2-14H12zm-5 10.3l2.6.7v-2.1l-2.5-.1-.1-1.7 2.6-.1v-2L7 9.8z" fill="#FFF"/></svg>""",
        "file-css": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#1572B6"><path d="M2.3 2.1l1.8 20.3L12 24l7.9-1.6L21.7 2.1z"/><path d="M12 21.8l6.2-1.6.1-1.3 1.5-16.8H12z" fill="#33A9DC"/><path d="M12 5.1v15.2l-5.1-1.4L5.7 4.1H12z" fill="#FFF"/><path d="M12 9.8h-2l.1 2h1.9v2H7.9l.1 2H12v-2H9.9l-.1-2H12zm2.1 0h2l-.1 2h-1.9v2h1.9l-.1 2H12v-2h2.1z" fill="#EBEBEB"/></svg>""",
        "file-json": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 16c-1.1 0-2-.9-2-2V9c0-1.1.9-2 2-2"></path><path d="M16 8c1.1 0 2 .9 2 2v5c0 1.1-.9 2-2 2"></path><path d="M12 8v8"></path></svg>""",
        "file-text": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 8 9 8 11"></polyline></svg>""",
        "file-yaml": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M8 13h3l-3 4h3"></path><path d="M13 13h3l-1.5 2 1.5 2h-3"></path></svg>""",
        "file-csv": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M9.5 13.5c.3.3.5.6.5 1s-.2.7-.5 1-.6.5-1 .5h-1v-3h1c.4 0 .7.2 1 .5zM8.5 12.5v3M12 15.5h-1v-3h1M16 15.5h-2c-.6 0-1-.4-1-1v-1c0-.6.4-1 1-1h2v3z"/></svg>""",
        "star": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>""",
        "folder-open": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2v1"></path><path d="M20 19v-5.5a2.5 2.5 0 0 0-5 0V19"></path></svg>""",
        "favorites": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f0f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"></path></svg>""",
    }
    if name not in svg_data: 
        return get_icon("file") # Devuelve icono de archivo genérico si no se encuentra
        
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

# --- Estilo QSS (CSS de Qt) para el Tema Oscuro ---
# (Extraído de tu app.py y expandido para el gestor de archivos)
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

/* --- Menú de Navegación Principal (de tu app) --- */
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
    padding: 15px 20px;
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
    background-color: #00acc1;
    color: #ffffff;
}

/* --- Estilos para Gestores (Unificados) --- */
#LeftMenu {
    background-color: #3c3c3c;
    border-right: 1px solid #4a4a4a;
}
#LeftMenu QLabel, #FileManagerLeftMenu QLabel {
    font-size: 12pt;
    font-weight: bold;
    padding: 10px;
    margin-bottom: 5px;
    background-color: #454545;
    border-radius: 5px;
    text-align: center;
}
QListWidget {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 5px;
}
QListWidget::item {
    padding: 8px 10px; 
    margin-bottom: 5px;
    border-radius: 5px;
    color: #f0f0f0;
}
QWidget#InstanceItem {
    background-color: transparent;
    border-radius: 5px;
    padding: 5px 10px;
}
QListWidget::item:hover, QListWidget::item:hover QWidget#InstanceItem {
    background-color: #4a4a4a;
}
QListWidget::item:selected, QListWidget::item:selected QWidget#InstanceItem {
    background-color: #00acc1;
    color: #ffffff;
}
QListWidget::item:selected QLabel#InstanceName {
    color: #ffffff;
}

/* --- Botones (Generales) --- */
QPushButton {
    background-color: #00acc1;
    color: #ffffff;
    border: none;
    padding: 10px 15px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #26c6da;
}
QPushButton:pressed {
    background-color: #0097a7;
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
QPlainTextEdit, QTextEdit {
    background-color: #1e1e1e;
    color: #dcdcdc;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10pt;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 10px;
}
QDialog QPlainTextEdit, QDialog QTextEdit {
    font-size: 11pt;
    min-height: 400px;
    min-width: 600px;
}

/* --- NUEVO: Estilos para el Gestor de Archivos --- */

/* Pestañas del menú lateral */
QTabWidget::pane {
    border: none;
}
QTabBar::tab {
    background-color: #3c3c3c;
    color: #aaaaaa;
    padding: 10px 15px;
    border: 1px solid #4a4a4a;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    font-weight: bold;
}
QTabBar::tab:hover {
    background-color: #4a4a4a;
    color: #f0f0f0;
}
QTabBar::tab:selected {
    background-color: #2b2b2b; /* Fondo del contenido */
    color: #ffffff;
    border-bottom: 1px solid #2b2b2b; /* Unir con el panel */
}

# ... (rest of the stylesheet) ...

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
QTreeWidget::item.highlighted {
    background-color: #FFD700; /* Gold */
    color: #000000;
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
#TreeButtonWidget {
    background-color: transparent;
}
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

# --- Ventana de Diálogo para Edición ---

class TextEditorDialog(QDialog):
    """
    Un diálogo modal para editar archivos .txt y .rtf.
    """
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_rich_text = file_path.lower().endswith('.rtf')

        self.setWindowTitle(f"Editando: {os.path.basename(file_path)}")
        self.setWindowIcon(get_icon("edit"))
        
        layout = QVBoxLayout(self)

        # Área de texto
        self.text_edit = QTextEdit()
        if not self.load_file():
            # Si no se puede cargar, cierra el diálogo
            self.close() 
            return

        layout.addWidget(self.text_edit)

        # Botones
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("SecondaryButton")
        self.cancel_button.setIcon(get_icon("stop"))
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("Guardar Cambios")
        self.save_button.setIcon(get_icon("save"))
        self.save_button.clicked.connect(self.save_and_accept)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet(TURQUOISE_STYLESHEET) # Aplicar estilo

    def load_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if self.is_rich_text:
                # QTextEdit puede manejar RTF directamente si se establece como HTML
                # (Es una peculiaridad de Qt, pero funciona para mostrar/guardar)
                self.text_edit.setHtml(content)
            else:
                self.text_edit.setPlainText(content)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error al Cargar", f"No se pudo leer el archivo:\n{e}")
            return False

    def save_and_accept(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                if self.is_rich_text:
                    # Guardar como RTF (usando toHtml() que produce RTF)
                    f.write(self.text_edit.toHtml())
                else:
                    # Guardar como texto plano
                    f.write(self.text_edit.toPlainText())
            self.accept() # Cierra el diálogo con éxito
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo:\n{e}")


# --- Widget Principal del Gestor de Archivos ---

class FileManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración para persistencia
        self.settings = QSettings("PyAppHub", "FileManager")

        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Divisor
        splitter = QSplitter(Qt.Horizontal)
        
        # 1. Menú Izquierdo
        self.left_menu = self.create_left_menu()
        splitter.addWidget(self.left_menu)

        # 2. Contenido Derecho (Árbol)
        self.right_content = self.create_right_content()
        splitter.addWidget(self.right_content)
        
        # Configuración del divisor
        splitter.setSizes([300, 700]) # Tamaños iniciales
        splitter.setCollapsible(0, False) # No colapsar menú
        splitter.setCollapsible(1, False)
        
        main_layout.addWidget(splitter)
        
        self.load_folders() # Cargar carpetas guardadas
        self.load_favorites() # Cargar favoritos guardados

    def create_left_menu(self):
        """Crea el widget del menú lateral izquierdo con pestañas."""
        widget = QWidget()
        widget.setObjectName("FileManagerLeftMenu")
        widget.setMaximumWidth(400)
        widget.setMinimumWidth(250)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._create_folders_tab(), "Carpetas")
        self.tab_widget.addTab(self._create_favorites_tab(), "Favoritos")
        
        layout.addWidget(self.tab_widget)
        return widget

    def _create_folders_tab(self):
        """Crea el widget para la pestaña de carpetas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Botón para copiar ruta de la carpeta seleccionada
        self.copy_path_button = QPushButton("Copiar Ruta de Carpeta")
        self.copy_path_button.setIcon(get_icon("copy"))
        self.copy_path_button.clicked.connect(self.on_copy_selected_folder_path)
        layout.addWidget(self.copy_path_button)
        
        # Lista de carpetas de interés
        self.folder_list = QListWidget()
        self.folder_list.itemClicked.connect(self.on_folder_selected)
        layout.addWidget(self.folder_list, 1)
        
        # Botón para añadir nueva carpeta
        self.add_folder_button = QPushButton("Añadir Carpeta")
        self.add_folder_button.setIcon(get_icon("add"))
        self.add_folder_button.clicked.connect(self.on_add_folder)
        layout.addWidget(self.add_folder_button)
        
        return widget

    def _create_favorites_tab(self):
        """Crea el widget para la pestaña de favoritos."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.favorites_list = QListWidget()
        self.favorites_list.setWordWrap(True)
        layout.addWidget(self.favorites_list, 1)
        
        # Botón para limpiar favoritos
        self.clear_favorites_button = QPushButton("Limpiar Favoritos")
        self.clear_favorites_button.setIcon(get_icon("trash"))
        self.clear_favorites_button.clicked.connect(self.on_clear_favorites)
        layout.addWidget(self.clear_favorites_button)
        
        return widget

    def create_right_content(self):
        """Crea el widget del explorador de archivos (árbol)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Etiqueta para la ruta actual
        self.current_path_label = QLabel("Seleccione una carpeta del menú de la izquierda.")
        self.current_path_label.setObjectName("CurrentPathLabel")
        self.current_path_label.setStyleSheet("font-size: 11pt; color: #aaaaaa; padding: 5px;")
        layout.addWidget(self.current_path_label)

        # Árbol de archivos
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Nombre", "Tipo", "Acciones"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setIconSize(QSize(20, 20))
        
        # Conexión para la carga "perezosa" (lazy loading)
        self.tree.itemExpanded.connect(self.on_item_expanded)
        
        layout.addWidget(self.tree, 1) # 1 = stretch factor
        return widget

    # --- Lógica del Menú Izquierdo ---

    def on_add_folder(self):
        """Abre un diálogo para seleccionar y añadir una nueva carpeta de interés."""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if path:
            name = os.path.basename(path)
            
            # Verificar si ya existe
            for i in range(self.folder_list.count()):
                if self.folder_list.item(i).data(Qt.UserRole) == path:
                    QMessageBox.warning(self, "Carpeta Duplicada", "Esa carpeta ya está en la lista.")
                    return
            
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, path) # Guardamos la ruta completa
            item.setIcon(get_icon("folder"))
            self.folder_list.addItem(item)
            self.save_folders()

    def on_copy_selected_folder_path(self):
        """Copia la ruta de la carpeta seleccionada en la lista izquierda."""
        current_item = self.folder_list.currentItem()
        if current_item:
            path = current_item.data(Qt.UserRole)
            QApplication.clipboard().setText(path)
            # Feedback simple:
            self.copy_path_button.setText("¡Copiado!")
            self.copy_path_button.setStyleSheet("background-color: #4CAF50;") # Verde
            # Volver al estado normal después de 2 segundos
            QTimer.singleShot(2000, lambda: (
                self.copy_path_button.setText("Copiar Ruta de Carpeta"),
                self.copy_path_button.setStyleSheet("background-color: #00acc1; color: #ffffff;")
            ))
        else:
            QMessageBox.warning(self, "Error", "No hay ninguna carpeta seleccionada.")

    def on_folder_selected(self, item):
        """Se llama al hacer clic en una carpeta de la lista. Puebla el árbol."""
        path = item.data(Qt.UserRole)
        self.current_path_label.setText(path)
        self.tree.clear()
        
        if os.path.exists(path):
            self.populate_tree(path, self.tree.invisibleRootItem())
        else:
            self.tree.clear()
            self.current_path_label.setText(f"Error: La ruta no existe: {path}")

    # --- Lógica de Favoritos ---

    def on_clear_favorites(self):
        """Limpia la lista de favoritos."""
        reply = QMessageBox.question(self, "Confirmar", "¿Está seguro de que desea eliminar todos los favoritos?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.favorites_list.clear()
            self.save_favorites()

    def save_favorites(self):
        """Guarda la lista de favoritos en QSettings."""
        favorites = []
        for i in range(self.favorites_list.count()):
            item = self.favorites_list.item(i)
            favorites.append(item.data(Qt.UserRole))
        self.settings.setValue("favorites", favorites)

    def load_favorites(self):
        """Carga los favoritos guardados de QSettings al iniciar."""
        favorites = self.settings.value("favorites", [])
        for file_path in favorites:
            if os.path.exists(file_path):
                self._add_favorite_item(file_path)

    def _add_to_favorites(self, path):
        """Añade un archivo a la lista de favoritos si no existe ya."""
        # Evitar duplicados
        for i in range(self.favorites_list.count()):
            if self.favorites_list.item(i).data(Qt.UserRole) == path:
                QMessageBox.information(self, "Duplicado", "Este archivo ya está en tus favoritos.")
                return

        self._add_favorite_item(path)
        self.save_favorites()

    def _add_favorite_item(self, path):
        """Crea y añade el widget personalizado para un favorito a la lista."""
        item = QListWidgetItem(self.favorites_list)
        item.setData(Qt.UserRole, path)
        
        widget = self._create_favorite_item_widget(path)
        
        item.setSizeHint(widget.sizeHint())
        self.favorites_list.addItem(item)
        self.favorites_list.setItemWidget(item, widget)

    def _create_favorite_item_widget(self, path):
        """Crea un widget para un item en la lista de favoritos."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Icono y Nombre
        icon_label = QLabel()
        ext = os.path.splitext(path)[1]
        icon_label.setPixmap(self.get_file_icon(ext).pixmap(24, 24))
        file_name = QLabel(os.path.basename(path))
        file_name.setToolTip(path) # Tooltip con la ruta completa

        layout.addWidget(icon_label)
        layout.addWidget(file_name, 1)

        # Botones de acción
        button_widget = QWidget()
        button_widget.setObjectName("TreeButtonWidget")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        edit_btn = QPushButton(get_icon("edit"), "")
        edit_btn.setToolTip("Editar archivo")
        edit_btn.clicked.connect(lambda: self.edit_file(path))
        if not path.lower().endswith(('.txt', '.rtf')):
            edit_btn.setEnabled(False)

        open_folder_btn = QPushButton(get_icon("folder-open"), "")
        open_folder_btn.setToolTip("Mostrar en la carpeta")
        open_folder_btn.clicked.connect(lambda: self._open_favorite_in_tree(path))

        remove_btn = QPushButton(get_icon("trash"), "")
        remove_btn.setToolTip("Quitar de Favoritos")
        remove_btn.clicked.connect(lambda: self._remove_favorite(path))

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(open_folder_btn)
        button_layout.addWidget(remove_btn)
        
        layout.addWidget(button_widget)
        return widget

    def _remove_favorite(self, path):
        """Elimina un archivo de la lista de favoritos."""
        for i in range(self.favorites_list.count()):
            item = self.favorites_list.item(i)
            if item.data(Qt.UserRole) == path:
                self.favorites_list.takeItem(i)
                self.save_favorites()
                break

    def _open_favorite_in_tree(self, path):
        """Encuentra y selecciona un archivo favorito en el árbol de carpetas."""
        parent_dir = os.path.dirname(path)
        
        # 1. Encontrar y seleccionar la carpeta raíz correspondiente
        root_folder_item = None
        for i in range(self.folder_list.count()):
            item = self.folder_list.item(i)
            root_path = item.data(Qt.UserRole)
            if parent_dir.startswith(root_path):
                root_folder_item = item
                break

        if not root_folder_item:
            QMessageBox.warning(self, "Carpeta no encontrada", 
                                f"Para ver este archivo, primero añada su carpeta contenedora ('{parent_dir}') o una superior a la lista de Carpetas.")
            return

        # 2. Cambiar a la pestaña de carpetas y seleccionar la carpeta
        self.tab_widget.setCurrentIndex(0) # 0 es la pestaña de Carpetas
        self.folder_list.setCurrentItem(root_folder_item)
        self.on_folder_selected(root_folder_item) # Poblar el árbol

        # 3. Encontrar el archivo en el árbol (búsqueda recursiva)
        # Usamos un QTimer para esperar a que el árbol se pueble
        QTimer.singleShot(100, lambda: self._find_and_highlight_item(path))

    def _find_and_highlight_item(self, path):
        """Busca un item por su ruta en el árbol y lo resalta."""
        item_to_select = self._find_item_in_tree(self.tree.invisibleRootItem(), path)

        if item_to_select:
            self.tree.setCurrentItem(item_to_select)
            self.tree.scrollToItem(item_to_select, QAbstractItemView.ScrollHint.PositionAtCenter)
            
            # Resaltado temporal
            original_brush = item_to_select.background(0)
            highlight_brush = QBrush(QColor("#00acc1")) # Turquesa brillante
            item_to_select.setBackground(0, highlight_brush)
            
            QTimer.singleShot(2000, lambda: item_to_select.setBackground(0, original_brush))

    def _find_item_in_tree(self, parent_item, path):
        """Busca recursivamente un item en el árbol que coincida con la ruta."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            item_path = child.data(0, Qt.UserRole)
            if item_path == path:
                return child
            
            # Si el item es una carpeta, expandir y buscar dentro si es necesario
            if path.startswith(item_path or ""):
                if child.childCount() > 0:
                    found = self._find_item_in_tree(child, path)
                    if found:
                        return found
        return None

    def save_folders(self):
        """Guarda la lista de carpetas en QSettings."""
        folders = []
        for i in range(self.folder_list.count()):
            item = self.folder_list.item(i)
            folders.append((item.text(), item.data(Qt.UserRole)))
        self.settings.setValue("folders", folders)

    def load_folders(self):
        """Carga las carpetas guardadas de QSettings al iniciar."""
        folders = self.settings.value("folders", [])
        for name, path in folders:
            if os.path.exists(path): # Solo añadir si la ruta sigue existiendo
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, path)
                item.setIcon(get_icon("folder"))
                self.folder_list.addItem(item)

    # --- Lógica del Árbol de Archivos (Derecha) ---

    def populate_tree(self, path, parent_item):
        """Puebla el árbol con el contenido de un directorio."""
        try:
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                
                if os.path.isdir(full_path):
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, entry) # Columna Nombre
                    folder_item.setText(1, "Carpeta") # Columna Tipo
                    folder_item.setIcon(0, get_icon("folder"))
                    folder_item.setData(0, Qt.UserRole, full_path) # Guardar ruta
                    
                    # Añadir botón de copiar ruta para la carpeta
                    self.add_folder_actions(folder_item, full_path)
                    
                    # Añadir un hijo "dummy" para que aparezca la flecha de expansión
                    # Solo si la carpeta no está vacía
                    try:
                        if any(os.scandir(full_path)):
                            dummy = QTreeWidgetItem(folder_item)
                            dummy.setText(0, "...")
                    except PermissionError:
                        folder_item.setText(0, f"{entry} (Acceso Denegado)")
                        folder_item.setDisabled(True)

                elif os.path.isfile(full_path):
                    name, ext = os.path.splitext(entry)
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, entry) # Columna Nombre
                    file_item.setText(1, ext[1:].upper() or "Archivo") # Columna Tipo
                    file_item.setIcon(0, self.get_file_icon(ext))
                    file_item.setData(0, Qt.UserRole, full_path) # Guardar ruta
                    
                    # Añadir botones de acción para el archivo
                    self.add_file_actions(file_item, full_path)
                    
        except PermissionError:
            parent_item.setText(0, f"{parent_item.text(0)} (Acceso Denegado)")
        except Exception as e:
            print(f"Error poblando el árbol: {e}")

    def on_item_expanded(self, item):
        """Carga perezosa (Lazy Loading). Se llama al expandir una carpeta."""
        # Si el primer hijo es el "dummy"
        if item.childCount() == 1 and item.child(0).text(0) == "...":
            item.takeChild(0) # Eliminar el dummy
            path = item.data(0, Qt.UserRole)
            if path:
                self.populate_tree(path, item) # Poblar con contenido real

    def get_file_icon(self, ext):
        """Devuelve un icono específico basado en la extensión del archivo."""
        ext_map = {
            '.py': 'file-py', '.pyw': 'file-py',
            '.js': 'file-js', '.mjs': 'file-js',
            '.html': 'file-html', '.htm': 'file-html',
            '.css': 'file-css', '.scss': 'file-css',
            '.json': 'file-json',
            '.txt': 'file-text', '.md': 'file-text', '.rtf': 'file-text',
            '.yml': 'file-yaml', '.yaml': 'file-yaml',
            '.csv': 'file-csv',
        }
        return get_icon(ext_map.get(ext.lower(), 'file')) # 'file' es el genérico

    def add_folder_actions(self, item, path):
        """Añade el botón de 'copiar ruta' a un item de carpeta."""
        widget = QWidget()
        widget.setObjectName("TreeButtonWidget")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        copy_path_btn = QPushButton(get_icon("copy"), "")
        copy_path_btn.setToolTip("Copiar ruta de la carpeta")
        copy_path_btn.clicked.connect(lambda: self.copy_to_clipboard(path))
        
        layout.addWidget(copy_path_btn)
        layout.addStretch() # Alinea a la izquierda
        
        self.tree.setItemWidget(item, 2, widget) # Columna "Acciones"

    def add_file_actions(self, item, path):
        """Añade los 3 botones de acción a un item de archivo."""
        widget = QWidget()
        widget.setObjectName("TreeButtonWidget")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        name = os.path.basename(path)
        ext = os.path.splitext(path)[1].lower()

        # 1. Copiar Nombre
        copy_name_btn = QPushButton(get_icon("copy"), "")
        copy_name_btn.setToolTip("Copiar nombre del archivo")
        copy_name_btn.clicked.connect(lambda: self.copy_to_clipboard(name))

        # 2. Copiar Ruta Completa
        copy_path_btn = QPushButton(get_icon("external-link"), "")
        copy_path_btn.setToolTip("Copiar ruta completa del archivo")
        copy_path_btn.clicked.connect(lambda: self.copy_to_clipboard(path))

        # 3. Editar
        edit_btn = QPushButton(get_icon("edit"), "")
        edit_btn.setToolTip("Editar archivo")
        edit_btn.clicked.connect(lambda: self.edit_file(path))
        
        # 4. Añadir a Favoritos
        fav_btn = QPushButton(get_icon("star"), "")
        fav_btn.setToolTip("Añadir a Favoritos")
        fav_btn.clicked.connect(lambda: self._add_to_favorites(path))

        # Deshabilitar si no es editable
        if ext not in ['.txt', '.rtf']:
            edit_btn.setEnabled(False)
            edit_btn.setToolTip("Solo se pueden editar archivos .txt y .rtf")

        layout.addWidget(copy_name_btn)
        layout.addWidget(copy_path_btn)
        layout.addWidget(edit_btn)
        layout.addWidget(fav_btn)
        layout.addStretch() # Alinea a la izquierda
        
        self.tree.setItemWidget(item, 2, widget) # Columna "Acciones"

    def copy_to_clipboard(self, text):
        """Función helper para copiar texto al portapapeles."""
        try:
            QApplication.clipboard().setText(text)
        except Exception as e:
            print(f"Error al copiar al portapapeles: {e}")

    def edit_file(self, path):
        """Abre el diálogo de edición para el archivo."""
        dialog = TextEditorDialog(path, self)
        dialog.exec()
        # No es necesario hacer nada después de que se cierre,
        # el diálogo maneja el guardado.


# --- Bloque de prueba ---
# (Puedes ejecutar este archivo directamente para probar el widget)
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"Error al iniciar QApplication: {e}")
        print("Asegúrate de tener PySide6 instalado: pip install PySide6")
        sys.exit(1)

    # Creamos una ventana principal solo para probar el widget
    window = QMainWindow()
    window.setWindowTitle("Prueba del Gestor de Archivos")
    window.setGeometry(150, 150, 1200, 700)
    
    # Instanciamos nuestro gestor
    file_manager = FileManagerWidget()
    
    # Aplicamos el estilo
    window.setStyleSheet(TURQUOISE_STYLESHEET)
    
    window.setCentralWidget(file_manager)
    window.show()
    
    sys.exit(app.exec())