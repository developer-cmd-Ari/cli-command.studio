
# =============================================================================
# 1. IMPORTACIONES Y CONSTANTES GLOBALES
# =============================================================================

import sys
import os
import json
import requests
import git
import subprocess
import datetime
from cryptography.fernet import Fernet
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QTextEdit, QFileDialog,
    QMessageBox, QDialog, QFormLayout, QLabel, QStatusBar, QInputDialog,
    QTabWidget, QTableView, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QDesktopServices, QTextCursor, QColor, QStandardItemModel, QStandardItem

# --- Constantes Globales ---
CONFIG_DIR = Path.home() / ".github_manager"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEY_FILE = CONFIG_DIR / "app.key"
LOG_FILE = CONFIG_DIR / "manager.log"
GITHUB_API_URL = "https://api.github.com"

# --- Estilo (Dark Mode + Red Accent) ---
DARK_STYLE = """
    QWidget {
        background-color: #2b2b2b;
        color: #f0f0f0;
        font-family: Arial;
        font-size: 10pt;
    }
    QMainWindow, QDialog {
        background-color: #3c3c3c;
    }
    QLineEdit, QTextEdit, QComboBox {
        background-color: #454545;
        border: 1px solid #5a5a5a;
        border-radius: 4px;
        padding: 5px;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox::down-arrow {
        image: url(none); /* Ocultar flecha por defecto */
    }
    QPushButton {
        background-color: #5a5a5a;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #6a6a6a;
    }
    QPushButton:pressed {
        background-color: #7a7a7a;
    }
    /* Botón de acento rojo */
    QPushButton#commit_push_btn {
        background-color: #c92121;
        color: white;
    }
    QPushButton#commit_push_btn:hover {
        background-color: #e02f2f;
    }
    QPushButton#commit_push_btn:pressed {
        background-color: #b01e1e;
    }
    QStatusBar {
        background-color: #2b2b2b;
        color: #f0f0f0;
    }
    QStatusBar::item {
        border: none;
    }
"""

# =============================================================================
# 2. CLASE SETTINGSMANAGER (MANEJO DE CREDENCIALES)
# =============================================================================

class SettingsManager:
    """
    Maneja la carga, guardado y encriptación/desencriptación de credenciales.
    """
    def __init__(self):
        self.key = self._get_or_generate_key()
        self.fernet = Fernet(self.key)
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _get_or_generate_key(self):
        if not KEY_FILE.exists():
            key = Fernet.generate_key()
            with open(KEY_FILE, 'wb') as f:
                f.write(key)
        else:
            with open(KEY_FILE, 'rb') as f:
                key = f.read()
        return key

    def save_credentials(self, username, email, token):
        encrypted_token = self.fernet.encrypt(token.encode()).decode()
        data = {
            'username': username,
            'email': email,
            'token': encrypted_token
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except IOError:
            return False

    def load_credentials(self):
        if not CONFIG_FILE.exists():
            return None
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            
            token = self.fernet.decrypt(data['token'].encode()).decode()
            return data['username'], data['email'], token
        except Exception:
            # Si falla la desencriptación (ej. cambió la clave), borrar
            self.clear_credentials()
            return None

    def clear_credentials(self):
        if CONFIG_FILE.exists():
            os.remove(CONFIG_FILE)
            
    def credentials_exist(self):
        return CONFIG_FILE.exists()

# =============================================================================
# 3. CLASE GITHUBAPI (INTERFAZ CON LA API DE GITHUB)
# =============================================================================

class GitHubAPI:
    """
    Wrapper para la API REST de GitHub usando 'requests'.
    """
    def __init__(self, username, token, logger):
        self.username = username
        self.token = token
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHubManagerApp'
        })

    def _request(self, method, endpoint, **kwargs):
        try:
            url = f"{GITHUB_API_URL}/{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            self.logger.log(f"Error HTTP: {e.response.status_code} - {e.response.text}", "ERROR")
        except requests.exceptions.RequestException as e:
            self.logger.log(f"Error de conexión: {e}", "ERROR")
        return None

    def list_repos(self):
        response = self._request('GET', 'user/repos?type=owner&per_page=100')
        if response:
            try:
                repos = response.json()
                return sorted([repo['full_name'] for repo in repos])
            except json.JSONDecodeError:
                self.logger.log("Error al decodificar la respuesta de repositorios.", "ERROR")
                return []
        return []

    def list_branches(self, repo_full_name):
        response = self._request('GET', f'repos/{repo_full_name}/branches')
        if response:
            try:
                branches = response.json()
                return [branch['name'] for branch in branches]
            except json.JSONDecodeError:
                self.logger.log("Error al decodificar la respuesta de ramas.", "ERROR")
                return []
        return []

    def create_branch(self, repo_full_name, base_branch, new_branch):
        # 1. Obtener el SHA de la rama base
        ref_response = self._request('GET', f'repos/{repo_full_name}/git/ref/heads/{base_branch}')
        if not ref_response:
            self.logger.log(f"No se pudo obtener el SHA de la rama base '{base_branch}'", "ERROR")
            return False
        
        try:
            base_sha = ref_response.json()['object']['sha']
        except (KeyError, json.JSONDecodeError):
            self.logger.log("Respuesta inesperada al obtener SHA.", "ERROR")
            return False

        # 2. Crear la nueva rama (referencia)
        payload = {
            "ref": f"refs/heads/{new_branch}",
            "sha": base_sha
        }
        create_response = self._request('POST', f'repos/{repo_full_name}/git/refs', json=payload)
        
        if create_response and create_response.status_code == 201:
            self.logger.log(f"Rama remota '{new_branch}' creada exitosamente.", "INFO")
            return True
        else:
            self.logger.log(f"No se pudo crear la rama remota '{new_branch}'.", "ERROR")
            return False

# =============================================================================
# 4. CLASE LOCALGIT (OPERACIONES GIT LOCALES)
# =============================================================================

