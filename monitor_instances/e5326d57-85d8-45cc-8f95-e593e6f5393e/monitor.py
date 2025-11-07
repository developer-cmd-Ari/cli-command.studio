
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
    """Carga las reglas de monitoreo desde el archivo de configuración."""
    global monitoreo_rutas
    monitoreo_rutas = {}
    
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Error: Archivo de configuración '{CONFIG_FILE}' no encontrado.")
        print("Creando archivo de ejemplo...")
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(r"# Formato: archivo.py | C:\ruta\origen | C:\ruta\destino | C:\ruta\backup\n")
                f.write(r"ejemplo.txt | . | .\destino | .\backup\n")
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
                        print(f"⚠️ Advertencia: Carpeta de origen no encontrada: {ruta_origen}")
                        continue
                        
                    # Creamos carpetas de destino y backup si no existen
                    ruta_destino.mkdir(parents=True, exist_ok=True)
                    ruta_backup.mkdir(parents=True, exist_ok=True)
                    
                    archivo_completo = ruta_origen / archivo_nombre
                    
                    if not archivo_completo.exists():
                        print(f"⚠️ Advertencia: Archivo de origen no encontrado: {archivo_completo}")
                        continue

                    monitoreo_rutas[str(archivo_completo)] = (archivo_nombre, ruta_destino, ruta_backup)
                    print(f"✅ Regla cargada: {archivo_nombre} -> Destino: {ruta_destino.name} | Backup: {ruta_backup.name}")
                    
                except ValueError:
                    print(f"❌ Error de formato en la línea: '{line}'. Formato esperado: archivo.py | origen | destino | backup")
                    
    except Exception as e:
        print(f"Error inesperado al leer {CONFIG_FILE}: {e}")
        return False
        
    return True # Carga exitosa

def realizar_backup_inicial():
    """Copia el archivo de origen a la carpeta de backup al inicio."""
    print("\n--- 💾 Iniciando Copia de Seguridad Inicial (Backup) ---")
    
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
    """Manejador de eventos que copia el archivo si detecta una modificación."""

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
            print(f"\n⚙️ Cambio detectado en: {archivo_nombre}")
            
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

    print(f"\nObservando {len(carpetas_a_observar)} carpetas:")
    for carpeta in carpetas_a_observar:
        print(f"  - {carpeta}")
        observer.schedule(event_handler, carpeta, recursive=True)

    print("\n--- 🤖 Iniciando monitoreo... Presiona CTRL+C para detener. ---")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()
    print("--- Monitoreo detenido. ---")
