import sys
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QTextEdit, QLineEdit, QPushButton,
    QDockWidget, QToolBar, QToolButton, QMessageBox, QInputDialog,
    QTabWidget, QListWidgetItem, QStyle
)
from PySide6.QtCore import Qt, QProcess, QSettings, QSize
from PySide6.QtGui import QIcon, QTextCharFormat, QColor, QFont

# --- Estilo Moderno Oscuro (Dark Theme QSS) ---
# Puedes personalizar esta paleta de colores
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
    titlebar-color: #555555; /* No funciona en todos los SO */
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
QToolBar {
    background-color: #3c3c3c;
    border: none;
    padding: 4px;
}
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
    border-bottom: 1px solid #2b2b2b; /* Oculta el borde inferior */
}
QTabBar::tab:!selected {
    background: #444;
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
"""

class DockerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Docker Command GUI")
        self.setGeometry(100, 100, 1400, 800)

        # Configuraciones para guardar el token
        self.settings = QSettings("MyDockerApp", "AppConfig")

        # Proceso para ejecutar comandos
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)

        # Base de datos de comandos
        self.commands_db = {}
        self.setup_commands_db()

        # Configurar la UI
        self.setup_ui()
        self.init_signals()

        # Cargar estado inicial del panel derecho
        self.refresh_right_dock()

    def setup_ui(self):
        # --- Barra de herramientas rápida (para el Token) ---
        toolbar = QToolBar("Herramientas Rápidas")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Usamos un icono estándar de PySide
        icon_key = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        self.token_button = QToolButton()
        self.token_button.setIcon(icon_key)
        self.token_button.setText("Token GH")
        self.token_button.setToolTip("Guardar o Copiar Token de GitHub (PAT)")
        self.token_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.addWidget(self.token_button)

        # --- Dock Izquierdo (Categorías) ---
        self.left_dock = QDockWidget("Categorías", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        
        self.category_list = QListWidget()
        self.category_list.addItems(self.commands_db.keys())
        self.left_dock.setWidget(self.category_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # --- Dock Derecho (Info en Vivo) ---
        self.right_dock = QDockWidget("Vistas en Vivo", self)
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        right_dock_widget = QWidget()
        right_layout = QVBoxLayout(right_dock_widget)

        self.refresh_button = QPushButton("Actualizar Vistas")
        right_layout.addWidget(self.refresh_button)

        self.info_tabs = QTabWidget()
        self.containers_view = QTextEdit()
        self.containers_view.setReadOnly(True)
        self.images_view = QTextEdit()
        self.images_view.setReadOnly(True)
        
        self.info_tabs.addTab(self.containers_view, "Contenedores Activos")
        self.info_tabs.addTab(self.images_view, "Imágenes Locales")
        
        right_layout.addWidget(self.info_tabs)
        self.right_dock.setWidget(right_dock_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)


        # --- Widget Central (Contenido Principal) ---
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # 1. StackedWidget para las listas de comandos
        self.command_stack = QStackedWidget()
        for category in self.commands_db:
            command_list_widget = QListWidget()
            for cmd_name in self.commands_db[category]:
                item = QListWidgetItem(cmd_name)
                # Guardamos el comando real en el item
                item.setData(Qt.ItemDataRole.UserRole, self.commands_db[category][cmd_name]["command"])
                command_list_widget.addItem(item)
            self.command_stack.addWidget(command_list_widget)
            # Conectamos la señal de cada lista de comandos
            command_list_widget.itemClicked.connect(self.on_command_selected)

        # 2. Área de información del comando
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setFixedHeight(120) # Altura fija para la info
        self.info_display.setHtml("<h3>Selecciona una categoría y luego un comando...</h3>")

        # 3. Campo de entrada del comando
        input_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Escribe tu comando o haz clic en uno de arriba...")
        self.run_button = QPushButton("Ejecutar")
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.run_button)

        # 4. Consola de salida
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))

        # Ensamblar el layout central
        main_layout.addWidget(self.command_stack)
        main_layout.addWidget(self.info_display)
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.console_output) # La consola ocupa el espacio restante

        self.setCentralWidget(central_widget)

    def setup_commands_db(self):
        """Define todos los comandos disponibles en la GUI."""
        self.commands_db = {
            "Contenedores": {
                "Ver activos": {
                    "command": "docker ps",
                    "info": "<b>¿Qué hace?</b><br>Muestra todos los contenedores que están actualmente en ejecución."
                },
                "Ver todos": {
                    "command": "docker ps -a",
                    "info": "<b>¿Qué hace?</b><br>Muestra todos los contenedores, incluyendo los que están detenidos (exited)."
                },
                "Detener un contenedor": {
                    "command": "docker stop [ID_O_NOMBRE]",
                    "info": "<b>¿Qué hace?</b><br>Detiene un contenedor en ejecución.<br><b>Uso:</b> Reemplaza [ID_O_NOMBRE] con el ID o nombre del contenedor."
                },
                "Eliminar un contenedor": {
                    "command": "docker rm [ID_O_NOMBRE]",
                    "info": "<b>¿Qué hace?</b><br>Elimina un contenedor detenido. No puedes eliminar uno en ejecución (primero usa 'stop')."
                },
                "Eliminar forzado": {
                    "command": "docker rm -f [ID_O_NOMBRE]",
                    "info": "<b>¿Qué hace?</b><br>Fuerza la eliminación de un contenedor, incluso si está en ejecución."
                }
            },
            "Imágenes": {
                "Listar imágenes": {
                    "command": "docker images",
                    "info": "<b>¿Qué hace?</b><br>Muestra todas las imágenes de Docker que tienes descargadas localmente."
                },
                "Eliminar imagen": {
                    "command": "docker rmi [ID_O_TAG]",
                    "info": "<b>¿Qué hace?</b><br>Elimina una imagen local.<br><b>Uso:</b> Reemplaza [ID_O_TAG] con el ID o el 'TAG' de la imagen."
                },
                "Construir imagen (build)": {
                    "command": "docker build -t mi-imagen:tag .",
                    "info": "<b>¿Qué hace?</b><br>Construye una imagen a partir de un 'Dockerfile' en el directorio actual ('.').<br><b>Uso:</b> Cambia 'mi-imagen:tag' por el nombre y tag que desees."
                }
            },
            "Push a GitHub (GHCR)": {
                "1. Login en GHCR": {
                    "command": "docker login ghcr.io -u TU_USUARIO",
                    "info": ("<b>¿Qué hace?</b><br>Inicia sesión en GitHub Container Registry (GHCR).<br>"
                             "<b>Uso:</b> Reemplaza 'TU_USUARIO' con tu nombre de usuario de GitHub. "
                             "Te pedirá una contraseña: usa el <b>Token (PAT)</b> que generaste en GitHub. "
                             "Puedes usar el botón <b>(🔑 Token GH)</b> de arriba para guardarlo y copiarlo.")
                },
                "2. Etiquetar (Tag) Imagen": {
                    "command": "docker tag IMAGEN_LOCAL:TAG ghcr.io/TU_USUARIO/IMAGEN_REPO:TAG",
                    "info": ("<b>¿Qué hace?</b><br>Crea un alias (tag) para tu imagen local que la apunta al registro de GitHub.<br>"
                             "<b>Uso:</b><br>"
                             " - <b>IMAGEN_LOCAL:TAG</b>: El nombre de tu imagen (ej: 'mi-app:latest').<br>"
                             " - <b>TU_USUARIO</b>: Tu usuario de GitHub.<br>"
                             " - <b>IMAGEN_REPO</b>: El nombre que tendrá en GitHub (ej: 'mi-app-publica').")
                },
                "3. Subir (Push) Imagen": {
                    "command": "docker push ghcr.io/TU_USUARIO/IMAGEN_REPO:TAG",
                    "info": ("<b>¿Qué hace?</b><br>Sube la imagen etiquetada a GitHub Container Registry.<br>"
                             "<b>Uso:</b> Asegúrate de que los nombres coincidan exactamente con el paso 2.")
                }
            }
        }

    def init_signals(self):
        """Conecta todas las señales y slots."""
        self.category_list.currentRowChanged.connect(self.command_stack.setCurrentIndex)
        self.run_button.clicked.connect(self.execute_command)
        self.command_input.returnPressed.connect(self.execute_command)
        self.refresh_button.clicked.connect(self.refresh_right_dock)
        self.token_button.clicked.connect(self.manage_github_token)

    # --- Slots (Funciones de respuesta) ---

    def on_command_selected(self, item):
        """Se activa al hacer clic en un comando de la lista central."""
        cmd_name = item.text()
        # Encontramos la categoría actual
        current_category_index = self.command_stack.currentIndex()
        category_name = self.category_list.item(current_category_index).text()

        # Obtenemos datos de nuestro "DB"
        cmd_data = self.commands_db[category_name][cmd_name]
        
        # 1. Poner info en el panel superior
        self.info_display.setHtml(f"<h3>{cmd_name}</h3><p>{cmd_data['info']}</p>")
        
        # 2. Poner comando en el campo de texto
        self.command_input.setText(cmd_data["command"])
        self.command_input.setFocus() # Pone el cursor listo para editar

    def execute_command(self):
        """Ejecuta el comando del QLineEdit en la consola."""
        command_str = self.command_input.text().strip()
        if not command_str:
            return

        # Limpiar consola y mostrar el comando a ejecutar
        self.console_output.append(f"<b style='color: #00aaff;'>&gt; {command_str}</b>")

        # Usamos 'docker' como programa y el resto como argumentos
        # Manejo simple para comandos con espacios (ej. "docker ps -a")
        parts = command_str.split()
        program = parts[0]
        arguments = parts[1:]

        # Para que 'docker login' funcione interactivamente, necesitamos
        # un terminal real. Para otros comandos, QProcess está bien.
        # Esta es una simplificación; un 'docker login' real
        # es mejor hacerlo en una terminal externa.
        if "docker login" in command_str:
            self.console_output.append("<i style='color: #ffcc00;'>AVISO: 'docker login' es interactivo. "
                                       "Se recomienda ejecutarlo en una terminal externa. "
                                       "Pega tu Token (PAT) cuando pida la contraseña.</i>")
        
        # Iniciar el proceso
        self.process.start(program, arguments)

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
        # Usamos QProcess.execute() para un comando síncrono (bloqueante)
        # ya que solo queremos la salida final, no es interactivo.
        process_ps = QProcess()
        # '--no-trunc' evita que se corten los IDs largos
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

    def manage_github_token(self):
        """Maneja el guardado y copiado del Token PAT de GitHub."""
        # Opciones para el usuario
        items = ["Guardar/Actualizar Token (PAT)", "Copiar Token al Portapapeles"]
        item, ok = QInputDialog.getItem(self, "Gestor de Token de GitHub",
                                        "¿Qué deseas hacer?", items, 0, False)
        
        if ok and item:
            if item == items[0]: # Guardar/Actualizar
                token, ok_input = QInputDialog.getText(self, "Guardar Token",
                                                       "Pega tu Personal Access Token (PAT) de GitHub:",
                                                       QLineEdit.Password)
                if ok_input and token:
                    self.settings.setValue("github_pat", token)
                    QMessageBox.information(self, "Éxito", "Token guardado localmente.")
                    self.show_token_security_warning()

            elif item == items[1]: # Copiar
                token = self.settings.value("github_pat")
                if token:
                    clipboard = QApplication.clipboard()
                    clipboard.setText(token)
                    QMessageBox.information(self, "Éxito", "Token copiado al portapapeles. "
                                                         "¡Úsalo para el 'docker login'!")
                else:
                    QMessageBox.warning(self, "Error", "No hay ningún token guardado. "
                                                      "Por favor, guárdalo primero.")

    def show_token_security_warning(self):
        QMessageBox.warning(self, "Advertencia de Seguridad",
                            "Tu token se ha guardado en la configuración de la aplicación. "
                            "Aunque es conveniente, esto puede no ser seguro en un PC compartido. "
                            "Maneja tus tokens con cuidado.")

    def closeEvent(self, event):
        """Asegura que el proceso termine al cerrar la app."""
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.terminate()
            self.process.waitForFinished()
        event.accept()


# --- Punto de entrada de la Aplicación ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplicar el tema oscuro
    app.setStyleSheet(DARK_THEME_QSS)
    
    window = DockerGUI()
    window.show()
    sys.exit(app.exec())