# IP Blender Tool

> **Render Queue & Automation for Blender**

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

## 🛠️ Requirements & Installation

1. **Python**: Python 3.10+ installed.
2. **Blender**: Blender 4.2 LTS or 5.1 (installed in Program Files, or customizable path).
3. **FFmpeg**: Configured in settings or available in system PATH.

### Quick Start (Source Run)

1. Clone or copy the repository contents.
2. Setup the virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
3. Boot the application:
   ```powershell
   .venv\Scripts\python.exe app\main.py
   ```

---

## 📂 Project Structure

* **`app/main.py`**: Main application bootloader.
* **`app/core/`**: Services for database, settings, logging, project scan, CLI subprocess execution, and outbox thread.
* **`app/ui/`**: PySide6 dark stylesheet and window layout.
* **`blender_scripts/`**: Internal Python scripts executed inside Blender background CLI to scan scenes and run camera/compositor operations.

---

## 📝 Documentation Suite

For deep technical details, check the `docs/` folder:
* **[01_vision.md](docs/01_vision.md)**: Product scope, vision, and roadmap.
* **[02_user_guide.md](docs/02_user_guide.md)**: Steps to run and configure the tool.
* **[03_installation.md](docs/03_installation.md)**: Windows deployment, PyInstaller, and Inno Setup build guides.
* **[06_architecture.md](docs/06_architecture.md)**: Threading model, MVC structure, and boundaries.
* **[07_cli_contract.md](docs/07_cli_contract.md)**: Command line contract between Python and Blender background processes.
* **[08_database_schema.md](docs/08_database_schema.md)**: Database tables and indexes.
* **[10_troubleshooting.md](docs/10_troubleshooting.md)**: Fixes for locked databases, missing paths, and GPU memory errors.

---

## 📄 License
This project is licensed under the MIT License.
