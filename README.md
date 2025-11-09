# 🧩 CLICommandStudio

### *Visual Command Manager for Developers*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![UI-PySide6](https://img.shields.io/badge/UI-PySide6-darkblue) ![Status](https://img.shields.io/badge/status-active-success)

**CLICommandStudio** es una herramienta de escritorio que permite **crear, editar y ejecutar comandos de línea** desde una interfaz visual moderna.
En lugar de programar un CLI desde cero, simplemente definís tus comandos y variables en **archivos JSON**, y la aplicación genera automáticamente un entorno visual para gestionarlos.

---

## 🎯 ¿Qué es y para qué sirve?

CLICommandStudio es un **entorno visual para comandos de consola**.
Te permite definir tus propias herramientas, scripts o flujos de trabajo sin necesidad de crear un CLI con `argparse`, `click` o Bash.

Su objetivo es **simplificar la automatización y organización de tareas de desarrollo**, DevOps o administración de sistemas.
Ideal para quienes manejan contenedores Docker, despliegues, repositorios o pipelines desde terminal, pero prefieren una interfaz más ordenada y reutilizable.

---

## 🧠 Principales características

* 🎛️ **Gestor visual de comandos**
  Agrupá tus comandos por categorías y ejecutalos con un clic.
  Cada comando se define en un `commands.json`.

* 🧮 **Variables globales reutilizables**
  Las variables se guardan en `variables.json` y se integran en los comandos mediante placeholders (`[VARIABLE]`).

* 🧰 **Editor integrado**
  Agregá, modificá o eliminá comandos y categorías directamente desde la interfaz, sin tocar el JSON.

* 🖥️ **Monitor en vivo**
  Ejecutá comandos como `docker ps` o `kubectl get pods` de forma continua para ver estados actualizados.

* 🧾 **Vista previa del comando final**
  El sistema reemplaza automáticamente las variables y muestra el comando que se va a ejecutar.

* 🎨 **Interfaz moderna**
  Basada en **PySide6 / Qt6**, con tema oscuro y diseño tipo “dock studio”.

---

## ⚙️ Ejemplo rápido

**commands.json**

```json
{
  "Contenedores": {
    "Ver activos": { 
      "template": "docker ps", 
      "info": "Lista contenedores en ejecución." 
    },
    "Detener contenedor": { 
      "template": "docker stop [CONTENEDOR_ID]", 
      "info": "Detiene un contenedor por ID o nombre." 
    }
  }
}
```

**variables.json**

```json
{
  "CONTENEDOR_ID": {
    "descripcion": "ID o nombre del contenedor",
    "valores": ["web_1", "db_postgres"],
    "default": "web_1"
  }
}
```

Abrís la app, seleccionás el comando, completás las variables y lo ejecutás directamente.

---

## 🔍 Diferencias clave frente a otros enfoques

| Método                                                           | Desventaja tradicional                              | Cómo lo soluciona CLICommandStudio                      |
| ---------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------- |
| **Scripts o CLIs en Bash / Python**                              | Tenés que escribir lógica de argumentos, help, etc. | Todo se define en JSON y se interpreta automáticamente. |
| **Herramientas gráficas específicas (Docker Desktop, Git GUIs)** | Limitadas a un solo tipo de herramienta.            | Es universal: cualquier comando CLI puede agregarse.    |
| **Automatización web o low-code**                                | Dependen de conectividad o frameworks externos.     | Es completamente local, multiplataforma y portable.     |

---

## 🚀 Casos de uso

* Administrar contenedores Docker o servicios locales.
* Centralizar tus comandos frecuentes en una interfaz.
* Documentar flujos DevOps con ejemplos ejecutables.
* Crear un panel de operaciones para tu equipo sin programar un CLI.
* Probar y componer comandos complejos antes de automatizarlos.

---

## 💡 Uso combinado con IA (opcional)

Aunque CLICommandStudio **no depende de IA**, podés potenciarlo con ella:
Pedile a una IA (como ChatGPT, Claude u otras) que te genere los archivos `commands.json` y `variables.json` con los comandos que necesites.

Ejemplo:

> “Generame un commands.json con 5 comandos Docker y un variables.json con las variables necesarias.”

Solo copiás esos archivos a la carpeta del proyecto, y CLICommandStudio los interpretará automáticamente como un nuevo entorno CLI visual.

Esto permite crear **interfaces completas a partir de descripciones generadas por IA**, sin integrar la IA dentro de la app.

---

## 🧱 Arquitectura general

```
┌───────────────────────┐
│ commands.json         │──▶ Define categorías y comandos
├───────────────────────┤
│ variables.json        │──▶ Define variables y valores globales
└───────────────────────┘
          │
          ▼
┌────────────────────────────┐
│ CLICommandStudio (PySide6) │
│ - Renderiza UI             │
│ - Reemplaza variables      │
│ - Ejecuta comandos (QProcess) │
└────────────────────────────┘
          │
          ▼
   💻 Ejecución visual y monitoreo
```

---

## ⚡ Instalación y uso

```bash
git clone https://github.com/tuusuario/clicommandstudio.git
cd clicommandstudio
pip install -r requirements.txt
python clicommandstudio.py
```

La primera ejecución creará `commands.json` y `variables.json` con ejemplos por defecto.

---

## 🧰 Tecnologías

* **Python 3.10+**
* **PySide6 / Qt6**
* **JSON** como formato declarativo
* **QProcess** para ejecución en vivo

---

## 🗺️ Roadmap futuro

* [ ] Validación por esquema JSON
* [ ] Exportación / importación de entornos
* [ ] Modo remoto (SSH / Docker SDK)
* [ ] Integración opcional con modelos de IA (para generación automática)
* [ ] Nuevos temas visuales (claro / oscuro)

---

## 💬 Contribuciones

Las PRs son bienvenidas.
Podés colaborar con:

* Nuevos ejemplos JSON
* Mejoras de UX o diseño
* Funcionalidades adicionales (logs, perfiles, etc.)

---

## 📜 Licencia

MIT © [developer-cmd-Ari]

---

