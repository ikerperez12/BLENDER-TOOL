# Guía de Usuario - IP Blender Tool

Este manual detalla el flujo de instalación, configuración inicial y uso de **IP Blender Tool** para automatizar tu flujo de trabajo de renders con Blender.

---

## 🚀 1. Instalación y Puesta en Marcha

### Para Usuarios Finales
1. Descarga el archivo de instalación `IP-Blender-Tool-Setup-1.0.0.exe` desde la página de Lanzamientos (Releases) de GitHub.
2. Ejecuta el archivo. La aplicación se instalará en tu carpeta local de usuario (`%USERPROFILE%\AppData\Local\Programs\IP Blender Tool\`), por lo que no requiere permisos de administrador.
3. Al finalizar, inicia la aplicación desde el acceso directo creado en tu escritorio o en el menú de inicio.

### Para Desarrolladores (Ejecución desde Código)
Si prefieres ejecutar el software directamente desde el código fuente:
1. Asegúrate de tener Python 3.11+ instalado.
2. Instala las dependencias necesarias: `.venv\Scripts\pip.exe install -r requirements.txt`.
3. Ejecuta el archivo principal:
   ```powershell
   .venv\Scripts\python.exe app\main.py
   ```

---

## ⚙️ 2. Asistente de Configuración Inicial (First-Run Wizard)

Si es la primera vez que abres **IP Blender Tool**, aparecerá de forma obligatoria el asistente inicial en pantalla para guiarte en los siguientes pasos:

* **Paso 1: Blender**: Localizar y seleccionar el ejecutable principal (`blender.exe`). El asistente intentará detectarlo automáticamente en `C:\Program Files\Blender Foundation\`. Si no lo logra, puedes seleccionarlo manualmente con el botón **Examinar...**.
* **Paso 2: Carpetas**: Configurar el **Directorio de Proyectos** (donde se encuentran tus archivos `.blend`) y el **Directorio de Renders** (donde se guardarán las imágenes finales).
* **Paso 3: Modo de Proyecto**: Seleccionar el perfil de ingesta por defecto para la búsqueda y nombrado de archivos.
* **Paso 4: Probar Configuración**: Hacer clic en **Probar Configuración** para validar que la ruta de Blender es correcta y que tienes permisos de escritura. Una vez aprobado el test, se habilitará el botón **Finalizar**.

> [!NOTE]
> Si cierras el asistente sin completarlo, la aplicación se mantendrá en un **Modo de Solo Lectura Deshabilitado** para evitar fallos. Podrás volver a lanzar el asistente o modificar cualquiera de estas rutas haciendo clic en el botón **⚙ Ajustes** en la esquina superior derecha de la interfaz principal.

---

## 📂 3. Modos de Ingesta y Escaneo de Proyectos

La sección **1. Proyecto a Cargar** soporta tres pestañas según la estructura de tu proyecto:

### A. ID Legacy (Modo IP)
- **Uso:** Ideal si usas una estructura organizada por carpetas indexadas por números de proyecto (e.g. `(0024)_Cliente_Blender`).
- **Paso a paso:** Escribe el ID numérico del proyecto (e.g. `0024`) y haz clic en **Escanear ID**.
- **Comportamiento:** La aplicación resolverá de forma automática el directorio bajo el patrón `(0024)*`, localizará los archivos `.blend` de cámaras principales dentro de `03_*_3D_BLENDER` y asignará la ruta de salida a `06_*_3D_RENDERS`.

### B. Carpeta Manual
- **Uso:** Para cualquier directorio estructurado libremente que contenga archivos de Blender.
- **Paso a paso:** Selecciona la carpeta origen del proyecto y, de forma opcional, una carpeta destino para los renders. Haz clic en **Escanear Carpeta**.
- **Comportamiento:** Escanea recursivamente el directorio seleccionado (hasta una profundidad máxima de 3 subcarpetas) para descubrir archivos `.blend`.

### C. Archivo Blend
- **Uso:** Para renderizar una cámara o escena directamente desde un archivo `.blend` específico.
- **Paso a paso:** Selecciona el archivo `.blend` específico y, opcionalmente, la carpeta de destino. Haz clic en **Escanear Archivo**.
- **Comportamiento:** Abre de forma silenciosa el archivo seleccionado para leer sus cámaras internas.

---

## 📷 4. Selección de Cámaras y Perfiles de Calidad

1. Tras completar el escaneo de un proyecto, el panel **2. Cámaras Detectadas** mostrará la lista de cámaras leídas del archivo.
2. Selecciona las casillas de las cámaras que deseas renderizar.
3. **Compilación y montaje automatizados:**
   - Si se detecta un archivo de post-composición asociado (`_montaje.blend`), la opción **+ Montaje** se marcará de forma automática para generar una salida montada JPEG.
   - Si los fotogramas de inicio y fin de la escena difieren, se habilitará la opción **+ Video MP4** para compilar la animación con FFmpeg.
4. En la sección **3. Calidad de Salida**, elige un perfil de renderizado:
   - **Borrador:** Renders en formato JPEG a 50% de resolución para revisiones rápidas.
   - **Cliente:** Renders a 100% de resolución en PNG, ideales para aprobación de detalles.
   - **Final:** Renders a máxima calidad (100% o 200%) en PNG/EXR con alta tasa de muestreo.
5. Haz clic en **➕ Añadir a Cola** para encolar los trabajos.

---

## 🚦 5. Gestión y Ejecución de la Cola

1. Configura una acción automática para cuando finalicen los renders en el menú desplegable **Al finalizar cola** (e.g., *Apagar PC* o *Suspender PC*).
2. Haz clic en **▶ Iniciar Cola** para comenzar la ejecución secuencial.
3. En cualquier momento puedes pulsar **⏸ Pausar** para detener la cola o **🛑 Cancelar Actual** para abortar de forma segura el proceso de Blender en ejecución (la app matará todo el árbol de procesos huérfanos).
4. Si necesitas examinar detalles del renderizado en tiempo real, haz clic en **▼ Mostrar Consola Técnica**.
5. Abre la carpeta final de renders haciendo clic en el botón **📂 Renders**.
