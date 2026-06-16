# Sistema de Progreso Real y Logs Limpios (Progress & Logging)

Este documento detalla la especificación técnica de la canalización de progreso y el sistema de logs filtrados en **IP Blender Tool v1.0.0**.

---

## 🚫 1. Regla de Oro: Progreso Real, No Simulado

La aplicación tiene prohibido simular porcentajes de progreso mediante temporizadores heurísticos en proyectos reales.
* **Porcentaje Determinado**: Solo se muestra si existe una métrica física medible emitida directamente por el subproceso (Blender o FFmpeg).
* **Porcentaje Indeterminado**: Si el proceso está activo pero no hay un porcentaje interno fiable del progreso del renderizado, la barra de progreso de la UI entrará en modo indeterminado (`setRange(0, 0)` en PySide6), indicando de forma honesta que la tarea está en curso sin inventar porcentajes.

---

## 📡 2. Eventos Estructurados `IPBT_EVENT`

Para evitar el parseo heurístico de la consola técnica de Blender (el cual es frágil ante cambios de versión del motor), nuestros scripts de Blender instrumentados ([scan_scene.py](file:///c:/PROYECTOS/IDEAS/BLENDER%20TOOL/blender_scripts/scan_scene.py), [render_camera.py](file:///c:/PROYECTOS/IDEAS/BLENDER%20TOOL/blender_scripts/render_camera.py) y [update_compositor.py](file:///c:/PROYECTOS/IDEAS/BLENDER%20TOOL/blender_scripts/update_compositor.py)) emiten eventos JSON estructurados en la salida estándar (`stdout`) con el prefijo `IPBT_EVENT `.

### Formato del Evento
Cada evento es una única línea impresa en la consola con el formato:
```text
IPBT_EVENT {"job_id": 123, "type": "event_type", "phase": "phase_name", "message": "Texto descriptivo", ...}
```
*Cada línea debe ser descargada inmediatamente usando `flush=True` en Python.* El campo `job_id` es obligatorio para poder asociar unívocamente el evento con la tarea de la cola.

### Manejo de Errores de Parseo
Si una línea empieza por `IPBT_EVENT ` pero no se puede parsear como un JSON válido:
- Se escribe la línea completa inalterada en el archivo de log técnico físico.
- Se muestra una advertencia limpia (`[ADVERTENCIA] ...`) opcional en la UI console.
- **No se interrumpe la ejecución del render** ni se bloquea la interfaz de usuario.

### Tipos de Eventos Mínimos
1. **`job_started`**: Emitido cuando se inicia el proceso de Blender.
2. **`blend_loaded`**: Emitido tras cargar el archivo `.blend`.
3. **`scene_prepared`**: Emitido cuando la cámara y los perfiles de render se aplican.
4. **`render_started`**: Emitido antes de invocar el renderizado de Blender.
5. **`frame_started`**: Emitido al iniciar el procesamiento de un fotograma en particular.
6. **`frame_done`**: Emitido tras completar y guardar físicamente un fotograma en el disco.
7. **`render_saved`**: Emitido cuando se guarda la imagen final.
8. **`compositor_started`**: Emitido al iniciar el postprocesado de montaje.
9. **`compositor_image_replaced`**: Emitido al intercambiar la imagen del render en el compositor.
10. **`compositor_saved`**: Emitido tras guardar la salida final del compositor.
11. **`job_completed`**: Emitido al finalizar la ejecución del script con éxito.
12. **`warning`**: Registra advertencias (como texturas faltantes).
13. **`error`**: Informa errores críticos (como cámara no encontrada o CUDA out of memory).

---

## 🎬 3. Progreso de FFmpeg (Compilación de Video)

El componente ejecutor de FFmpeg ([ffmpeg_runner.py](file:///c:/PROYECTOS/IDEAS/BLENDER%20TOOL/app/core/ffmpeg_runner.py)) sigue las mismas reglas de honestidad de progreso:
* **Métrica Física**: La tasa de compilación se basa en la lectura de `frame=[número]` de la salida de FFmpeg dividido por el número total de imágenes físicas en la secuencia a procesar.
* **Barra Indeterminada**: Si la salida de FFmpeg no provee información parseable en tiempo real o no se puede calcular el frame actual de forma fiable, la barra permanecerá en modo indeterminado con el texto "Compilando video...".
* **Separación de Logs**: Al igual que con Blender, toda la salida estándar (`stdout`/`stderr`) de FFmpeg se escribe directamente en el archivo `.log` técnico asociado al trabajo, manteniendo la consola de la UI limpia.

---

## 🪵 4. Canalización y Separación de Logs

El componente `BlenderRunner` intercepta la salida estándar y la separa en tres canales distintos:

```text
Blender Subprocess Stdout
           │
           ▼
     BlenderRunner
      /    │    \
     /     │     \
    /      │      \
   ▼       ▼       ▼
Canal 1  Canal 2  Canal 3
[Eventos] [Log Limpio] [Log Técnico]
   │       │         │
   ▼       ▼         ▼
  Progreso  Consola   Archivo .log
   UI       UI        %APPDATA%/logs/
```

### Canal 1: Progreso de UI (`IPBT_EVENT`)
Filtra las líneas que comienzan con `IPBT_EVENT `, las decodifica como JSON y actualiza:
- **Animaciones**: Porcentaje calculado como `frames_completados / total_frames`.
- **Renders Fijos**: Transita por fases (`launch` 0%, `load` 5%, `prepare` 10%, `render` indeterminado (o samples si se obtienen de stats), `save` 95%, `complete` 100%).
- **Montajes**: Muestra el paso actual del pipeline.

### Canal 2: Consola Visual Limpia (UI)
Muestra únicamente logs informativos breves, advertencias y errores críticos. Esto evita saturar al usuario con el spam de inicialización de Blender. Además, la consola visual está limitada a un tamaño máximo de **500 líneas** mediante rotación de texto en caliente.

### Canal 3: Archivo de Logs Técnico (Raw)
Todo el flujo de `stdout` y `stderr` sin procesar de Blender se escribe de forma síncrona en un archivo de log físico en el disco:
`%APPDATA%\IP Blender Tool\logs\job_[job_id]_[camera].log`

La ruta absoluta real de este archivo de log se guarda en la columna `log_file` de la tabla `jobs` de la base de datos sqlite en cuanto inicia el trabajo.

La interfaz de usuario expone dos botones de control bajo la Consola Técnica:
- **📂 Ver log completo**: Abre la ruta del archivo `.log` real técnico asociada al trabajo en el editor de texto predeterminado del sistema (Notepad).
- **📋 Copiar error**: Si el trabajo falló, copia el sumario de error (`error_summary`) directamente al portapapeles.