class LocalGit:
    """
    Maneja operaciones de Git en el repositorio local usando 'GitPython'.
    """
    def __init__(self, path, logger):
        self.logger = logger
        self.repo_path = path
        self.repo = None
        try:
            self.repo = git.Repo(self.repo_path)
            self.logger.log(f"Repositorio Git cargado desde: {path}", "INFO")
        except git.InvalidGitRepositoryError:
            self.logger.log(f"El directorio seleccionado no es un repositorio Git válido.", "ERROR")
        except git.NoSuchPathError:
            self.logger.log(f"El directorio no existe: {path}", "ERROR")
        except Exception as e:
            self.logger.log(f"Error al cargar el repositorio: {e}", "ERROR")

    def initialize_repository(path, logger):
        try:
            logger.log(f"Inicializando repositorio Git en: {path}", "INFO")
            repo = git.Repo.init(path)
            logger.log("Repositorio inicializado exitosamente.", "SUCCESS")
            return repo
        except Exception as e:
            logger.log(f"Error al inicializar el repositorio: {e}", "ERROR")
            return None

    def is_valid_repo(self):
        return self.repo is not None

    def get_remote_url(self):
        if not self.is_valid_repo() or not self.repo.remotes:
            return None
        return self.repo.remotes.origin.url

    def update_remote_url_with_token(self, username, token):
        """ Reconfigura la URL del remoto 'origin' para incluir el token. """
        if not self.is_valid_repo():
            return
        
        try:
            remote = self.repo.remotes.origin
            original_url = remote.url
            
            if "https://" in original_url and "@" not in original_url:
                # Extraer 'user/repo.git' de 'https://github.com/user/repo.git'
                url_parts = original_url.split('https://')[-1].split('/')
                domain = url_parts[0] # github.com
                repo_path = "/".join(url_parts[1:]) # user/repo.git
                
                new_url = f"https://{username}:{token}@{domain}/{repo_path}"
                
                with remote.config_writer as writer:
                    writer.set("url", new_url)
                
                self.logger.log("URL del remoto 'origin' actualizada con token para autenticación.", "INFO")
        except Exception as e:
            self.logger.log(f"No se pudo actualizar la URL del remoto: {e}", "WARNING")

    def get_current_branch(self):
        if not self.is_valid_repo():
            return "N/A"
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "(detached HEAD)"

    def get_local_branches(self):
        if not self.is_valid_repo():
            return []
        return [b.name for b in self.repo.branches]

    def fetch(self):
        try:
            self.repo.remotes.origin.fetch()
            self.logger.log("Fetch de 'origin' completado.", "INFO")
            return True
        except Exception as e:
            self.logger.log(f"Error durante el fetch: {e}", "ERROR")
            return False

    def get_remote_branches(self):
        if not self.is_valid_repo():
            return None # Indicar fallo
        
        if not self.fetch():
            return None # Indicar fallo
            
        try:
            remote_refs = self.repo.remotes.origin.refs
            branches = [r.name.split('/')[-1] for r in remote_refs if r.remote_head and 'HEAD' not in r.name]
            return list(set(branches))
        except Exception as e:
            self.logger.log(f"Error procesando ramas remotas: {e}", "ERROR")
            return None # Indicar fallo

    def checkout_branch(self, name):
        try:
            self.logger.log(f"Ejecutando checkout en el directorio: {self.repo.working_dir}", "DEBUG")
            # Usar '--' para asegurar que el nombre de la rama se trate como un solo argumento
            self.repo.git.checkout(name)
            self.logger.log(f"Cambiado a la rama local '{name}'.", "INFO")
            return True
        except git.GitCommandError as e:
            self.logger.log(f"Error al cambiar de rama: {e}", "ERROR")
            return False

    def create_and_checkout_branch(self, name, base="HEAD", from_remote=False):
        try:
            if from_remote:
                # Crear rama local rastreando la remota
                self.repo.git.checkout('-b', name, '--', f'origin/{name}')
                self.logger.log(f"Rama '{name}' creada y rastreando 'origin/{name}'.", "INFO")
            else:
                # Usar 'git checkout -b' que es atómico y más seguro
                self.repo.git.checkout('-b', name, base)
                self.logger.log(f"Nueva rama local '{name}' creada desde '{base}'.", "INFO")
            return True
        except Exception as e:
            self.logger.log(f"Error al crear la rama '{name}': {e}", "ERROR")
            return False

    def prune_repo(self):
        if not self.is_valid_repo():
            return False
        try:
            self.repo.git.gc(prune='now')
            return True
        except Exception as e:
            self.logger.log(f"Error durante git gc: {e}", "ERROR")
            return False

    def get_status(self):
        """
        Devuelve una lista de todos los archivos modificados, nuevos (untracked), y eliminados.
        Retorna una lista de tuplas (status_char, file_path).
        """
        if not self.is_valid_repo():
            return []
        
        # GitPython's is_dirty() is simpler but porcelain is more detailed
        status_text = self.repo.git.status('--porcelain')
        self.logger.log(f"Salida de 'git status --porcelain':\n{status_text}", "INFO") # DEBUG
        if not status_text:
            return []

        files = []
        for line in status_text.split('\n'):
            if not line:
                continue
            status, file_path = line[:2], line[3:]
            files.append((status.strip(), file_path.strip()))
        return files

    def add_files(self, file_paths):
        """Añade una lista de archivos al staging area (index)."""
        if not self.is_valid_repo():
            return False
        try:
            self.repo.index.add(file_paths)
            self.logger.log(f"{len(file_paths)} archivo(s) añadido(s) al staging area.", "INFO")
            return True
        except Exception as e:
            self.logger.log(f"Error al añadir archivos: {e}", "ERROR")
            return False

    def get_staged_files(self):
        """Devuelve una lista de archivos en el staging area."""
        if not self.is_valid_repo():
            return []
        
        try:
            # Si no hay commits, repo.head.commit lanzará un ValueError
            staged_diffs = self.repo.index.diff('HEAD')
        except git.exc.GitCommandError as e:
            # Capturar el error específico de que HEAD no existe
            if "bad revision 'HEAD'" in str(e):
                # No hay commits, por lo tanto no hay nada "staged" contra un commit anterior.
                # Devolver una lista vacía es el comportamiento correcto.
                return []
            else:
                # Si es otro error de git, lo relanzamos o lo logueamos
                self.logger.log(f"Error inesperado en get_staged_files: {e}", "ERROR")
                return []

        return [diff.b_path or diff.a_path for diff in staged_diffs]

    def commit_all(self, message, author_name, author_email):
        try:
            with self.repo.config_writer() as writer:
                writer.set_value("user", "name", author_name)
                writer.set_value("user", "email", author_email)
            
            if not self.repo.is_dirty(untracked_files=True):
                self.logger.log("No hay cambios para hacer commit.", "INFO")
                return False

            self.repo.git.add(A=True)
            self.repo.index.commit(message)
            self.logger.log(f"Commit realizado: '{message}'", "INFO")
            return True
        except Exception as e:
            self.logger.log(f"Error durante el commit: {e}", "ERROR")
            return False

    def commit_staged(self, message, author_name, author_email):
        """Realiza un commit únicamente de los archivos que ya están en el staging area."""
        if not self.is_valid_repo():
            return False
        try:
            if self.repo.index.diff('HEAD') == []:
                self.logger.log("No hay cambios en el staging area para hacer commit.", "WARNING")
                return False

            with self.repo.config_writer() as writer:
                writer.set_value("user", "name", author_name)
                writer.set_value("user", "email", author_email)

            self.repo.index.commit(message)
            self.logger.log(f"Commit (solo staged) realizado: '{message}'", "INFO")
            return True
        except Exception as e:
            self.logger.log(f"Error durante el commit (solo staged): {e}", "ERROR")
            return False

    def unstage_files(self, file_paths):
        """Quita una lista de archivos del staging area."""
        if not self.is_valid_repo() or not file_paths:
            return False
        try:
            self.repo.index.reset('HEAD', paths=file_paths)
            self.logger.log(f"{len(file_paths)} archivo(s) quitado(s) del staging area.", "INFO")
            return True
        except Exception as e:
            self.logger.log(f"Error al quitar archivos del staging: {e}", "ERROR")
            return False

    def push_current(self):
        try:
            current_branch = self.repo.active_branch
            self.repo.remotes.origin.push(current_branch.name, set_upstream=True)
            self.logger.log(f"Push a 'origin/{current_branch.name}' exitoso.", "INFO")
            return True
        except Exception as e:
            self.logger.log(f"Error durante el push: {e}", "ERROR")
            return False

    def get_commits(self, revision, max_count=100):
        """Devuelve una lista de commits para una revisión dada (ej. 'main', 'origin/main..main')."""
        if not self.is_valid_repo():
            return None
        try:
            commits = list(self.repo.iter_commits(revision, max_count=max_count))
            commit_data = []
            for c in commits:
                commit_data.append({
                    "sha": c.hexsha[:7],
                    "author": c.author.name,
                    "date": datetime.datetime.fromtimestamp(c.committed_date).strftime('%Y-%m-%d %H:%M'),
                    "message": c.message.split('\n')[0]
                })
            return commit_data
        except git.GitCommandError as e:
            self.logger.log(f"Error al obtener commits para '{revision}': {e}", "ERROR")
            return None

    def get_unpushed_commits(self):
        """Devuelve los commits locales que no están en la rama remota de seguimiento."""
        if not self.is_valid_repo():
            return None
        
        try:
            current_branch = self.repo.active_branch
            tracking_branch = current_branch.tracking_branch()
            
            if not tracking_branch:
                self.logger.log(f"La rama actual '{current_branch.name}' no está rastreando una rama remota.", "WARNING")
                return []

            revision_spec = f'{tracking_branch.name}..{current_branch.name}'
            self.logger.log(f"Buscando commits no pusheados con la revisión: {revision_spec}", "INFO")
            return self.get_commits(revision_spec)

        except Exception as e:
            self.logger.log(f"Error al obtener commits no pusheados: {e}", "ERROR")
            return None

    def checkout_commit(self, sha):
        """Crea una nueva rama desde un commit específico."""
        if not self.is_valid_repo():
            return False
        try:
            new_branch_name = f"commit-{sha}"
            self.logger.log(f"Creando nueva rama '{new_branch_name}' desde el commit {sha}...", "INFO")
            self.repo.git.checkout('-b', new_branch_name, sha)
            self.logger.log(f"Checkout exitoso a la nueva rama '{new_branch_name}'.", "SUCCESS")
            return True
        except git.GitCommandError as e:
            self.logger.log(f"Error durante el checkout del commit: {e}", "ERROR")
            return False

    def revert_commit(self, sha, author_name, author_email):
        """Revierte un commit creando un nuevo commit que deshace los cambios."""
        if not self.is_valid_repo():
            return False
        try:
            with self.repo.config_writer() as writer:
                writer.set_value("user", "name", author_name)
                writer.set_value("user", "email", author_email)
            
            self.repo.git.revert(sha, no_edit=True)
            self.logger.log(f"Revert del commit {sha} exitoso.", "SUCCESS")
            return True
        except git.GitCommandError as e:
            self.logger.log(f"Error durante el revert del commit: {e}", "ERROR")
            return False

