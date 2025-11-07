import subprocess
import os
import time

def run_commands_from_file(filepath='comandos.txt'):
    """
    Lee un archivo de texto y ejecuta cada línea en una nueva ventana de CMD.
    Cada línea en el archivo de texto debe contener una cadena de comandos completa
    unida por '&&'.

    Args:
        filepath (str): La ruta al archivo que contiene los comandos.
    """
    print("Iniciando el lanzador de procesos...")
    
    # Verifica si el archivo de comandos existe.
    if not os.path.exists(filepath):
        print(f"Error: No se encontró el archivo '{filepath}'.")
        print("Por favor, asegúrate de que el archivo exista en el mismo directorio que este script.")
        # Crea un archivo de ejemplo si no existe.
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Ejemplo de comando: cambia de directorio, activa el venv y ejecuta un script\n")
            f.write("cd /d C:\\ruta\\a\\tu\\proyecto && .\\venv\\Scripts\\activate && python tu_script.py\n")
        print(f"Se ha creado un archivo '{filepath}' de ejemplo.")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            commands = f.readlines()

        if not commands:
            print(f"El archivo '{filepath}' está vacío. No hay comandos para ejecutar.")
            return

        print(f"Se encontraron {len(commands)} comandos para ejecutar.")

        for i, command in enumerate(commands):
            # Ignorar líneas vacías o comentadas con #
            if command.strip() and not command.strip().startswith('#'):
                # Construye el comando final para ser ejecutado por 'start cmd /k'
                # 'start' abre una nueva ventana.
                # 'cmd /k' ejecuta el comando y mantiene la ventana abierta.
                full_command = f'start "Proceso {i+1}" cmd /k "{command.strip()}"'
                
                print(f"Ejecutando en una nueva ventana: {command.strip()}")
                
                # Usamos subprocess.run para ejecutar el comando.
                # shell=True es necesario para que 'start' y '&&' sean interpretados por el shell de Windows.
                subprocess.run(full_command, shell=True, check=True)
                
                # Pequeña pausa entre lanzamientos para no saturar el sistema
                time.sleep(1)

        print("\nTodos los procesos han sido lanzados en sus respectivas ventanas.")

    except FileNotFoundError:
        print(f"Error: El archivo '{filepath}' no fue encontrado.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    # El nombre del archivo de comandos está definido aquí.
    # Puedes cambiarlo si lo deseas.
    commands_file = 'comandos.txt'
    run_commands_from_file(commands_file)
    # Se ha eliminado la línea input() para evitar errores con pyinstaller.
    # La ventana del lanzador se cerrará automáticamente al terminar.
    print("\nCerrando lanzador en 3 segundos...")
    time.sleep(3)

