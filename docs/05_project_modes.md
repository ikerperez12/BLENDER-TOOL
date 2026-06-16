# Modos de Proyecto (Project Modes)

Este documento detalla los tres modos de ingesta y escaneo soportados por **IP Blender Tool v1.0.0**. Estos modos hacen que la aplicación sea genérica y flexible, sirviendo tanto para un flujo corporativo específico como para un gestor de renderizado de uso general.

---

## 🗂️ Resumen de Modos

Al iniciar el escaneo de un proyecto, la aplicación explora y organiza los archivos según el modo seleccionado. Esto se registra en la base de datos bajo el campo `project_mode`.

| Nombre del Modo | Cadena DB | Selección de Ingesta | Comportamiento del Escáner | Enrutado de Salida (Renders) |
| :--- | :--- | :--- | :--- | :--- |
| **IP / Legacy** | `IP_LEGACY` | Código numérico (ej: `0024`) | Busca en la raíz la carpeta que coincida con el patrón del código e ingesta los archivos `.blend` de su subcarpeta de Blender. | Genera la salida en `renders_root/<carpeta_proyecto>/vXXX/` |
| **Carpeta Manual** | `MANUAL_FOLDER` | Directorio seleccionado por el usuario | Explora de forma recursiva toda la carpeta seleccionada buscando archivos `.blend`. | Genera la salida en `renders_root/<nombre_carpeta>/vXXX/` |
| **Archivo Único** | `SINGLE_BLEND` | Un archivo `.blend` específico | Omite la exploración de carpetas; lee directamente las escenas y cámaras del archivo seleccionado. | Genera la salida en `renders_root/` o carpetas adyacentes |

---

## 🔍 Comportamiento Detallado

### 1. IP / Legacy (`IP_LEGACY`)
Pensado para flujos de trabajo altamente estandarizados donde las carpetas de proyectos y renders siguen una nomenclatura fija basada en códigos numéricos.
* **Flujo de Ingesta**: El usuario introduce el número del proyecto (ej: `0024`) en el cuadro de texto de la pestaña correspondiente.
* **Lógica de Escaneo**:
  1. El escáner localiza en el directorio raíz de proyectos una carpeta cuyo nombre comience o contenga el número (ej: `(0024)_Proyecto_Haro`).
  2. Dentro de esa carpeta, busca la subcarpeta de Blender (configurada por defecto en el perfil como `03_{project_id}_3D_BLENDER`).
  3. Ejecuta el script de lectura para extraer cámaras, fotogramas y configuraciones de resolución de los archivos `.blend`.
* **Destino**: Los renders se guardan automáticamente en la subcarpeta `06_{project_id}_3D_RENDERS` bajo carpetas de versión incremental (`v0001`, `v0002`...).

### 2. Carpeta Manual (`MANUAL_FOLDER`)
Permite procesar directorios de trabajo personalizados que no siguen la estructura rígida de proyectos Legacy.
* **Flujo de Ingesta**: El usuario hace clic en **Examinar...** para seleccionar cualquier carpeta de su disco duro.
* **Lógica de Escaneo**:
  1. El escáner recorre de forma recursiva el directorio seleccionado buscando todos los archivos `.blend` que contenga.
  2. Lee de cada archivo las cámaras disponibles y las lista agrupadas por archivo.
* **Destino**: Los renders se almacenarán en una carpeta con el mismo nombre del directorio seleccionado dentro de la raíz de renders.

### 3. Archivo Único (`SINGLE_BLEND`)
Diseñado para la renderización rápida de un archivo `.blend` específico sin necesidad de analizar carpetas o subcarpetas.
* **Flujo de Ingesta**: El usuario selecciona un único archivo `.blend` usando el explorador de archivos.
* **Lógica de Escaneo**:
  1. Se omite la recursión en el sistema de archivos.
  2. El escáner ejecuta el script de lectura CLI directamente en el archivo seleccionado.
  3. **Protección de Timeout**: El proceso de lectura cuenta con un **tiempo límite estricto de 120 segundos**. Si el archivo contiene scripts de autoarranque que bloquean la CLI o está dañado, el proceso se aborta automáticamente evitando que la interfaz se congele.
* **Destino**: Salida directa a la carpeta de renders base o rutas relativas.
