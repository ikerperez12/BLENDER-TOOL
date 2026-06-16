# Proceso de Compilación y Distribución (Release Process)

Este documento detalla cómo compilar **IP Blender Tool** en un paquete instalable `.exe` ejecutable para Windows.

---

## 🛠️ Herramientas de Compilación
El flujo de compilación consta de:
1. **PyInstaller**: Empaqueta el código Python, el entorno virtual y las dependencias (PySide6, etc.) en un directorio ejecutable autónomo (`mode onedir`).
2. **Inno Setup**: Compila ese directorio resultante en un único instalador ejecutable (`.exe`) de Windows, configurando accesos directos, registro de desinstalación y directorios de usuario.

---

## 🚀 Paso a Paso del Build

Todo el proceso está automatizado a través del script [build.py](file:///c:/PROYECTOS/IDEAS/BLENDER%20TOOL/build.py) ubicado en la raíz del proyecto.

### 1. Preparación del Entorno
Asegúrate de que el entorno virtual está activo y las dependencias de Python están instaladas:
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```
*Nota: Debes tener instalado el compilador Inno Setup 6 en el sistema. El script intentará buscar `ISCC.exe` en las rutas por defecto de Program Files y en la carpeta local de programas de AppData.*

### 2. Ejecutar la Compilación
Lanza el script de build:
```powershell
python build.py
```

El script de compilación realizará automáticamente los siguientes pasos:
1. **Sanity Check**: Ejecuta `verify.py` para asegurar que las importaciones y la base de datos funcionan localmente.
2. **Limpieza**: Elimina cualquier rastro de compilaciones previas (`build/`, `dist/`, `releases/`).
3. **Ejecutar PyInstaller**: Lee `IPBlenderTool.spec` y genera la carpeta ejecutable en `dist/IPBlenderTool`.
4. **Verificar Scripts**: Comprueba que los scripts internos de Blender en `_internal/blender_scripts/` se empaquetaron correctamente.
5. **Inno Setup (ISCC)**: Invoca el compilador de Inno Setup con el archivo `installer/ip_blender_tool.iss`.
6. **Integridad (SHA256)**: Genera un hash SHA256 del instalador resultante y crea un archivo de texto `.sha256` a su lado.
7. **Organización**: Mueve los archivos finales a `releases/1.0.0/`.

---

## 📦 Estructura de Salida (Release)
Tras completar con éxito el script, la carpeta `releases/1.0.0/` contendrá:
* `IP-Blender-Tool-Setup-1.0.0.exe`: El instalador ejecutable final.
* `IP-Blender-Tool-Setup-1.0.0.exe.sha256`: Archivo con el hash de verificación de integridad.
* `CHANGELOG.md` & `release_notes_v1.0.0.md`: Documentos informativos de la release.

---

## ⚙️ Reglas de Aislamiento en el Instalador
El script Inno Setup está configurado en modo no administrativo (`PrivilegesRequired=lowest`):
* **Destino de Ejecutables**: Se instala en `%LOCALAPPDATA%\Programs\IP Blender Tool\`. Esto permite a cualquier usuario instalar la app sin permisos de administrador.
* **Destino de Estado e Historial**: La base de datos SQLite y las configuraciones de usuario se guardan en `%APPDATA%\IP Blender Tool\`. Esto garantiza que la carpeta de instalación permanezca libre de escrituras de datos a nivel de ejecución.
* **Desinstalación Segura**: Al desinstalar la app, se eliminan los ejecutables y los accesos directos, pero **se preservan** la base de datos de configuraciones, los logs e imágenes renderizadas de los usuarios para evitar pérdidas de datos accidentales.
