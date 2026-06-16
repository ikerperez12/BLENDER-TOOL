# IP Blender Tool

> **Render Queue & Automation for Blender on Windows**

IP Blender Tool is a lightweight, professional rendering assistant designed to orchestrate, queue, and automate rendering tasks in Blender. It wraps a polished High-DPI dark desktop user interface (PySide6) around a robust, error-tolerant command-line execution engine.

---

## 🚀 Key Features

* **Ingestion Scanning**: Inspects `.blend` files automatically to extract scenes, cameras, frame ranges, and warns about **missing textures** before queueing jobs.
* **Persistent Render Queue**: Stack multiple render jobs (stills or animations) and run them sequentially.
* **Non-Blocking Operation**: The UI remains fluid and fully responsive during long rendering cycles.
* **Auto-Versioning & Folders**: Never overwrite files; output filenames increment automatically (`_v001`, `_v002`) and organize results into subfolders categorised by camera name.
* **Auto-Montage (FFmpeg/Compositor)**:
  - Swaps freshly rendered stills into compositing nodes for final montage outputs.
  - Compiles animation frame folders into clean H.264 MP4 videos using exact Blender frame rate ratios.
* **Asynchronous Outbox**: Dispatches Telegram or Discord status alerts with preview thumbnails without pausing or blocking the render queue.
* **Process Abort (psutil)**: Aborting jobs safely cleans up parent and all child Blender execution threads.
* **Automatic Power Management**: Apagar (Shutdown) or Suspender (Sleep) the PC upon queue completion.

---

## 📥 Installation (User)

**No se requiere Python. No se requiere línea de comandos.**

1. Ve a la página de [**Releases**](../../releases) de este repositorio.
2. Descarga el instalador: `IP-Blender-Tool-Setup-x.x.x.exe`.
3. Ejecuta el instalador — se instala en tu perfil de usuario (`%LOCALAPPDATA%\Programs\IP Blender Tool\`). **No requiere permisos de administrador.**
4. Abre el programa desde el acceso directo en el Escritorio o Menú de Inicio.
5. Completa el **Asistente de Configuración Inicial** (First-Run Wizard): configura la ruta de `blender.exe`, `ffmpeg.exe` y tus carpetas de proyectos.

### Verificación de integridad

Cada release incluye un archivo `.sha256`. Para verificar la descarga:

```powershell
certutil -hashfile IP-Blender-Tool-Setup-1.0.0-rc2.exe SHA256
```

Compara el hash con el contenido de `IP-Blender-Tool-Setup-1.0.0-rc2.exe.sha256`.

---

## 🛠️ Desarrollo (Desarrolladores)

### Requisitos

* **Python**: 3.10 o superior.
* **Blender**: 4.2 LTS o 5.1 (instalado en Program Files, o ruta personalizable).
* **FFmpeg**: Configurado en ajustes o disponible en el PATH del sistema.

### Ejecución desde código fuente

```powershell
# Clonar el repositorio
git clone https://github.com/ikerperez12/BLENDER-TOOL.git
cd BLENDER-TOOL

# Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# Ejecutar la aplicación
.venv\Scripts\python.exe app\main.py
```

### Compilación del instalador

Requisitos adicionales: [PyInstaller](https://pyinstaller.org/) y [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```powershell
.venv\Scripts\python.exe build.py
```

Esto ejecuta automáticamente:
1. Verificación pre-compilación (`verify.py`)
2. Empaquetado con PyInstaller (modo `onedir`)
3. Compilación del instalador con Inno Setup
4. Generación del checksum SHA256

Los artefactos finales se organizan en `releases/<versión>/`.

---

## 📂 Estructura del Proyecto

```
app/
├── main.py              # Punto de entrada de la aplicación
├── core/                # Servicios: DB, settings, log, scanner, subprocess, outbox
└── ui/                  # Interfaz PySide6, tema oscuro, ventana principal
blender_scripts/         # Scripts Python ejecutados dentro de Blender (CLI background)
docs/                    # Documentación técnica completa (14 capítulos)
installer/               # Script Inno Setup (.iss)
build.py                 # Script de compilación de producción
verify.py                # Verificación pre-compilación de imports y entorno
```

---

## 📝 Documentación

Para detalles técnicos completos, consulta la carpeta `docs/`:

| Archivo | Contenido |
|---------|-----------|
| [01_vision.md](docs/01_vision.md) | Alcance del producto, visión y roadmap |
| [02_user_guide.md](docs/02_user_guide.md) | Guía de usuario (instalación y uso) |
| [03_installation.md](docs/03_installation.md) | Despliegue en Windows, PyInstaller e Inno Setup |
| [04_first_run_wizard.md](docs/04_first_run_wizard.md) | Asistente de configuración inicial |
| [05_project_modes.md](docs/05_project_modes.md) | Modos de proyecto (IP Legacy, Manual, Single Blend) |
| [06_architecture.md](docs/06_architecture.md) | Modelo de threading, estructura MVC |
| [07_cli_contract.md](docs/07_cli_contract.md) | Contrato CLI entre Python y Blender |
| [08_database_schema.md](docs/08_database_schema.md) | Esquema de base de datos SQLite |
| [09_release_process.md](docs/09_release_process.md) | Proceso de release |
| [10_troubleshooting.md](docs/10_troubleshooting.md) | Solución de problemas comunes |
| [11_security_privacy.md](docs/11_security_privacy.md) | Seguridad y privacidad |
| [12_diagnostics.md](docs/12_diagnostics.md) | Diagnósticos y utilidades |
| [13_qa_checklist.md](docs/13_qa_checklist.md) | Checklist de QA |
| [14_progress_and_logging.md](docs/14_progress_and_logging.md) | Progreso real y logging |

---

## 📄 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).
