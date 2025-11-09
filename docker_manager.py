import sys
import os
import json
import subprocess
import re

# --- Dependencias Requeridas ---
# (Asegúrate de instalarlas: pip install PySide6 docker cryptography)

try:
    from PySide6.QtCore import Qt, QObject, QRunnable, Signal, Slot, QThreadPool, QSize
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QStackedWidget, QListWidget, QListWidgetItem, QLabel, QDialog,
        QLineEdit, QPushButton, QFormLayout, QSpacerItem, QSizePolicy,
        QMessageBox, QProgressDialog, QTextEdit, QTableView, QHeaderView,
        QAbstractItemView, QFileDialog, QInputDialog
    )
    from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont, QTextCursor
except ImportError:
    print("Error: No se encontró PySide6. Por favor, instálalo: pip install PySide6")
    sys.exit(1)

try:
    import docker
    from docker.errors import DockerException, APIError
except ImportError:
    print("Error: No se encontró el SDK de Docker. Por favor, instálalo: pip install docker")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    print("Error: No se encontró cryptography. Por favor, instálalo: pip install cryptography")
    sys.exit(1)


# =============================================================================
# 1. GESTOR DE CONFIGURACIÓN SEGURA (config_manager.py)
# =============================================================================

# --- Constantes de Configuración ---
CONFIG_DIR = 'config'
KEY_FILE = os.path.join(CONFIG_DIR, 'app.key')
CREDS_FILE = os.path.join(CONFIG_DIR, 'credentials.enc')

