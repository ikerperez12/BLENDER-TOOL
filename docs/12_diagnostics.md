# Sistema de Diagnóstico (Panel y Herramientas)

Este documento detalla el **Sistema de Diagnóstico** integrado en la barra lateral colapsable de **IP Blender Tool v1.0.0**.

---

## 🛠️ Panel de Diagnóstico en la Interfaz
Ubicado en el lateral izquierdo, permite comprobar el estado del entorno de renderizado, empaquetar archivos de depuración y generar proyectos de prueba sin necesidad de ejecutar comandos en la terminal.

---

## 🔍 1. Pruebas Rápidas (Pre-Flight Checks)
Al hacer clic en **"🔍 Ejecutar Preflight Checks"**, la aplicación ejecuta una serie de tests automáticos en tiempo real y muestra un resumen con los siguientes puntos:
1. **Ruta de Blender**: Verifica si el ejecutable `blender.exe` configurado responde correctamente (`blender.exe -b -v`).
2. **FFmpeg**: Valida si el comando `ffmpeg` es accesible para la compilación de videos y animaciones MP4.
3. **Base de Datos**: Verifica la conexión y permisos de lectura/escritura en el archivo `jobs.sqlite`.
4. **Permisos de Carpetas**: Intenta crear y borrar un archivo temporal de prueba en las carpetas base de proyectos y renders configuradas.
5. **Conexiones de Notificación**: Comprueba el envío a los servicios de Telegram/Discord si el usuario ha habilitado e ingresado sus configuraciones.

---

## 📦 2. Exportación de Diagnósticos (ZIP)
Cuando el usuario detecta un error y solicita soporte técnico, puede hacer clic en **"📦 Exportar ZIP de Diagnóstico"**:
* **Ubicación**: El usuario selecciona dónde guardar el archivo comprimido (por defecto `Desktop/ip_blender_tool_diagnostic.zip`).
* **Contenido por defecto (Seguro)**:
  - `app_settings_redacted.json`: Copia de los ajustes de configuración con todos los tokens de notificaciones, chats y webhooks eliminados, y nombres de usuario locales anonimizados (`C:\Users\<USER>`).
  - `db_schema.sql`: Un archivo SQL con el volcado vacío del esquema de las tablas. No se exportan filas de datos históricos ni nombres de proyectos de forma predeterminada.
  - Carpetas de `logs/`: Historial de registros del programa con trazas detalladas y excepciones capturadas de ejecuciones anteriores (anonimizando nombres de usuario en rutas).
  - `preflight_diagnostics.json`: Estado de las verificaciones de Blender, base de datos y sistema operativo.
* **Consentimiento Avanzado de Base de Datos**:
  - Para depurar fallas complejas de la cola de renders, el usuario puede marcar la casilla **"Incluir base de datos (sanitizada)"** antes de exportar.
  - Esto adjuntará al ZIP el archivo `jobs_sanitized.sqlite`. Dicho archivo es una copia limpia donde el sistema ha ejecutado un script de limpieza automática, eliminando nombres de carpetas privados, nombres reales de proyectos y rutas locales de archivos antes de insertarlo en el paquete comprimido.

---

## 🎮 3. Generación de Proyecto Demo y Modo Simulado

Para permitir a los usuarios probar las capacidades de la interfaz incluso si no disponen de Blender instalado en su máquina (o están en una fase de configuración inicial), el panel incluye el botón **"Generar Proyecto Demo"**.

### Carpeta del Proyecto Demo
Genera una estructura de pruebas en la raíz de proyectos seleccionada:
```text
[Carpeta de Proyectos]/
└── (0000)_Proyecto_Demo/
    ├── 03_0000_3D_BLENDER/
    │   ├── (0000)_Camara A.blend (Archivo mockup de Blender)
    │   └── (0000)_Camara A_montaje.blend (Archivo de post-composición)
    ├── 06_0000_3D_RENDERS/ (Carpeta vacía lista para renders)
    └── LEEME_DEMO.txt (Instrucciones de uso paso a paso)
```

### Modo Simulado (Mock Mode)
* **Activación**: Este modo simulado se ejecuta **exclusivamente** para el proyecto demo `0000` si la aplicación detecta que la ruta de Blender no está configurada o no es válida.
* **Comportamiento**:
  - **Escaneo**: Al escanear el proyecto `0000`, la aplicación intercepta la falta de Blender y devuelve cámaras y configuraciones preestablecidas de prueba en lugar de fallar. En la interfaz se mostrará el estado en azul como: **"Listo (Modo Demo / Simulado)"**.
  - **Renderizado**: Al iniciar la cola con trabajos del proyecto demo en Modo Simulado, la aplicación emite una secuencia de progreso progresiva durante unos segundos (~3s por cámara).
  - **Aislamiento de Archivos de Salida**: Al finalizar la renderización simulada, la app crea un archivo de imagen demo PNG vacío (de 1x1 píxeles) tanto en la ruta tradicional como en una subcarpeta aislada llamada **`demo_renders`** dentro del proyecto para evitar mezclar datos simulados con renders reales en producción.
  - **Seguridad**: El Modo Simulado está estrictamente limitado al proyecto `0000`. Si un usuario intenta renderizar un proyecto con código real sin Blender configurado, el sistema rechazará la acción y marcará el trabajo como `Failed` arrojando un error claro.