# =============================================================================
# 5. CLASE CREDENTIALSDIALOG (VENTANA PARA GUARDAR CREDENCIALES)
# =============================================================================

class CredentialsDialog(QDialog):
    """
    Diálogo modal para solicitar y guardar las credenciales del usuario.
    """
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Configurar Credenciales de GitHub")
        self.setModal(True)
        
        self.layout = QFormLayout(self)
        
        self.info_label = QLabel("Por favor, ingrese sus datos de GitHub.\nSe requiere un Personal Access Token (PAT) con permisos 'repo'.")
        self.layout.addRow(self.info_label)

        self.user_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        
        self.layout.addRow("Usuario de GitHub:", self.user_edit)
        self.layout.addRow("Email (para commits):", self.email_edit)
        self.layout.addRow("Personal Access Token:", self.token_edit)
        
        self.button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Guardar")
        self.cancel_btn = QPushButton("Cancelar")
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.cancel_btn)
        self.button_layout.addWidget(self.save_btn)
        
        self.layout.addRow(self.button_layout)
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.setStyleSheet(DARK_STYLE)

    def accept(self):
        username = self.user_edit.text()
        email = self.email_edit.text()
        token = self.token_edit.text()
        
        if not username or not email or not token:
            QMessageBox.warning(self, "Campos incompletos", "Todos los campos son obligatorios.")
            return
            
        if self.settings_manager.save_credentials(username, email, token):
            QMessageBox.information(self, "Éxito", "Credenciales guardadas y encriptadas.")
            super().accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron guardar las credenciales.")