class ConfigManager:
    """
    Gestiona la creación, encriptación y desencriptación de credenciales
    usando una clave local.
    """
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)

    def _load_or_generate_key(self):
        """Carga la clave de encriptación o genera una nueva si no existe."""
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(KEY_FILE, 'wb') as f:
                f.write(key)
            return key

    def save_credentials(self, username, password_or_token):
        """Encripta y guarda las credenciales en un archivo."""
        try:
            creds = {"username": username, "token": password_or_token}
            data = json.dumps(creds).encode('utf-8')
            encrypted_data = self.fernet.encrypt(data)
            with open(CREDS_FILE, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(f"Error al guardar credenciales: {e}")
            return False

    def load_credentials(self):
        """Carga y desencripta las credenciales desde el archivo."""
        if not os.path.exists(CREDS_FILE):
            return None
        
        try:
            with open(CREDS_FILE, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            creds = json.loads(decrypted_data.decode('utf-8'))
            return creds
        except InvalidToken:
            print("Error: Token inválido. El archivo de credenciales puede estar corrupto.")
            # Si está corrupto, lo eliminamos para que pida uno nuevo
            os.remove(CREDS_FILE)
            return None
        except Exception as e:
            print(f"Error al cargar credenciales: {e}")
            return None

# =============================================================================
# 2. SERVICIO DE LÓGICA DOCKER (docker_service.py)
# =============================================================================

class DockerService:
    """
    Capa de abstracción para todas las interacciones con el Docker SDK.
    Maneja la conexión y las operaciones de Docker.
    """
    def __init__(self):
        self.client = None
        # MODIFICADO: Nombres de variables generalizados
        self.registry_username = None
        self.registry_password_or_token = None # NUEVO
        self.registry_logged_in = False

    def check_connection(self):
        """Verifica la conexión con el Docker Engine."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            print("Conexión con Docker Engine exitosa.")
            return True, "Conexión con Docker Engine exitosa."
        except DockerException as e:
            print(f"Error: No se puede conectar con Docker Engine. {e}", file=sys.stderr)
            error_msg = ("No se puede conectar con Docker Engine.\n"
                         "¿Está Docker Desktop (o Docker service) en ejecución?")
            return False, error_msg
        except Exception as e:
            print(f"Error inesperado de conexión: {e}", file=sys.stderr)
            return False, f"Error inesperado: {e}"

    # MODIFICADO: Método generalizado para cualquier registro
    def login_to_registry(self, registry, username, password_or_token):
        """Intenta autenticarse en un registro (ej. ghcr.io)."""
        if not self.client:
            return False, "Cliente Docker no inicializado."
        
        try:
            print(f"Intentando login en {registry} como {username}...")
            # El SDK maneja la URL del registro (ej. 'ghcr.io' o 'https://index.docker.io/v1/')
            self.client.login(username=username, password=password_or_token, registry=registry)
            self.registry_username = username
            self.registry_password_or_token = password_or_token # NUEVO
            self.registry_logged_in = True
            print("Login exitoso.")
            return True, f"Login en {registry} exitoso."
        except APIError as e:
            print(f"Error de API al autenticarse: {e}", file=sys.stderr)
            return False, f"Error de autenticación: {e}"
        except Exception as e:
            print(f"Error inesperado durante el login: {e}", file=sys.stderr)
            return False, f"Error inesperado: {e}"

    # --- Operaciones con Imágenes ---

    def list_images(self):
        """Devuelve una lista de imágenes locales formateadas."""
        if not self.client: return []
        try:
            images = self.client.images.list()
            formatted_images = []
            for img in images:
                if not img.tags: continue # Omitir imágenes <none>:<none> por ahora
                
                # Formatear tamaño
                size_mb = img.attrs['Size'] / (1024 * 1024)
                
                formatted_images.append({
                    "id": img.short_id.split(':')[-1],
                    "tags": ", ".join(img.tags),
                    "size_mb": f"{size_mb:.2f} MB",
                    "created": img.attrs['Created'].split('T')[0] # Solo fecha
                })
            return formatted_images
        except APIError as e:
            print(f"Error al listar imágenes: {e}")
            return []

    def get_build_stream(self, path, tag):
        """Retorna el generador/stream de un build para ser consumido en un Hilo."""
        if not self.client: return
        print(f"Iniciando build en {path} con tag {tag}")
        # Usamos la API de bajo nivel para obtener un stream de bytes crudos
        # y evitar problemas con la decodificación automática del SDK.
        return self.client.api.build(path=path, tag=tag, rm=True, decode=False)

    def get_pull_stream(self, image_name):
        """Retorna el stream de un pull (descarga)."""
        if not self.client: return
        print(f"Iniciando pull de {image_name}")
        # Retorna un generador.
        return self.client.api.pull(image_name, stream=True, decode=True)

    def get_push_stream(self, image_name_with_tag):
        """Retorna el stream de un push (subida)."""
        if not self.client or not self.registry_logged_in:
            print("Debe estar logueado para hacer push.")
            yield {"error": "No autenticado en el registro."}
            return

        auth_config = {
            "username": self.registry_username,
            "password": self.registry_password_or_token
        }

        print(f"Iniciando push de {image_name_with_tag} con auth explícito y decodificación manual.")
        
        try:
            # DECODE=FALSE: Obtenemos bytes crudos para evitar bloqueos en el SDK
            original_stream = self.client.images.push(
                image_name_with_tag, 
                stream=True, 
                decode=False, 
                auth_config=auth_config
            )
            
            # Envolvemos el stream para decodificar y añadir depuración
            def stream_wrapper(stream):
                print("DEBUG: Wrapper: Verificando el stream de Docker (bytes)...", flush=True)
                had_items = False
                for chunk in stream:
                    had_items = True
                    try:
                        # Un chunk puede tener múltiples JSONs separados por \r\n
                        lines = chunk.decode('utf-8').splitlines()
                        for line in lines:
                            if line:
                                item = json.loads(line)
                                yield item
                    except (UnicodeDecodeError, json.JSONDecodeError) as e:
                        print(f"DEBUG: Wrapper: No se pudo decodificar el chunk: {chunk}, error: {e}", flush=True)

                if not had_items:
                    print("DEBUG: Wrapper: ¡ALERTA! El stream de Docker estaba vacío.", flush=True)
                    yield {"error": "El motor de Docker no devolvió información de progreso. Causa probable: error de red, firewall o un bug en Docker."}
                print("DEBUG: Wrapper: Fin del stream.", flush=True)

            return stream_wrapper(original_stream)

        except Exception as e:
            print(f"DEBUG: Excepción al llamar a client.images.push(): {e}", flush=True)
            yield {"error": f"Excepción al iniciar el push: {e}"}

    def run_container(self, image_name):
        """Intenta ejecutar un contenedor en modo detached."""
        if not self.client: return False, "Cliente no inicializado"
        try:
            container = self.client.containers.run(image_name, detach=True)
            return True, f"Contenedor {container.short_id} iniciado desde {image_name}."
        except docker.errors.ImageNotFound:
            return False, f"Error: Imagen '{image_name}' no encontrada."
        except APIError as e:
            return False, f"Error de API al iniciar {image_name}: {e}"
        except Exception as e:
            return False, f"Error inesperado: {e}"

    def tag_image(self, image_id_or_tag, new_tag_full):
        """Añade un nuevo tag a una imagen existente."""
        if not self.client: return False, "Cliente no inicializado"
        try:
            # Parsear el tag completo en repositorio y etiqueta
            repo_part, tag_part = (None, None)
            if ':' in new_tag_full:
                parts = new_tag_full.rsplit(':', 1)
                # Una comprobación simple: si la parte después de los dos puntos contiene '/',
                # es probable que sea parte de una ruta con un puerto, no una etiqueta.
                if '/' in parts[1]:
                    repo_part = new_tag_full
                    tag_part = 'latest'
                else:
                    repo_part = parts[0]
                    tag_part = parts[1]
            else:
                repo_part = new_tag_full
                tag_part = 'latest'

            print(f"DEBUG: Tagging with repo='{repo_part}' and tag='{tag_part}'")
            image = self.client.images.get(image_id_or_tag)
            success = image.tag(repository=repo_part, tag=tag_part)
            
            if success:
                return True, f"Imagen {image_id_or_tag} tageada como {new_tag_full}."
            else:
                # Es poco probable llegar aquí, ya que un fallo suele lanzar una excepción.
                return False, f"No se pudo tagear la imagen. Verifique que el tag no esté en uso."

        except docker.errors.ImageNotFound:
            return False, f"Error: Imagen '{image_id_or_tag}' no encontrada."
        except APIError as e:
            return False, f"Error de API al tagear: {e}"
        except ValueError:
            return False, f"Error: El formato del nuevo tag '{new_tag_full}' es inválido."
        except Exception as e:
            return False, f"Error inesperado al tagear: {e}"

    # --- Operaciones con Contenedores ---

    def list_containers(self, all_containers=True):
        """Devuelve una lista de contenedores formateados."""
        if not self.client: return []
        try:
            containers = self.client.containers.list(all=all_containers)
            formatted_containers = []
            for c in containers:
                # Formatear puertos
                ports_str = ""
                if c.ports:
                    ports_str = ", ".join([f"{k} -> {v[0]['HostPort']}" 
                                         for k, v in c.ports.items() if v])

                formatted_containers.append({
                    "id": c.short_id,
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                    "status": c.status,
                    "ports": ports_str
                })
            return formatted_containers
        except APIError as e:
            print(f"Error al listar contenedores: {e}")
            return []

    def stop_container(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            return True, f"Contenedor {container_id} detenido."
        except Exception as e:
            return False, f"Error al detener {container_id}: {e}"

    def remove_container(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            container.remove()
            return True, f"Contenedor {container_id} eliminado."
        except Exception as e:
            return False, f"Error al eliminar {container_id}: {e}"

    def get_logs_stream(self, container_id):
        """Retorna el stream de logs de un contenedor."""
        try:
            container = self.client.containers.get(container_id)
            # Retorna un generador de bytes
            return container.logs(stream=True, follow=True, stdout=True, stderr=True)
        except Exception as e:
            print(f"Error al obtener logs: {e}")
            yield f"Error al obtener logs: {e}".encode('utf-8')

    def get_stats_stream(self, container_id):
        """Retorna el stream de estadísticas (CPU, Mem) de un contenedor."""
        try:
            container = self.client.containers.get(container_id)
            # Retorna un generador de dicts
            return container.stats(stream=True, decode=True)
        except Exception as e:
            print(f"Error al obtener stats: {e}")
            yield {"error": f"Error al obtener stats: {e}"}


# =============================================================================
# 3. APLICACIÓN PRINCIPAL PYSIDE6 (main_app.py)
# =============================================================================

# --- Estilos CSS para el Tema Oscuro ---
DARK_STYLESHEET = """
QWidget {
    background-color: #2b2b2b;
    color: #f0f0f0;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}
QMainWindow {
    background-color: #1e1e1e;
}
QDialog {
    background-color: #3c3c3c;
}

/* --- Panel de Navegación --- */
QListWidget {
    background-color: #1e1e1e;
    border: none;
    padding-top: 10px;
}
QListWidget::item {
    padding: 12px 15px;
    border-radius: 5px;
    margin: 2px 5px;
    color: #aaaaaa;
}
QListWidget::item:hover {
    background-color: #2a2a2a;
}
QListWidget::item:selected {
    background-color: #007acc; /* Azul brillante para selección */
    color: #ffffff;
    font-weight: bold;
}

/* --- Botones --- */
QPushButton {
    background-color: #007acc;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #0098ff;
}
QPushButton:pressed {
    background-color: #005c99;
}
QPushButton:disabled {
    background-color: #555555;
    color: #999999;
}

/* --- Inputs --- */
QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
}
QLineEdit:focus {
    border-color: #007acc;
}

/* --- Tablas --- */
QTableView {
    background-color: #3c3c3c;
    border: 1px solid #444;
    gridline-color: #444;
    selection-background-color: #007acc;
}
QTableView::item {
    padding: 5px;
}
QHeaderView::section {
    background-color: #2b2b2b;
    border: 1px solid #444;
    padding: 6px;
    font-weight: bold;
}

/* --- Panel de Logs --- */
QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #444;
    border-radius: 4px;
    font-family: 'Consolas', 'Courier New', monospace;
    color: #dcdcdc;
}
"""

# --- Iconos (Usando recursos de PySide6 para evitar archivos externos) ---
def get_icon(name):
    try:
        # Intenta usar los iconos estándar de QStyle
        style = QApplication.style()
        if name == "home":
            return style.standardIcon(style.StandardPixmap.SP_ComputerIcon)
        if name == "image":
            return style.standardIcon(style.StandardPixmap.SP_DriveHDIcon)
        if name == "container":
            return style.standardIcon(style.StandardPixmap.SP_DriveNetIcon)
        if name == "logs":
            return style.standardIcon(style.StandardPixmap.SP_FileIcon)
        if name == "settings":
            return style.standardIcon(style.StandardPixmap.SP_SettingsIcon)
        if name == "error":
            return style.standardIcon(style.StandardPixmap.SP_DialogCriticalButton)
        if name == "info":
            return style.standardIcon(style.StandardPixmap.SP_DialogHelpButton)
        return QIcon()
    except Exception:
        return QIcon() # Fallback

# --- Hilos de Trabajo (Worker Threads) ---
class WorkerSignals(QObject):
    """Define las señales disponibles para un hilo de trabajo."""
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(object)

class Worker(QRunnable):
    """
    Worker genérico que ejecuta una función en el QThreadPool.
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        print(f"DEBUG: Worker.run: Entered for function '{self.fn.__name__}'.", flush=True)
        try:
            result = self.fn(*self.args, **self.kwargs)
            print(f"DEBUG: Worker.run: Function '{self.fn.__name__}' executed, got result: {result}", flush=True)

            if hasattr(result, '__next__') and hasattr(result, '__iter__'):
                print(f"DEBUG: Worker.run: Result is a generator. Iterating...", flush=True)
                # Es un generador (stream)
                item_count = 0
                for progress_data in result:
                    item_count += 1
                    print(f"DEBUG: Worker.run: Emitting progress signal for item {item_count}.", flush=True)
                    self.signals.progress.emit(progress_data)
                
                if item_count == 0:
                    print("DEBUG: Worker.run: WARNING - The stream/generator was empty.", flush=True)

                print("DEBUG: Worker.run: Generator finished. Emitting 'finished' signal.", flush=True)
                self.signals.finished.emit(None) 
            else:
                # Es un resultado normal
                print("DEBUG: Worker.run: Result is not a generator. Emitting 'finished' signal.", flush=True)
                self.signals.finished.emit(result)
                
        except Exception as e:
            print(f"DEBUG: Worker.run: Exception caught: {e}", flush=True)
            import traceback
            traceback.print_exc()
            self.signals.error.emit(str(e))
        finally:
            print(f"DEBUG: Worker.run: Exiting for function '{self.fn.__name__}'.", flush=True)


# --- Diálogo de Inicio de Sesión (Login) ---
class LoginDialog(QDialog):
    """Diálogo modal para solicitar credenciales del registro."""
    
    # MODIFICADO: Aceptar la URL del registro
    def __init__(self, docker_service, config_manager, registry_url, parent=None):
        super().__init__(parent)
        self.docker_service = docker_service
        self.config_manager = config_manager
        self.registry_url = registry_url # NUEVO
        
        # MODIFICADO: Título dinámico
        self.setWindowTitle(f"Login de Registro ({self.registry_url})")
        self.setMinimumWidth(350)
        self.setModal(True)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de usuario (ej. tu-usuario-github)")
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Token de Acceso Personal (PAT)")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton("Login y Guardar")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ffcccc;")

        info_label = QLabel(
            "Se recomienda usar un Token de Acceso Personal (PAT) con permisos 'read:packages' y 'write:packages'."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 9pt; color: #aaaaaa;")

        layout = QFormLayout(self)
        layout.addRow("Usuario:", self.username_input)
        layout.addRow("Token:", self.token_input)
        layout.addRow(info_label)
        layout.addRow(self.login_button)
        layout.addRow(self.status_label)

        self.login_button.clicked.connect(self.handle_login)
        self.threadpool = QThreadPool()

    def handle_login(self):
        """Inicia el proceso de login en un hilo."""
        username = self.username_input.text()
        token = self.token_input.text()
        
        if not username or not token:
            self.status_label.setText("Usuario y Token no pueden estar vacíos.")
            return

        self.login_button.setEnabled(False)
        self.status_label.setText(f"Autenticando en {self.registry_url}...")
        
        # MODIFICADO: Llamar al método generalizado
        worker = Worker(self.docker_service.login_to_registry, self.registry_url, username, token)
        worker.signals.finished.connect(self.on_login_finished)
        worker.signals.error.connect(self.on_login_error)
        self.threadpool.start(worker)

    @Slot(object)
    def on_login_finished(self, result):
        if result is None:
            self.on_login_error("Respuesta inesperada del proceso de login.")
            return

        success, message = result
        if success:
            self.status_label.setText("¡Éxito! Guardando credenciales...")
            self.config_manager.save_credentials(
                self.username_input.text(),
                self.token_input.text()
            )
            self.accept()
        else:
            self.on_login_error(message)

    @Slot(str)
    def on_login_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.login_button.setEnabled(True)


# --- Diálogo para Crear Dockerfile (SIN CAMBIOS) ---
class CreateDockerfileDialog(QDialog):
    """Diálogo para generar un Dockerfile básico para una app Python."""
    
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        
        self.setWindowTitle("Crear Dockerfile para App Python")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        # --- Widgets ---
        self.base_image_input = QLineEdit("python:3.10-slim")
        self.workdir_input = QLineEdit("/app")
        self.requirements_input = QLineEdit("requirements.txt")
        self.port_input = QLineEdit("8000")
        self.run_cmd_input = QLineEdit("gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000")

        self.create_button = QPushButton("Crear Dockerfile")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ffcccc;")

        info_label = QLabel(
            "Rellene los campos para generar un Dockerfile básico para una aplicación Python (ej. FastAPI/Flask)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 9pt; color: #aaaaaa;")

        # --- Layout ---
        layout = QFormLayout(self)
        layout.addRow(info_label)
        layout.addRow("Imagen Base:", self.base_image_input)
        layout.addRow("Directorio de Trabajo:", self.workdir_input)
        layout.addRow("Archivo de Dependencias:", self.requirements_input)
        layout.addRow("Puerto a Exponer:", self.port_input)
        layout.addRow("Comando de Ejecución:", self.run_cmd_input)
        layout.addRow(self.create_button)
        layout.addRow(self.status_label)

        # --- Conexiones ---
        self.create_button.clicked.connect(self.handle_create_file)

    def handle_create_file(self):
        """Genera y escribe el contenido del Dockerfile."""
        base_image = self.base_image_input.text()
        workdir = self.workdir_input.text()
        requirements = self.requirements_input.text()
        port = self.port_input.text()
        run_cmd = self.run_cmd_input.text()

        if not all([base_image, workdir, requirements, run_cmd]):
            self.status_label.setText("Error: Todos los campos son obligatorios.")
            return

        # --- Generar Contenido del Dockerfile ---
        content = f"""
# Dockerfile Básico para Aplicación Python

# 1. Imagen Base
FROM {base_image}

# 2. Directorio de Trabajo
WORKDIR {workdir}

# 3. Copiar dependencias e instalarlas
COPY {requirements} {requirements}
RUN pip install --no-cache-dir -r {requirements}

# 4. Copiar el resto de la aplicación
COPY . .

"""
        if port:
            content += f"# 5. Exponer puerto\nEXPOSE {port}\n\n"

        content += f"""# 6. Comando de ejecución
CMD [\"{run_cmd}\"]
"""
        # El comando CMD necesita ser parseado para el formato JSON
        # Esto es una simplificación, un CMD real podría necesitar más parsing
        # Por ahora, lo dividimos por espacios, lo cual es suficientemente bueno para muchos casos
        cmd_parts = run_cmd.split()
        cmd_json = json.dumps(cmd_parts)
        content = content.replace(f'[\"{run_cmd}\"]', cmd_json)


        # --- Escribir Archivo ---
        dockerfile_path = os.path.join(self.path, "Dockerfile")
        try:
            with open(dockerfile_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.status_label.setText(f"Dockerfile creado en {dockerfile_path}")
            self.accept() # Cerrar el diálogo con éxito

        except Exception as e:
            self.status_label.setText(f"Error al escribir archivo: {e}")


# --- Widget Principal del Dashboard ---
class DockerManagerWidget(QWidget):
    
    # MODIFICADO: Aceptar la URL del registro
    def __init__(self, docker_service, config_manager, registry_url, parent=None):
        super().__init__(parent)
        self.docker_service = docker_service
        self.config_manager = config_manager
        self.registry_url = registry_url # NUEVO
        self.threadpool = QThreadPool()
        self.current_op_has_error = False # Flag para rastrear errores en streams
        self.detected_repo_name = None # Para el nombre del repo detectado por git

        self.create_widgets()
        self.create_layout()
        
        self.load_containers_async()
        self.load_images_async()

    def create_widgets(self):
        """Crea todos los widgets que se usarán en la UI."""
        
        # --- 1. Panel de Navegación ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.setIconSize(QSize(24, 24))
        
        QListWidgetItem(get_icon("home"), "Home", self.nav_list)
        QListWidgetItem(get_icon("image"), "Imágenes", self.nav_list)
        QListWidgetItem(get_icon("container"), "Contenedores", self.nav_list)
        QListWidgetItem(get_icon("logs"), "Logs y Build", self.nav_list)
        QListWidgetItem(get_icon("settings"), "Configuración", self.nav_list)
        
        self.nav_list.setCurrentRow(0)

        # --- 2. Stack de Páginas ---
        self.main_stack = QStackedWidget()
        self.main_stack.addWidget(self.create_home_page())
        self.main_stack.addWidget(self.create_images_page())
        self.main_stack.addWidget(self.create_containers_page())
        self.main_stack.addWidget(self.create_logs_page())
        self.main_stack.addWidget(self.create_settings_page())
        
        # --- 3. Conexión de Navegación ---
        self.nav_list.currentRowChanged.connect(self.main_stack.setCurrentIndex)

    def create_layout(self):
        """Organiza los widgets principales en la ventana."""
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.nav_list)
        main_layout.addWidget(self.main_stack)
        
        self.setLayout(main_layout)

    # --- Constructores de Páginas ---

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title = QLabel("Bienvenido a DockerVizion")
        title.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        status = "Conectado a Docker Engine." if self.docker_service.client else "Error: No conectado a Docker."
        layout.addWidget(QLabel(status))
        
        # MODIFICADO: Usar variables y texto de registro general
        login_status = (f"Autenticado en {self.registry_url} como: {self.docker_service.registry_username}" 
                        if self.docker_service.registry_logged_in 
                        else f"No autenticado en {self.registry_url}.")
        layout.addWidget(QLabel(login_status))
        
        return page

    def create_images_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar = QHBoxLayout()
        self.btn_create_dockerfile = QPushButton(get_icon("info"), "Crear Dockerfile...")
        self.btn_build = QPushButton(get_icon("info"), "Buildear Imagen...")
        self.btn_push = QPushButton(get_icon("info"), "Subir (Push)...")
        self.btn_pull = QPushButton(get_icon("info"), "Descargar (Pull)...")
        self.btn_refresh_images = QPushButton(get_icon("info"), "Refrescar")
        
        toolbar.addWidget(self.btn_create_dockerfile)
        toolbar.addWidget(self.btn_build)
        toolbar.addWidget(self.btn_push)
        toolbar.addWidget(self.btn_pull)
        toolbar.addWidget(self.btn_refresh_images)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Conexiones
        self.btn_create_dockerfile.clicked.connect(self.handle_create_dockerfile_standalone)
        self.btn_build.clicked.connect(self.handle_build_image)
        self.btn_push.clicked.connect(self.handle_push_image)
        self.btn_pull.clicked.connect(self.handle_pull_image)
        self.btn_refresh_images.clicked.connect(self.load_images_async)
        
        self.images_table = QTableView()
        self.images_table.setSortingEnabled(True)
        self.images_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.images_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.images_model = QStandardItemModel()
        self.images_model.setHorizontalHeaderLabels(["ID", "Tags", "Tamaño (MB)", "Creada"])
        self.images_table.setModel(self.images_model)
        self.images_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.images_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.images_table)
        
        return page

    def create_containers_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        self.btn_run = QPushButton(get_icon("info"), "Levantar (Run)...")
        self.btn_refresh_containers = QPushButton(get_icon("info"), "Refrescar")
        
        toolbar.addWidget(self.btn_run)
        toolbar.addWidget(self.btn_refresh_containers)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Conexiones Toolbar
        self.btn_run.clicked.connect(self.handle_run_container)
        self.btn_refresh_containers.clicked.connect(self.load_containers_async)

        self.containers_table = QTableView()
        self.containers_table.setSortingEnabled(True)
        self.containers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.containers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.containers_model = QStandardItemModel()
        self.containers_model.setHorizontalHeaderLabels(["ID", "Nombre", "Imagen", "Estado", "Puertos"])
        self.containers_table.setModel(self.containers_model)
        self.containers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.containers_table)
        
        action_toolbar = QHBoxLayout()
        self.btn_view_logs = QPushButton("Ver Logs")
        self.btn_view_metrics = QPushButton("Ver Métricas")
        self.btn_stop_container = QPushButton("Detener (Stop)")
        self.btn_remove_container = QPushButton("Eliminar (Remove)")

        action_toolbar.addWidget(self.btn_view_logs)
        action_toolbar.addWidget(self.btn_view_metrics)
        action_toolbar.addWidget(self.btn_stop_container)
        action_toolbar.addWidget(self.btn_remove_container)
        action_toolbar.addStretch()
        layout.addLayout(action_toolbar)
        
        # Conexiones Action Toolbar
        self.btn_view_logs.clicked.connect(self.handle_view_logs)
        self.btn_view_metrics.clicked.connect(self.handle_view_metrics)
        self.btn_stop_container.clicked.connect(self.handle_stop_container)
        self.btn_remove_container.clicked.connect(self.handle_remove_container)
        
        return page

    def create_logs_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Logs de Build / Contenedor en Tiempo Real"))
        
        self.logs_output = QTextEdit()
        self.logs_output.setReadOnly(True)
        layout.addWidget(self.logs_output)
        
        self.logs_output.append("--- Panel de Logs listo ---")
        
        return page

    def create_settings_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        layout.setSpacing(10)
        
        title = QLabel("Configuración")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addRow(title)
        
        creds = self.config_manager.load_credentials()
        username = creds['username'] if creds else "N/A"
        token = ("*" * len(creds['token'])) if creds else "N/A"
        
        # MODIFICADO: Textos para el registro general
        layout.addRow(f"Usuario ({self.registry_url}):", QLabel(username))
        layout.addRow("Token guardado:", QLabel(token))
        
        change_creds_button = QPushButton("Cambiar/Actualizar Credenciales")
        change_creds_button.clicked.connect(self.show_login_dialog_force)
        layout.addRow(change_creds_button)

        # Separador
        separator = QWidget()
        separator.setFixedHeight(20)
        layout.addRow(separator)

        repo_title = QLabel("Repositorio Enlazado")
        repo_title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addRow(repo_title)

        self.linked_repo_label = QLabel(self.detected_repo_name or "Ninguno")
        layout.addRow("Nombre del Repositorio:", self.linked_repo_label)

        link_repo_button = QPushButton("Enlazar Carpeta de Repositorio...")
        link_repo_button.clicked.connect(self.handle_link_repo_folder)
        layout.addRow(link_repo_button)

        return page

    # --- Lógica Asíncrona (Carga de datos) ---

    def load_images_async(self):
        """Carga la lista de imágenes en un hilo de trabajo."""
        worker = Worker(self.docker_service.list_images)
        worker.signals.finished.connect(self.update_images_table)
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)

    @Slot(object)
    def update_images_table(self, images_list):
        """Actualiza la QTableView de imágenes con los datos recibidos."""
        self.images_model.clear()
        self.images_model.setHorizontalHeaderLabels(["ID", "Tags", "Tamaño (MB)", "Creada"])
        for img in images_list:
            row = [
                QStandardItem(img["id"]),
                QStandardItem(img["tags"]),
                QStandardItem(img["size_mb"]),
                QStandardItem(img["created"])
            ]
            self.images_model.appendRow(row)
        self.log_to_panel(f"Tabla de imágenes actualizada. {len(images_list)} imágenes encontradas.")

    def load_containers_async(self):
        """Carga la lista de contenedores en un hilo de trabajo."""
        worker = Worker(self.docker_service.list_containers)
        worker.signals.finished.connect(self.update_containers_table)
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)

    @Slot(object)
    def update_containers_table(self, containers_list):
        """Actualiza la QTableView de contenedores."""
        self.containers_model.clear()
        self.containers_model.setHorizontalHeaderLabels(["ID", "Nombre", "Imagen", "Estado", "Puertos"])
        for c in containers_list:
            row = [
                QStandardItem(c["id"]),
                QStandardItem(c["name"]),
                QStandardItem(c["image"]),
                QStandardItem(c["status"]),
                QStandardItem(c["ports"])
            ]
            # Colorear según estado
            if c["status"].startswith("running"):
                row[3].setForeground(Qt.GlobalColor.green)
            elif c["status"].startswith("exited"):
                row[3].setForeground(Qt.GlobalColor.gray)
            self.containers_model.appendRow(row)
        self.log_to_panel(f"Tabla de contenedores actualizada. {len(containers_list)} contenedores encontrados.")

    # --- Manejadores de Acciones ---
    
    def _get_selected_container_id(self):
        """Helper para obtener el ID del contenedor seleccionado en la tabla."""
        indexes = self.containers_table.selectionModel().selectedRows()
        if not indexes:
            self.log_to_panel("Por favor, seleccione un contenedor de la tabla.", "orange")
            return None
        
        selected_row = indexes[0].row()
        # Asumiendo que la Columna 0 es el ID
        id_item = self.containers_model.item(selected_row, 0)
        return id_item.text()

    def _get_selected_image_details(self):
        """Helper para obtener ID y tags de la imagen seleccionada."""
        indexes = self.images_table.selectionModel().selectedRows()
        if not indexes:
            self.log_to_panel("Por favor, seleccione una imagen de la tabla.", "orange")
            return None, None
        
        selected_row = indexes[0].row()
        # Columna 0 es "ID", Columna 1 es "Tags"
        id_item = self.images_model.item(selected_row, 0)
        tags_item = self.images_model.item(selected_row, 1)
        
        return id_item.text(), tags_item.text()

    def handle_create_dockerfile_standalone(self):
        """Muestra un diálogo para seleccionar una carpeta y luego crear un Dockerfile."""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para crear Dockerfile")
        if not path:
            return  # Usuario canceló

        # Verificar si ya existe un Dockerfile
        dockerfile_path = os.path.join(path, "Dockerfile")
        if os.path.exists(dockerfile_path):
            reply = QMessageBox.question(self, "Dockerfile ya existe",
                                         "Ya existe un Dockerfile en esta carpeta.\n"
                                         "¿Desea sobrescribirlo?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                self.log_to_panel("Creación de Dockerfile cancelada.", "yellow")
                return

        create_dialog = CreateDockerfileDialog(path, self)
        if create_dialog.exec() == QDialog.DialogCode.Accepted:
            self.log_to_panel(f"Dockerfile creado exitosamente en {path}", "green")
        else:
            self.log_to_panel("Creación de Dockerfile cancelada.", "yellow")

    def _get_repo_name_from_path(self, path):
        """
        Intenta obtener el nombre del repositorio de GitHub desde la URL del remoto 'origin'.
        """
        try:
            command = ["git", "config", "--get", "remote.origin.url"]
            result = subprocess.run(
                command,
                cwd=path,
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8'
            )

            if result.returncode != 0:
                print(f"Git command failed: {result.stderr.strip()}")
                return None

            remote_url = result.stdout.strip()
            match = re.search(r'(?:github\.com/|github\.com:)([\w-]+/[\w.-]+)', remote_url)

            if match:
                full_repo_path = match.group(1)
                if full_repo_path.endswith('.git'):
                    full_repo_path = full_repo_path[:-4]
                
                repo_name = full_repo_path.split('/')[-1]
                return repo_name

        except FileNotFoundError:
            self.log_to_panel("Comando 'git' no encontrado. No se puede detectar el nombre del repositorio.", "orange")
            return None
        except Exception as e:
            self.log_to_panel(f"Error al detectar el repositorio: {e}", "red")
            return None
        
        return None

    def handle_build_image(self):
        """Muestra diálogos para seleccionar carpeta y tag, luego inicia el build."""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta con Dockerfile")
        if not path:
            return  # Usuario canceló

        dockerfile_path = os.path.join(path, "Dockerfile")
        
        # Si no existe el Dockerfile, preguntar para crearlo
        if not os.path.exists(dockerfile_path):
            reply = QMessageBox.question(self, "Dockerfile no encontrado",
                                         "No se encontró un Dockerfile en la carpeta seleccionada.\n"
                                         "¿Desea crear uno ahora?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                create_dialog = CreateDockerfileDialog(path, self)
                if create_dialog.exec() != QDialog.DialogCode.Accepted:
                    self.log_to_panel("Creación de Dockerfile cancelada.", "yellow")
                    return # El usuario canceló la creación
            else:
                self.log_to_panel("Build cancelado: se requiere un Dockerfile.", "orange")
                return # El usuario no quiso crear el archivo

        # MODIFICADO: Ejemplo de tag para GHCR
        tag, ok = QInputDialog.getText(self, "Tag de la Imagen",
                                       f"Ingrese el tag (ej: {self.registry_url}/tu-usuario/mi-app:latest):")
        if not ok or not tag:
            return  # Usuario canceló

        self.log_to_panel(f"Iniciando build en {path} con tag {tag}...", "cyan")
        self.nav_list.setCurrentRow(3)  # Cambiar a la pestaña de Logs
        self.logs_output.clear()

        worker = Worker(self.docker_service.get_build_stream, path, tag)
        worker.signals.progress.connect(self.handle_build_progress)
        worker.signals.finished.connect(self.on_build_finished)
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)

    @Slot(object)
    def on_build_finished(self, result=None):
        self.log_to_panel("--- Build completado ---", "green")
        self.load_images_async() # Refrescar la lista de imágenes

    @Slot(object)
    def handle_build_progress(self, log_data_bytes):
        """Muestra la salida del stream de build en el panel de logs."""
        try:
            # log_data_bytes es un trozo de bytes. Puede contener múltiples líneas JSON.
            lines = log_data_bytes.decode('utf-8').strip().split('\n')
            for line in lines:
                if not line:
                    continue
                try:
                    log_data = json.loads(line)  # Parsea cada línea como JSON
                    if 'stream' in log_data:
                        self.log_to_panel(log_data['stream'].strip(), color=None, move_cursor=True)
                    elif 'error' in log_data:
                        self.log_to_panel(log_data['error'].strip(), color="red", move_cursor=True)
                    elif 'status' in log_data:
                        # También maneja mensajes de 'status' para progreso tipo pull
                        progress = log_data.get('progress', '')
                        self.log_to_panel(f"{log_data['status']} {progress}".strip(), color='gray', move_cursor=True)
                    else:
                        self.log_to_panel(f"Build data (inesperado): {log_data}", color="yellow", move_cursor=True)
                except json.JSONDecodeError:
                    # Si una línea no es JSON, la imprime en crudo
                    self.log_to_panel(f"Build data (raw): {line}", color="yellow", move_cursor=True)
        except UnicodeDecodeError:
            pass  # Ignorar bytes corruptos

    def handle_pull_image(self):
        """Pide un nombre de imagen y la descarga (pull)."""
        # MODIFICADO: Ejemplo de pull para GHCR
        image_name, ok = QInputDialog.getText(self, "Descargar Imagen (Pull)", 
                                              f"Nombre de la imagen (ej: {self.registry_url}/usuario/imagen:latest):")
        if not ok or not image_name:
            return
        
        self.log_to_panel(f"Iniciando pull de {image_name}...", "cyan")
        self.nav_list.setCurrentRow(3) # Pestaña de Logs
        self.logs_output.clear()

        worker = Worker(self.docker_service.get_pull_stream, image_name)
        worker.signals.progress.connect(self.handle_pull_progress)
        worker.signals.finished.connect(self.on_pull_finished)
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)

    @Slot(object)
    def handle_pull_progress(self, log_data):
        """Muestra el progreso del pull."""
        status = log_data.get('status', '')
        progress = log_data.get('progress', '')
        self.log_to_panel(f"{status} {progress}", color=None, move_cursor=True)

    @Slot(object)
    def on_pull_finished(self, result=None):
        self.log_to_panel("--- Pull completado ---", "green")
        self.load_images_async()

    def handle_push_image(self):
        """Maneja la lógica para subir (push) una imagen al registro."""
        if not self.docker_service.registry_logged_in:
            self.log_to_panel(f"Debe estar autenticado en {self.registry_url} para poder subir imágenes.", "orange")
            self.show_login_dialog_force()
            return

        image_id, tags_str = self._get_selected_image_details()
        if not tags_str:
            return # Mensaje ya mostrado por el helper

        self.log_to_panel(f"--- Iniciando proceso de Push ---", "blue")
        self.log_to_panel(f"Imagen seleccionada: ID={image_id}, Tags='{tags_str}'", "blue")

        tags = [tag.strip() for tag in tags_str.split(',')]
        
        # 1. Determinar el tag a pushear
        tag_to_push = None
        if len(tags) == 1:
            tag_to_push = tags[0]
        else:
            # Si hay múltiples tags, preguntar al usuario
            tag_to_push, ok = QInputDialog.getItem(self, "Seleccionar Tag", 
                                                   "Esta imagen tiene múltiples tags. ¿Cuál desea subir?", tags, 0, False)
            if not ok or not tag_to_push:
                self.log_to_panel("Push cancelado.", "yellow")
                return

        # 2. Verificar si el tag es compatible con el registro
        if not tag_to_push.startswith(self.registry_url):
            self.log_to_panel(f"El tag '{tag_to_push}' no parece ser para el registro '{self.registry_url}'.", "yellow")
            
            # Sugerir un nuevo tag usando el repo detectado si existe
            repo_placeholder = self.detected_repo_name or "my-app"
            suggested_tag = f"{self.registry_url}/{self.docker_service.registry_username.lower()}/{repo_placeholder}:latest"
            new_tag, ok = QInputDialog.getText(self, "Retagear Imagen",
                                               f"Por favor, ingrese un nuevo tag completo para el registro:",
                                               QLineEdit.EchoMode.Normal,
                                               suggested_tag)
            
            if not ok or not new_tag:
                self.log_to_panel("Push cancelado.", "yellow")
                return

            # FIX: Docker repository names must be lowercase.
            try:
                # Separate registry from the rest of the tag, if present
                registry = ""
                repo_and_tag = new_tag
                
                parts = new_tag.split('/', 1)
                if len(parts) > 1 and ('.' in parts[0] or ':' in parts[0]):
                    registry = parts[0]
                    repo_and_tag = parts[1]

                # Lowercase the repository and tag part
                repo_and_tag_lower = repo_and_tag.lower()
                
                # Reassemble the full tag
                final_tag = f"{registry}/{repo_and_tag_lower}" if registry else repo_and_tag_lower

                if final_tag != new_tag:
                    self.log_to_panel(f"Aviso: El nombre del repositorio ha sido convertido a minúsculas: {final_tag}", "yellow")
                
                new_tag = final_tag
            except Exception as e:
                self.log_to_panel(f"Error inesperado al procesar el tag '{new_tag}': {e}", "red")
                return
            
            # Ejecutar el retag en un worker
            self.log_to_panel(f"Retageando '{tag_to_push}' a '{new_tag}'...", "cyan")
            worker = Worker(self.docker_service.tag_image, tag_to_push, new_tag)
            # Cuando termine, llamará a _start_push_worker con el nuevo tag
            worker.signals.finished.connect(lambda result: self._on_retag_finished(result, new_tag))
            worker.signals.error.connect(self.log_error)
            self.threadpool.start(worker)
        else:
            # El tag es correcto, iniciar el push directamente
            self._start_push_worker(tag_to_push)

    @Slot(object, str)
    def _on_retag_finished(self, result, new_tag):
        """Se llama cuando la operación de retag ha finalizado."""
        success, message = result
        self.log_to_panel(message, "green" if success else "red")
        
        if success:
            # Iniciar el push PRIMERO para evitar posibles conflictos de UI/hilos
            self._start_push_worker(new_tag) 
            # Luego, refrescar la lista de imágenes en segundo plano
            self.load_images_async() 
        else:
            self.log_to_panel("No se pudo retagear la imagen. Push cancelado.", "red")

    def _start_push_worker(self, tag_to_push):
        """Inicia el worker para la operación de push."""
        print(f"DEBUG: Starting push worker for tag: {tag_to_push}", flush=True)
        self.current_op_has_error = False # Resetear el flag de error
        self.log_to_panel(f"Iniciando push de {tag_to_push}...", "cyan")
        self.nav_list.setCurrentRow(3) # Pestaña de Logs
        self.logs_output.clear()

        worker = Worker(self.docker_service.get_push_stream, tag_to_push)
        worker.signals.progress.connect(self.handle_push_progress)
        worker.signals.finished.connect(self.on_push_finished)
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)

    @Slot(object)
    def handle_push_progress(self, log_data):
        """Muestra el progreso del push y detecta errores."""
        print(f"DEBUG (push stream): {log_data}", flush=True) # Para depuración en consola

        if 'errorDetail' in log_data or 'error' in log_data:
            self.current_op_has_error = True
            error_message = log_data.get('error', '')
            if not error_message:
                error_message = log_data.get('errorDetail', {}).get('message', 'Error desconocido durante el push.')
            
            self.log_to_panel(f"ERROR: {error_message}", "red", move_cursor=True)
            return

        status = log_data.get('status', '')
        progress = log_data.get('progress', '')
        
        # Filtrar para no mostrar todos los mensajes de "Layer already exists"
        if status not in ["Layer already exists", "Waiting"]:
            self.log_to_panel(f"{status} {progress}".strip(), color=None, move_cursor=True)

    @Slot(object)
    def on_push_finished(self, result=None):
        if self.current_op_has_error:
            self.log_to_panel("--- Push fallido ---", "red")
            self.log_to_panel("Causa más común: El Token de Acceso Personal (PAT) no tiene el permiso 'write:packages'.", "yellow")
        else:
            self.log_to_panel("--- Push completado ---", "green")
            self.log_to_panel("Si la imagen no aparece en tu repositorio de GitHub, ve a la sección 'Packages' de tu perfil/organización y puede que necesites vincular el paquete a un repositorio manualmente.", "yellow")
        # No es necesario refrescar imágenes aquí, ya que no cambian

    def handle_link_repo_folder(self):
        """
        Abre un diálogo para que el usuario seleccione una carpeta de repositorio
        y detecta el nombre del mismo.
        """
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Repositorio Local")
        if not path:
            return # Usuario canceló

        repo_name = self._get_repo_name_from_path(path)
        if repo_name:
            self.detected_repo_name = repo_name.lower()
            self.log_to_panel(f"Repositorio enlazado: {self.detected_repo_name}", "green")
            if hasattr(self, 'linked_repo_label'):
                self.linked_repo_label.setText(self.detected_repo_name)
        else:
            self.detected_repo_name = None
            self.log_to_panel("No se pudo detectar un repositorio de GitHub en la carpeta seleccionada.", "orange")
            if hasattr(self, 'linked_repo_label'):
                self.linked_repo_label.setText("Ninguno")

    def handle_run_container(self):
        """Pide una imagen y la ejecuta (run)."""
        image_name, ok = QInputDialog.getText(self, "Ejecutar Imagen (Run)", 
                                              "Nombre de la imagen a ejecutar:")
        if not ok or not image_name:
            return

        self.log_to_panel(f"Intentando ejecutar {image_name}...", "cyan")
        worker = Worker(self.docker_service.run_container, image_name)
        worker.signals.finished.connect(self.on_simple_action_finished) # Reusa el handler simple
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)

    def handle_stop_container(self):
        container_id = self._get_selected_container_id()
        if not container_id: return
        
        self.log_to_panel(f"Intentando detener {container_id}...", "orange")
        worker = Worker(self.docker_service.stop_container, container_id)
        worker.signals.finished.connect(self.on_simple_action_finished)
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)
        
    def handle_remove_container(self):
        container_id = self._get_selected_container_id()
        if not container_id: return
        
        self.log_to_panel(f"Intentando eliminar {container_id}...", "orange")
        worker = Worker(self.docker_service.remove_container, container_id)
        worker.signals.finished.connect(self.on_simple_action_finished)
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)

    @Slot(object)
    def on_simple_action_finished(self, result):
        """Manejador genérico para acciones simples (Stop, Remove, Run)."""
        success, message = result
        if success:
            self.log_to_panel(message, "green")
            self.load_containers_async() # Refrescar lista de contenedores
        else:
            self.log_to_panel(message, "red")

    def handle_view_logs(self):
        container_id = self._get_selected_container_id()
        if not container_id: return

        self.log_to_panel(f"Obteniendo logs para {container_id}...", "cyan")
        self.nav_list.setCurrentRow(3) # Pestaña de Logs
        self.logs_output.clear()

        worker = Worker(self.docker_service.get_logs_stream, container_id)
        worker.signals.progress.connect(self.handle_log_stream)
        worker.signals.finished.connect(lambda: self.log_to_panel("--- Fin del stream de logs ---", "gray"))
        worker.signals.error.connect(self.log_error)
        self.threadpool.start(worker)

    @Slot(object)
    def handle_log_stream(self, log_data_bytes):
        """Muestra la salida de logs de un contenedor."""
        try:
            self.log_to_panel(log_data_bytes.decode('utf-8').strip(), color=None, move_cursor=True)
        except UnicodeDecodeError:
            pass # Ignorar bytes corruptos

    def handle_view_metrics(self):
        container_id = self._get_selected_container_id()
        if not container_id: return
        
        self.log_to_panel(f"Función 'Ver Métricas' para {container_id} no implementada.", "yellow")
        # TODO: Iniciar un stream de stats (get_stats_stream) y mostrarlo en una
        # ventana/panel separado, actualizándose en tiempo real.
        # Esto es más complejo ya que el stream no "termina" mientras
        # el contenedor esté vivo.

    # --- Utilidades ---
    
    def show_login_dialog_force(self):
        """Muestra el diálogo de login, incluso si ya hay credenciales."""
        # MODIFICADO: Pasar la URL del registro al diálogo
        dialog = LoginDialog(self.docker_service, self.config_manager, self.registry_url, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.log_to_panel("Credenciales actualizadas exitosamente.")
            
            # MODIFICADO: Actualizar el título de la ventana principal
            if hasattr(self.window(), 'setWindowTitle'):
                 self.window().setWindowTitle(f"DockerVizion (Usuario: {self.docker_service.registry_username} @ {self.registry_url})")
                 
            # Recargar página de settings
            self.main_stack.removeWidget(self.main_stack.widget(4))
            self.main_stack.insertWidget(4, self.create_settings_page())
        
    @Slot(str)
    def log_error(self, message):
        """Muestra un error en el panel de logs."""
        print(f"Error en worker: {message}")
        self.log_to_panel(f"[ERROR] {message}", color="red")

    def log_to_panel(self, message, color=None, move_cursor=False):
        """Añade un mensaje al panel de logs."""
        if hasattr(self, 'logs_output'):
            if color:
                self.logs_output.append(f"<span style='color:{color};'>{message}</span>")
            else:
                self.logs_output.append(message)
            
            if move_cursor:
                self.logs_output.moveCursor(QTextCursor.MoveOperation.End)

        print(message)


# --- Ventana Principal para modo Standalone ---
class MainWindow(QMainWindow):
    # MODIFICADO: Aceptar la URL del registro
    def __init__(self, docker_service, config_manager, registry_url):
        super().__init__()
        # MODIFICADO: Título de ventana dinámico
        self.setWindowTitle(f"DockerVizion Dashboard (Usuario: {docker_service.registry_username} @ {registry_url})")
        self.setGeometry(100, 100, 1280, 720)
        
        # MODIFICADO: Pasar la URL del registro al widget principal
        docker_widget = DockerManagerWidget(docker_service, config_manager, registry_url, self)
        self.setCentralWidget(docker_widget)


# =============================================================================
# 4. PUNTO DE ENTRADA DE LA APLICACIÓN
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    
    # NUEVO: Definir el registro aquí
    REGISTRY_URL = "ghcr.io"
    
    # 1. Inicializar servicios
    config_manager = ConfigManager()
    docker_service = DockerService()

    # 2. Verificar conexión con Docker Engine
    connected, error_msg = docker_service.check_connection()
    if not connected:
        QMessageBox.critical(None, "Error de Conexión Docker", error_msg)
        sys.exit(1)

    # 3. Intentar cargar credenciales y autenticarse
    creds = config_manager.load_credentials()
    
    if creds:
        print("Credenciales encontradas, intentando login automático...")
        # MODIFICADO: Usar el método generalizado con la URL del registro
        success, msg = docker_service.login_to_registry(REGISTRY_URL, creds['username'], creds['token'])
        if not success:
            print(f"Login automático fallido: {msg}")
            creds = None 
    
    # 4. Si no hay credenciales (o fallaron), mostrar diálogo de login
    if not creds:
        print("No se encontraron credenciales válidas. Mostrando diálogo de login.")
        # MODIFICADO: Pasar la URL del registro al diálogo
        login_dialog = LoginDialog(docker_service, config_manager, REGISTRY_URL)
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            print("Login cancelado por el usuario. Saliendo.")
            sys.exit(0)

    # 5. Si llegamos aquí, estamos conectados y autenticados
    # MODIFICADO: Pasar la URL del registro a la ventana principal
    main_window = MainWindow(docker_service, config_manager, REGISTRY_URL)
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()