# Guía de Instalación y Empaquetado - IP Blender Tool

Este documento detalla los procesos de instalación para usuarios finales, la configuración del entorno para desarrolladores, y los flujos de compilación/empaquetado del software.

---

## 💻 1. Instalación para Usuarios Finales

### Requisitos del Sistema
- **Sistema Operativo:** Windows 10 o Windows 11 (64 bits).
- **Blender:** Instalado y configurado en el sistema (probado en Blender 4.2 LTS y Blender 5.1).
- **FFmpeg:** Requerido solo si deseas compilar animaciones en formato MP4 o previsualizaciones.

### Instrucciones de Instalación
1. Descarga el instalador ejecutable oficial: `IP-Blender-Tool-Setup-1.0.0.exe` desde la pestaña de **Releases** en GitHub.
2. Ejecuta el archivo de instalación.
3. El asistente instalará la aplicación de forma predeterminada en tu ruta local de programas:
   `C:\Users\<Usuario>\AppData\Local\Programs\IP Blender Tool\`
   *Esta ruta local evita la necesidad de solicitar permisos de administrador (Privilegios mínimos).*
4. Selecciona si deseas crear un acceso directo en el escritorio y haz clic en **Instalar**.
5. Abre la aplicación desde el escritorio o el menú Inicio y sigue las indicaciones del Asistente de Configuración Inicial (First-Run Wizard).

### Desinstalación
- Puedes desinstalar el software en cualquier momento desde la herramienta nativa de Windows **Configuración > Aplicaciones > Aplicaciones instaladas** seleccionando "IP Blender Tool".
- **Nota de seguridad de datos:** La desinstalación eliminará los ejecutables instalados pero **conservará tus carpetas de proyectos, renders, configuraciones y base de datos histórica** en AppData, a menos que decidas borrarlos de forma manual.

---

## 🛠️ 2. Configuración y Ejecución para Desarrolladores

Para ejecutar la aplicación desde el código fuente o realizar modificaciones:

### Requisitos Previos
- Python 3.11 o superior instalado.
- Git.

### Configuración del Entorno de Desarrollo
1. Clona el repositorio del proyecto:
   ```powershell
   git clone <repo_url>
   cd "BLENDER TOOL"
   ```
2. Inicializa un entorno virtual de Python:
   ```powershell
   python -m venv .venv
   ```
3. Activa el entorno virtual e instala los paquetes requeridos:
   ```powershell
   .venv\Scripts\pip.exe install -r requirements.txt
   ```
4. Inicia la aplicación en modo desarrollo:
   ```powershell
   .venv\Scripts\python.exe app\main.py
   ```

---

## 📦 3. Compilación y Empaquetado de Releases

Para empaquetar de forma automática toda la aplicación en una carpeta autocontenida y posteriormente compilar el instalador `.exe`:

### Requisitos de Compilación
- Tener instalado **Inno Setup 6+** en Windows. Si no lo tienes, puedes instalarlo ejecutando en tu terminal:
  ```powershell
  winget install --id JRSoftware.InnoSetup -e --accept-package-agreements --accept-source-agreements
  ```

### Ejecución del Script de Compilación Automatizado
El proyecto incluye un script de compilación `build.py` en la raíz que ejecuta de forma secuencial todo el proceso de empaquetado:
```powershell
.venv\Scripts\python.exe build.py
```

Este script ejecuta las siguientes tareas automáticamente:
1. **Limpieza:** Borra builds anteriores (`build/`, `dist/`, `releases/`).
2. **Verificación:** Ejecuta el script `verify.py` para asegurar que el entorno es correcto.
3. **PyInstaller:** Empaqueta el código fuente en modo `onedir` usando `IPBlenderTool.spec`.
4. **Verificación del Bundle:** Revisa que los scripts internos de Blender (`blender_scripts/`) se hayan incluido correctamente en la compilación.
5. **Inno Setup:** Invoca `ISCC.exe` para compilar el instalador de Windows.
6. **Integridad:** Calcula el hash SHA256 del instalador y crea el archivo `.sha256`.
7. **Organización:** Mueve y ordena el instalador, changelog y checksum en la carpeta final `releases/1.0.0/`.