class AddFilesDialog(QDialog):
    """Diálogo para seleccionar archivos para 'git add'."""
    def __init__(self, files_status, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Archivos al Staging Area")
        self.setMinimumSize(600, 400)
        
        self.layout = QVBoxLayout(self)
        
        self.file_list = QListWidget()
        self.layout.addWidget(self.file_list)
        
        for status, file_path in files_status:
            item = QListWidgetItem(f"{status} - {file_path}")
            item.setData(Qt.UserRole, file_path) # Store the raw path
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.file_list.addItem(item)

        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Seleccionar Todos")
        deselect_all_btn = QPushButton("Deseleccionar Todos")
        self.add_btn = QPushButton("Añadir Seleccionados")
        
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.add_btn)
        
        self.layout.addLayout(button_layout)
        
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn.clicked.connect(self._deselect_all)
        self.add_btn.clicked.connect(self.accept)

    def _select_all(self):
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(Qt.Checked)

    def _deselect_all(self):
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(Qt.Unchecked)
            
    def get_selected_files(self):
        selected = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected

# =============================================================================
# 7. CLASE LOGGERUI (SISTEMA DE LOGS INTEGRADO) 
# (Definido antes de la UI principal para que esté disponible)
# =============================================================================

class LoggerUI:
    """
    Maneja la visualización de logs en la GUI y el guardado en archivo.
    """
    def __init__(self, text_widget, log_file_path):
        self.widget = text_widget
        self.file_path = log_file_path
        self.widget.setReadOnly(True)

    def log(self, msg, level="INFO"):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {msg}"
        
        # Escribir en archivo
        try:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except IOError as e:
            print(f"Error al escribir en log: {e}") # Log a consola si falla el de archivo

        # Mostrar en GUI con color
        color = "white"
        if level == "ERROR":
            color = "#ff6b6b" # Rojo
        elif level == "WARNING":
            color = "#f9d423" # Amarillo
        elif level == "INFO":
            color = "#f0f0f0" # Blanco
        elif level == "SUCCESS":
            color = "#69f0ae" # Verde
            
        html_entry = f'<span style="color: {color};">{log_entry}</span>'
        self.widget.append(html_entry)
        
        # Auto-scroll
        self.widget.moveCursor(QTextCursor.End)

# =============================================================================
# 6. CLASE GITHUBMANAGERUI (VENTANA PRINCIPAL)
# =============================================================================

