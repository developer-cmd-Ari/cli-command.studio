# Copilot / AI agent instructions for this repository

This file is a concise guide to help an AI coding agent be productive in this codebase.
Keep answers brief and actionable; follow examples below when modifying code.

## Quick summary
- Desktop PySide6 admin app that manages "instances", runs commands and integrates with Docker and GitHub registries.
- Key UIs: `app.py` (main hub), `comand_manager_v2.py` (Command Manager GUI), `docker_manager.py` (Docker SDK wrapper + secure config), `monitor_manager.py` (file monitor and helper script).
- Persistent data: `commands.json`, `variables.json`, `monitor_config.json` in repo root. Encrypted credentials live in `config/credentials.enc` with key `config/app.key` (managed by `ConfigManager` in `docker_manager.py`).

## How to run (developer flows)
- Launch the Command Manager GUI: `python comand_manager_v2.py` (works on Windows; example: `& C:/Python313/python.exe c:/path/to/comand_manager_v2.py`).
- Launch the main Hub UI: `python app.py`.
- Launcher that opens multiple CMD windows: `python launcher.py` (reads `comandos.txt`).
- Build with PyInstaller: project includes `app.spec` and `launcher.spec`; use `pyinstaller app.spec` to produce an executable.

## Important files and roles (single-line)
- `app.py` — main graphical hub and theme assets.
- `comand_manager_v2.py` — command editor/executor, loads `commands.json` and `variables.json`, uses `QProcess` for execution and `QProcess` for monitor output.
- `docker_manager.py` — Docker abstraction (`DockerService`) and `ConfigManager` (encrypt/decrypt credentials using `cryptography.Fernet`).
- `monitor_manager.py` — file-watch monitor and `MONITOR_SCRIPT_CONTENT` (template `monitor.py` used by instances).
- `file_manager.py` / `app_manager.py` — file and instance management widgets and UI helpers.
- `commands.json` / `variables.json` — user-editable command templates and substitution values. Templates use `[VAR_NAME]` placeholders.

## Patterns & conventions to follow
- UI code uses PySide6 and QSS constants for styling; prefer reusing existing style constants (e.g., `DARK_THEME_QSS`, `TURQUOISE_STYLESHEET`).
- Data files are read/written with `load_data()` / `save_data()` in `comand_manager_v2.py`: always call those helpers to persist changes.
- Command templates use square-bracket variables: e.g. `docker tag [IMAGEN_LOCAL] ghcr.io/[TU_USUARIO]/[IMAGEN_REPO]`. Replace by exact string match.
- Credentials are stored encrypted: never write plaintext credentials to repo. Use `ConfigManager.save_credentials()` and `load_credentials()` in `docker_manager.py`.
- Language: strings & comments are primarily Spanish — keep messages and new UI text consistent with Spanish wording.

## Integration points & external deps
- Docker: uses `docker` Python SDK. Wrap interactions through `DockerService` (check `login_to_registry`, `get_push_stream`, `list_containers`).
- GitHub Container Registry: push/pull flows go through `docker_manager.DockerService` and `commands.json` templates (GHCR templates exist).
- Encryption: `cryptography.fernet` is required and used by `ConfigManager`.
- File monitoring helper uses `watchdog` (see `MONITOR_SCRIPT_CONTENT` in `monitor_manager.py`).

## Examples to follow when editing
- Add a command template to `commands.json` with structure: `"Category": { "Command Name": { "template": "...", "info": "..." } }`.
- Use `variables.json` entries to provide possible values and defaults. `comand_manager_v2.py` calls `load_data()` then `save_data()` to persist.
- For Docker pushes, prefer using `DockerService.get_push_stream()` (it returns a generator of JSON chunks) instead of shelling out.

## Build / debug tips
- If UI imports fail, run the failing module directly to see ImportError messages (e.g., `python docker_manager.py`).
- To reproduce Docker issues, run the relevant method in a small script that imports `DockerService` and prints `check_connection()` output.
- Use the provided `.spec` files with PyInstaller rather than reauthoring them.

## Safe-guards and do-not-modify points
- Do not modify `config/app.key` or `config/credentials.enc` directly. Use `ConfigManager` to rotate or regenerate keys.
- Keep the `[VAR_NAME]` placeholder format intact when editing command templates.

## Where to look for more context
- UI styling/theme: search for `TURQUOISE_STYLESHEET`, `DARK_THEME_QSS` or `PINK_STYLESHEET` to find where styles are applied.
- Commands and variables: `commands.json`, `variables.json`, and `comandos.txt` (launcher samples).
- Build artifacts: `build/` contains previous pyinstaller outputs for reference.

If any section is unclear or you'd like me to include runnable snippets (e.g., a small test for `DockerService.check_connection()`), tell me which area to expand and I'll iterate.