class GitHubManagerWidget(QWidget):
    """
    Widget principal de la aplicación.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(DARK_STYLE)
        
        # --- Modelos de datos ---
        self.settings_manager = SettingsManager()
        self.github_api = None
        self.local_git = None
        self.credentials = None
        self.local_branches = []
        self.remote_branches = []

        # --- Inicializar UI y Logger ---
        self._init_logger()
        self._init_ui()
        self._connect_signals()
        
        # --- Cargar o solicitar credenciales ---
        self._load_or_request_credentials()

    def _init_logger(self):
        self.log_widget = QTextEdit()
        self.logger = LoggerUI(self.log_widget, LOG_FILE)
        self.logger.log("Aplicación iniciada.", "INFO")

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Pestaña 1: Operaciones ---
        operations_widget = QWidget()
        operations_layout = QVBoxLayout(operations_widget)
        self.tabs.addTab(operations_widget, "Operaciones")

        # 1. Selección de Proyecto
        project_layout = QHBoxLayout()
        project_label = QLabel("Proyecto:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Seleccione la carpeta de un repositorio Git...")
        self.path_edit.setReadOnly(True)
        self.browse_btn = QPushButton("Examinar")
        self.init_repo_btn = QPushButton("Iniciar Repo")
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.path_edit, 1)
        project_layout.addWidget(self.browse_btn)
        project_layout.addWidget(self.init_repo_btn)
        operations_layout.addLayout(project_layout)

        # 2. Repositorio y Ramas
        repo_layout = QHBoxLayout()
        repo_label = QLabel("Repo Remoto:")
        self.repo_combo = QComboBox()
        self.repo_combo.setToolTip("Repositorio remoto detectado/seleccionado.")
        branch_label = QLabel("Rama:")
        self.branch_combo = QComboBox()
        self.branch_combo.setToolTip("Seleccione, cambie o cree una rama.")
        self.refresh_branches_btn = QPushButton("Actualizar Ramas")
        self.prune_btn = QPushButton("Purgar Repo")
        self.new_branch_btn = QPushButton("Nueva Rama")
        repo_layout.addWidget(repo_label)
        repo_layout.addWidget(self.repo_combo, 2)
        repo_layout.addWidget(branch_label)
        repo_layout.addWidget(self.branch_combo, 2)
        repo_layout.addWidget(self.refresh_branches_btn)
        repo_layout.addWidget(self.prune_btn)
        repo_layout.addWidget(self.new_branch_btn)
        operations_layout.addLayout(repo_layout)

        # 3. Commit y Push
        commit_layout = QHBoxLayout()
        self.commit_msg_edit = QLineEdit()
        self.commit_msg_edit.setPlaceholderText("Mensaje de commit...")
        self.add_interactive_btn = QPushButton("Add Interactivo")
        self.commit_push_btn = QPushButton("Commit + Push")
        self.commit_push_btn.setObjectName("commit_push_btn")
        commit_layout.addWidget(self.commit_msg_edit, 1)
        commit_layout.addWidget(self.add_interactive_btn)
        commit_layout.addWidget(self.commit_push_btn)
        operations_layout.addLayout(commit_layout)

        # 4. Logs
        operations_layout.addWidget(QLabel("Registro de Operaciones:"))
        operations_layout.addWidget(self.log_widget, 1)

        # 5. Acciones Adicionales
        actions_layout = QHBoxLayout()
        self.open_repo_btn = QPushButton("Abrir en GitHub")
        self.force_fix_btn = QPushButton("Forzar Reparación")
        self.change_creds_btn = QPushButton("Cambiar Credenciales")
        actions_layout.addStretch()
        actions_layout.addWidget(self.open_repo_btn)
        actions_layout.addWidget(self.force_fix_btn)
        actions_layout.addWidget(self.change_creds_btn)
        operations_layout.addLayout(actions_layout)

        # --- Pestaña 2: Staging Area ---
        staging_widget = QWidget()
        staging_layout = QVBoxLayout(staging_widget)
        self.tabs.insertTab(1, staging_widget, "Staging Area")

        staging_actions_layout = QHBoxLayout()
        self.commit_staged_btn = QPushButton("Hacer Commit de lo Seleccionado")
        self.unstage_btn = QPushButton("Quitar de Staging")
        staging_actions_layout.addStretch()
        staging_actions_layout.addWidget(self.unstage_btn)
        staging_actions_layout.addWidget(self.commit_staged_btn)
        staging_layout.addLayout(staging_actions_layout)

        self.staging_tree = QTreeWidget()
        self.staging_tree.setHeaderLabels(["Archivo", "Ruta"])
        self.staging_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        staging_layout.addWidget(self.staging_tree)

        # --- Pestaña 3: Historial ---
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        self.tabs.addTab(history_widget, "Historial")

        history_controls_layout = QHBoxLayout()
        self.history_view_combo = QComboBox()
        self.refresh_history_btn = QPushButton("Refrescar Historial")
        self.push_unpushed_btn = QPushButton("Push")
        self.revert_commit_btn = QPushButton("Revertir Commit")
        self.checkout_commit_btn = QPushButton("Traer esta Versión")
        history_controls_layout.addWidget(QLabel("Vista:"))
        history_controls_layout.addWidget(self.history_view_combo, 1)
        history_controls_layout.addWidget(self.refresh_history_btn)
        history_controls_layout.addWidget(self.push_unpushed_btn)
        history_controls_layout.addWidget(self.revert_commit_btn)
        history_controls_layout.addWidget(self.checkout_commit_btn)
        history_layout.addLayout(history_controls_layout)

        self.push_unpushed_btn.hide()

        self.history_table = QTableView()
        self.history_table.setSelectionBehavior(QTableView.SelectRows)
        self.history_table.setEditTriggers(QTableView.NoEditTriggers)
        self.history_model = QStandardItemModel()
        self.history_model.setHorizontalHeaderLabels(["SHA", "Autor", "Fecha", "Mensaje"])
        self.history_table.setModel(self.history_model)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        history_layout.addWidget(self.history_table)

    def _connect_signals(self):
        # Pestaña Operaciones
        self.browse_btn.clicked.connect(self.select_project_folder)
        self.init_repo_btn.clicked.connect(self.handle_init_repo)
        self.refresh_branches_btn.clicked.connect(self.update_all_branches)
        self.prune_btn.clicked.connect(self.prune_repository)
        self.new_branch_btn.clicked.connect(self.create_new_branch)
        self.commit_push_btn.clicked.connect(self.commit_and_push)
        self.add_interactive_btn.clicked.connect(self.handle_interactive_add)
        self.change_creds_btn.clicked.connect(self._prompt_for_credentials)
        self.open_repo_btn.clicked.connect(self.open_repo_in_browser)
        self.force_fix_btn.clicked.connect(self.force_fix_repository)
        self.branch_combo.currentTextChanged.connect(self.change_local_branch)

        # Pestaña Staging Area
        self.commit_staged_btn.clicked.connect(self.handle_commit_staged)
        self.unstage_btn.clicked.connect(self.handle_unstage)

        # Pestaña Historial
        self.refresh_history_btn.clicked.connect(self._on_history_view_changed)
        self.history_view_combo.currentTextChanged.connect(self._on_history_view_changed)
        self.checkout_commit_btn.clicked.connect(self._handle_checkout_commit)
        self.revert_commit_btn.clicked.connect(self.handle_revert_commit)
        self.push_unpushed_btn.clicked.connect(self.handle_push_unpushed)

    # --- Lógica de Staging Area (NUEVO) ---
    def handle_interactive_add(self):
        if not self.local_git:
            QMessageBox.warning(self, "Error", "Seleccione un repositorio local primero.")
            return

        files_status = self.local_git.get_status()
        if not files_status:
            QMessageBox.information(self, "Información", "No hay cambios o archivos no rastreados para añadir.")
            return

        dialog = AddFilesDialog(files_status, self)
        if dialog.exec() == QDialog.Accepted:
            selected_files = dialog.get_selected_files()
            if selected_files:
                if self.local_git.add_files(selected_files):
                    self.refresh_staging_area()
            else:
                self.logger.log("No se seleccionó ningún archivo para añadir.", "INFO")

    def refresh_staging_area(self):
        if not self.local_git:
            self.staging_tree.clear()
            return

        self.staging_tree.clear()
        staged_files = self.local_git.get_staged_files()
        
        root_items = {}
        for file_path in staged_files:
            parts = Path(file_path).parts
            parent_item = self.staging_tree.invisibleRootItem()

            current_path_key = ""
            for i, part in enumerate(parts):
                # Construir una clave única para cada nodo en el árbol
                current_path_key = os.path.join(current_path_key, part)
                
                if i == len(parts) - 1:
                    file_item = QTreeWidgetItem([part, str(Path(file_path).parent)])
                    file_item.setData(0, Qt.UserRole, file_path) # Guardar ruta completa
                    parent_item.addChild(file_item)
                else:
                    if current_path_key not in root_items:
                        folder_item = QTreeWidgetItem([part, ""])
                        root_items[current_path_key] = folder_item
                        parent_item.addChild(folder_item)
                    parent_item = root_items[current_path_key]

        self.logger.log(f"{len(staged_files)} archivo(s) en el staging area.", "INFO")
        self.staging_tree.expandAll()

    def handle_commit_staged(self):
        if not self.local_git or not self.local_git.get_staged_files():
            QMessageBox.warning(self, "Error", "No hay archivos en el staging area para hacer commit.")
            return

        commit_msg, ok = QInputDialog.getText(self, "Mensaje de Commit", "Ingrese el mensaje para el commit:")
        if not (ok and commit_msg):
            self.logger.log("Commit cancelado por el usuario.", "INFO")
            return

        _, email, _ = self.credentials
        author = self.credentials[0]

        if self.local_git.commit_staged(commit_msg, author, email):
            self.logger.log("Commit de staged files exitoso.", "SUCCESS")
            self.refresh_staging_area()
            self._on_history_view_changed() # Refrescar vista de historial
        else:
            QMessageBox.critical(self, "Error", "Fallo al hacer commit. Revise los logs.")

    def handle_unstage(self):
        selected_items = self.staging_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Seleccione uno o más archivos para quitar del staging.")
            return

        files_to_unstage = []
        for item in selected_items:
            # Solo procesar items que son archivos (tienen data de UserRole)
            file_path = item.data(0, Qt.UserRole)
            if file_path:
                files_to_unstage.append(file_path)

        if not files_to_unstage:
            QMessageBox.warning(self, "Error", "Por favor, seleccione archivos, no carpetas.")
            return

        if self.local_git.unstage_files(files_to_unstage):
            self.logger.log("Archivos quitados del staging exitosamente.", "SUCCESS")
            self.refresh_staging_area()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron quitar los archivos del staging. Revise los logs.")


    # --- Lógica de Historial de Commits ---

    def _update_history_views(self):
        """Puebla el ComboBox de vistas de historial con las ramas disponibles."""
        self.history_view_combo.blockSignals(True)
        self.history_view_combo.clear()

        self.history_view_combo.addItem("Commits locales para Pushear", "unpushed")
        self.history_view_combo.addItem("--- Historial Local ---", None)
        for branch in self.local_branches:
            self.history_view_combo.addItem(f"Historial de: {branch}", f"local:{branch}")
        
        self.history_view_combo.addItem("--- Historial Remoto ---", None)
        for branch in self.remote_branches:
            self.history_view_combo.addItem(f"Historial de: origin/{branch}", f"remote:{branch}")
        
        self.history_view_combo.blockSignals(False)

    def _on_history_view_changed(self):
        """Se dispara cuando el usuario cambia la vista en el ComboBox de historial."""
        if not self.local_git:
            return

        view_key = self.history_view_combo.currentData()
        if not view_key:
            self._populate_history_table([])
            self.push_unpushed_btn.hide()
            return

        self.logger.log(f"Cargando vista de historial: {view_key}", "INFO")
        commits = []
        if view_key == "unpushed":
            commits = self.local_git.get_unpushed_commits()
            self.push_unpushed_btn.setVisible(bool(commits)) # Mostrar solo si hay commits
        else:
            self.push_unpushed_btn.hide()
            if view_key.startswith("local:"):
                branch = view_key.split(":")[1]
                commits = self.local_git.get_commits(branch)
            elif view_key.startswith("remote:"):
                branch = view_key.split(":")[1]
                commits = self.local_git.get_commits(f'origin/{branch}')

        if commits is None:
            self.logger.log("No se pudo cargar el historial de commits.", "ERROR")
            self._populate_history_table([])
        else:
            self._populate_history_table(commits)

    def _populate_history_table(self, commits):
        """Llena la tabla de historial con una lista de datos de commits."""
        self.history_model.removeRows(0, self.history_model.rowCount())
        for commit in commits:
            row = [
                QStandardItem(commit["sha"]),
                QStandardItem(commit["author"]),
                QStandardItem(commit["date"]),
                QStandardItem(commit["message"])
            ]
            self.history_model.appendRow(row)
        self.logger.log(f"{len(commits)} commits cargados en la tabla.", "INFO")

    def _handle_checkout_commit(self):
        """Crea una nueva rama desde el commit seleccionado en la tabla de historial."""
        selected_indexes = self.history_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un commit de la tabla.")
            return

        selected_row = selected_indexes[0].row()
        sha_item = self.history_model.item(selected_row, 0)
        sha = sha_item.text()

        reply = QMessageBox.question(self, "Confirmar Checkout",
                                     f"Esto creará una nueva rama llamada 'commit-{sha}' desde el commit seleccionado.\n¿Desea continuar?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.local_git.checkout_commit(sha):
                self.logger.log("Actualizando la UI después del checkout...", "INFO")
                self.update_all_branches()
                self.tabs.setCurrentIndex(0)
            else:
                QMessageBox.critical(self, "Error", "No se pudo hacer checkout del commit. Revise los logs.")

    def handle_revert_commit(self):
        """Revierte el commit seleccionado en la tabla de historial."""
        selected_indexes = self.history_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un commit de la tabla para revertir.")
            return

        selected_row = selected_indexes[0].row()
        sha_item = self.history_model.item(selected_row, 0)
        sha = sha_item.text()

        reply = QMessageBox.question(self, "Confirmar Revert",
                                     f"Esto creará un nuevo commit que deshace los cambios del commit {sha}. Esta es una operación segura.\n¿Desea continuar?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            _, email, _ = self.credentials
            author = self.credentials[0]
            if self.local_git.revert_commit(sha, author, email):
                self.logger.log("Revert exitoso. Actualizando historial...", "SUCCESS")
                self._on_history_view_changed()
            else:
                QMessageBox.critical(self, "Error", "No se pudo revertir el commit. Revise los logs.")

    def handle_push_unpushed(self):
        """Hace push de la rama actual."""
        self.logger.log("Iniciando Push de la rama actual...", "INFO")
        if self.local_git.push_current():
            self.logger.log("Push completado.", "SUCCESS")
            self._on_history_view_changed() # Refrescar para que la lista de unpushed se vacíe
        else:
            self.logger.log("Fallo el Push. Verifique los logs.", "ERROR")
            QMessageBox.critical(self, "Error", "Fallo el Push. Verifique los logs y sus credenciales.")

    # --- Lógica de Credenciales y API ---

    # ... (el resto de los métodos de la clase van aquí, sin cambios) ...
    def _load_or_request_credentials(self):
        self.credentials = self.settings_manager.load_credentials()
        if not self.credentials:
            self.logger.log("No se encontraron credenciales. Solicitando...", "INFO")
            self._prompt_for_credentials(force_prompt=True)
        else:
            self.logger.log("Credenciales cargadas exitosamente.", "INFO")
            self._initialize_apis()
            
        if not self.credentials:
            self.logger.log("No se proporcionaron credenciales. La funcionalidad remota está deshabilitada.", "WARNING")
            self._set_ui_enabled(False)
        else:
            # self._update_status_bar()
            self._load_remote_repos()

    def _prompt_for_credentials(self, force_prompt=False):
        if not force_prompt:
            reply = QMessageBox.question(self, "Confirmar", 
                                         "Esto borrará sus credenciales guardadas. ¿Desea continuar?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        self.settings_manager.clear_credentials()
        dialog = CredentialsDialog(self.settings_manager, self)
        
        if dialog.exec() == QDialog.Accepted:
            self.credentials = self.settings_manager.load_credentials()
            if self.credentials:
                self.logger.log("Nuevas credenciales guardadas.", "INFO")
                self._initialize_apis()
                # self._update_status_bar()
                self._load_remote_repos()
                self._set_ui_enabled(True)
        else:
            self.logger.log("Ingreso de credenciales cancelado.", "INFO")

    def _initialize_apis(self):
        if self.credentials:
            user, _, token = self.credentials
            self.github_api = GitHubAPI(user, token, self.logger)
            self.logger.log("API de GitHub inicializada.", "INFO")
        else:
            self.logger.log("No se pueden inicializar las APIs sin credenciales.", "ERROR")

    def _load_remote_repos(self):
        if not self.github_api:
            return
        
        self.logger.log("Cargando repositorios remotos...", "INFO")
        QApplication.processEvents() # Evitar que la UI se congele
        
        repos = self.github_api.list_repos()
        self.repo_combo.clear()
        if repos:
            self.repo_combo.addItems(repos)
            self.logger.log(f"{len(repos)} repositorios cargados.", "INFO")
        else:
            self.logger.log("No se pudieron cargar los repositorios.", "WARNING")

    def _set_ui_enabled(self, enabled):
        self.browse_btn.setEnabled(enabled)
        self.repo_combo.setEnabled(enabled)
        self.branch_combo.setEnabled(enabled)
        self.refresh_branches_btn.setEnabled(enabled)
        self.new_branch_btn.setEnabled(enabled)
        self.commit_msg_edit.setEnabled(enabled)
        self.commit_push_btn.setEnabled(enabled)
        self.open_repo_btn.setEnabled(enabled)

    def select_project_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta del Proyecto")
        if path:
            self.load_project(path)

    def load_project(self, path):
        """Carga y valida un repositorio Git desde una ruta específica."""
        self.path_edit.setText(path)
        self.local_git = LocalGit(path, self.logger)
        
        if not self.local_git.is_valid_repo():
            QMessageBox.warning(self, "Error", "La carpeta seleccionada no es un repositorio Git válido.")
            self.local_git = None
            return

        if self.credentials:
            user, _, token = self.credentials
            self.local_git.update_remote_url_with_token(user, token)
        
        self.auto_select_remote_repo()
        self.update_all_branches()
        self.refresh_staging_area() # Cargar staging area al cargar proyecto
        # self._update_status_bar()

    def auto_select_remote_repo(self):
        if not self.local_git:
            return
        
        url = self.local_git.get_remote_url()
        if not url:
            self.logger.log("El repositorio local no tiene un remoto 'origin' configurado.", "WARNING")
            return
        
        repo_name = None
        if "https:" in url:
            repo_name = "/".join(url.split('/')[-2:]).replace(".git", "")
        elif "git@" in url:
            repo_name = url.split(':')[-1].replace(".git", "")
        
        if repo_name:
            for i in range(self.repo_combo.count()):
                if self.repo_combo.itemText(i) == repo_name:
                    self.repo_combo.setCurrentIndex(i)
                    self.logger.log(f"Repositorio remoto detectado: {repo_name}", "INFO")
                    return
        
        self.logger.log(f"No se pudo autodetectar el repo remoto '{repo_name}' en su lista.", "WARNING")

    def update_all_branches(self):
        if not self.local_git or not self.github_api:
            self.logger.log("Debe seleccionar un proyecto y tener credenciales.", "WARNING")
            return
            
        self.logger.log("Actualizando listas de ramas...", "INFO")
        QApplication.processEvents()

        self.local_branches = self.local_git.get_local_branches()
        remote_branches_result = self.local_git.get_remote_branches()
        
        if remote_branches_result is None:
            self.logger.log("No se pudieron actualizar las ramas remotas. Verifique el log de errores.", "WARNING")
            all_branches = sorted(self.local_branches)
        else:
            self.remote_branches = remote_branches_result
            all_branches = sorted(list(set(self.local_branches + self.remote_branches)))
            self.logger.log("Listas de ramas actualizadas.", "SUCCESS")

        self.branch_combo.blockSignals(True)
        self.branch_combo.clear()
        self.branch_combo.addItems(all_branches)
        
        current_local = self.local_git.get_current_branch()
        self.branch_combo.setCurrentText(current_local)
        self.branch_combo.blockSignals(False)
        
        self.logger.log(f"Local branches después de actualizar: {self.local_branches}", "DEBUG")
        self.logger.log(f"Remote branches después de actualizar: {self.remote_branches}", "DEBUG")

        self._update_history_views() # Actualizar vistas de historial
        # self._update_status_bar()

    def change_local_branch(self, branch_name):
        if not branch_name or not self.local_git:
            return
            
        self.logger.log(f"change_local_branch: Solicitando rama '{branch_name}'.", "DEBUG")
        self.logger.log(f"change_local_branch: self.local_branches = {self.local_branches}", "DEBUG")
        self.logger.log(f"change_local_branch: self.remote_branches = {self.remote_branches}", "DEBUG")

        if self.local_git.get_current_branch() == branch_name:
            return

        self.logger.log(f"Intentando cambiar a la rama '{branch_name}'...", "INFO")

        if branch_name in self.local_branches:
            self.local_git.checkout_branch(branch_name)
        elif branch_name in self.remote_branches:
            self.local_git.create_and_checkout_branch(branch_name, from_remote=True)
            self.local_branches = self.local_git.get_local_branches()
        else:
            self.logger.log(f"La rama '{branch_name}' no se reconoce como local ni remota.", "ERROR")

        # self._update_status_bar()

    def create_new_branch(self):
        if not self.local_git or not self.github_api:
            QMessageBox.warning(self, "Error", "Seleccione un repositorio local primero.")
            return

        new_branch_name, ok = QInputDialog.getText(self, "Crear Nueva Rama", 
                                                 "Nombre de la nueva rama:")
        
        if ok and new_branch_name:
            # --- VALIDACIÓN: No permitir espacios en nombres de ramas ---
            if ' ' in new_branch_name:
                QMessageBox.warning(self, "Nombre de Rama Inválido",
                                    "Los nombres de rama no pueden contener espacios. "
                                    "Use guiones (-) o guiones bajos (_) en su lugar.")
                self.logger.log(f"Intento de crear rama con nombre inválido: '{new_branch_name}'", "ERROR")
                return

            repo_full_name = self.repo_combo.currentText()
            base_branch = self.local_git.get_current_branch()
            
            self.logger.log(f"Creando nueva rama '{new_branch_name}' desde '{base_branch}'...", "INFO")
            
            if not self.local_git.create_and_checkout_branch(new_branch_name, base=base_branch):
                self.logger.log("Fallo al crear la rama local.", "ERROR")
                return
            
            if not self.github_api.create_branch(repo_full_name, base_branch, new_branch_name):
                self.logger.log("Fallo al crear la rama remota (puede continuar localmente).", "WARNING")
            
            self.update_all_branches()
            self.branch_combo.setCurrentText(new_branch_name)
            self.logger.log(f"Cambiado a la nueva rama '{new_branch_name}'.", "SUCCESS")
            
            self.logger.log("Realizando push inicial para enlazar la nueva rama...", "INFO")
            self.local_git.push_current()

    def commit_and_push(self):
        if not self.local_git:
            QMessageBox.warning(self, "Error", "Seleccione un repositorio local primero.")
            return
            
        commit_msg = self.commit_msg_edit.text()
        if not commit_msg:
            QMessageBox.warning(self, "Error", "El mensaje de commit no puede estar vacío.")
            return
            
        self.logger.log("Iniciando Commit y Push...", "INFO")
        QApplication.processEvents()

        _, email, _ = self.credentials
        author = self.credentials[0]
        
        if not self.local_git.commit_all(commit_msg, author, email):
            self.logger.log("Intentando Push de cambios existentes...", "INFO")
        
        if self.local_git.push_current():
            self.logger.log("Commit y Push completados.", "SUCCESS")
            self.commit_msg_edit.clear()
        else:
            self.logger.log("Fallo el Push. Verifique los logs.", "ERROR")

    def open_repo_in_browser(self):
        repo_name = self.repo_combo.currentText()
        if not repo_name:
            QMessageBox.warning(self, "Error", "No hay un repositorio remoto seleccionado.")
            return
        
        url = QUrl(f"https://github.com/{repo_name}")
        QDesktopServices.openUrl(url)
        self.logger.log(f"Abriendo {url.toString()} en el navegador.", "INFO")

    def force_fix_repository(self):
        if not self.local_git:
            QMessageBox.warning(self, "Error", "Seleccione un repositorio local primero.")
            return

        repo_path = self.path_edit.text()
        corrupt_ref_name = "rama 2"
        corrupt_ref_path = Path(repo_path) / ".git" / "refs" / "heads" / corrupt_ref_name

        reply = QMessageBox.question(self, "Confirmar Reparación Forzada",
                                     f"Se ha detectado una referencia de rama corrupta ('{corrupt_ref_name}').\n\n"
                                     f"Esto intentará repararlo eliminando el archivo de referencia:\n"
                                     f"{corrupt_ref_path}\n\n"
                                     "Esta acción es generalmente segura para referencias corruptas, pero es irreversible. ¿Desea continuar?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            self.logger.log("Reparación forzada cancelada por el usuario.", "INFO")
            return

        if not corrupt_ref_path.exists():
            self.logger.log(f"El archivo de referencia corrupto no fue encontrado en la ruta esperada. No se necesita hacer nada.", "WARNING")
            QMessageBox.information(self, "No encontrado", "El archivo de referencia corrupto no fue encontrado. Puede que ya haya sido eliminado.")
            return

        try:
            os.remove(corrupt_ref_path)
            self.logger.log(f"Archivo de referencia corrupto eliminado: {corrupt_ref_path}", "SUCCESS")
            self.logger.log("Intente 'Actualizar Ramas' o 'Purgar Repo' de nuevo.", "INFO")
            QMessageBox.information(self, "Éxito", "Se ha eliminado la referencia corrupta. Por favor, intente la operación anterior de nuevo.")
            # Actualizar la UI para remover la rama eliminada
            self.update_all_branches()
        except Exception as e:
            self.logger.log(f"No se pudo eliminar el archivo de referencia corrupto: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el archivo: {e}")

    def prune_repository(self):
        if not self.local_git:
            QMessageBox.warning(self, "Error", "Seleccione un repositorio local primero.")
            return
        
        self.logger.log("Ejecutando purga del repositorio (git gc --prune=now)...", "INFO")
        QApplication.processEvents()
        
        if self.local_git.prune_repo():
            self.logger.log("Purga completada. Intente actualizar las ramas de nuevo.", "SUCCESS")
        else:
            self.logger.log("Fallo durante la purga del repositorio.", "ERROR")

    # --- Helpers ---

    def handle_init_repo(self):
        """Maneja la creación de un nuevo repositorio Git."""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta para Nuevo Repositorio")
        if not path:
            return

        # Verificar si ya es un repo
        if (Path(path) / '.git').exists():
            QMessageBox.information(self, "Información", "La carpeta seleccionada ya es un repositorio Git.")
            self.load_project(path) # Cargarlo de todos modos
            return

        # Verificar si el directorio no está vacío
        if len(os.listdir(path)) > 0:
            reply = QMessageBox.question(self, "Confirmar",
                                         "El directorio no está vacío. ¿Está seguro de que desea inicializar un repositorio aquí?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.logger.log("Inicialización cancelada por el usuario (directorio no vacío).", "INFO")
                return

        # Inicializar el repo
        if LocalGit.initialize_repository(path, self.logger):
            self.load_project(path)
        else:
            QMessageBox.critical(self, "Error", "No se pudo inicializar el repositorio. Revise los logs.")

# --- Ventana para modo Standalone ---
class GitHubManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Manager 1.0")
        self.setGeometry(100, 100, 800, 600)
        
        self.widget = GitHubManagerWidget(self)
        self.setCentralWidget(self.widget)
        
        # Recrear la barra de estado aquí
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.widget.status_user = QLabel("Usuario: N/A")
        self.widget.status_repo = QLabel("Repo: N/A")
        self.widget.status_branch = QLabel("Rama: N/A")
        self.status_bar.addPermanentWidget(self.widget.status_user, 1)
        self.status_bar.addPermanentWidget(self.widget.status_repo, 2)
        self.status_bar.addPermanentWidget(self.widget.status_branch, 1)
        
        # Sobrescribir el método del widget para que actualice la barra de estado de la ventana
        self.widget._update_status_bar = self._update_main_window_status_bar

    def _update_main_window_status_bar(self):
        if self.widget.credentials:
            self.widget.status_user.setText(f"Usuario: {self.widget.credentials[0]}")
        
        if self.widget.local_git and self.widget.local_git.is_valid_repo():
            self.widget.status_repo.setText(f"Repo: {self.widget.repo_combo.currentText()}")
            self.widget.status_branch.setText(f"Rama: {self.widget.local_git.get_current_branch()}")
        else:
            self.widget.status_repo.setText("Repo: N/A")
            self.widget.status_branch.setText("Rama: N/A")


# =============================================================================
# 8. BLOQUE MAIN (EJECUCIÓN DEL PROGRAMA)
# =============================================================================

if __name__ == "__main__":
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    window = GitHubManagerWindow()
    window.show()
    sys.exit(app.exec())
