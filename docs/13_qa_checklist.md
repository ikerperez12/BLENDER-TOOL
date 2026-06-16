# Lista de Verificación de Calidad (QA Release Checklist)

Esta lista de verificación debe ser ejecutada y aprobada en su totalidad sobre un entorno de pruebas (idealmente una máquina virtual de Windows limpia o sandbox) antes de publicar cualquier release oficial de **IP Blender Tool**.

---

## 🚫 Criterios de Bloqueo de Lanzamiento (Release Blockers)

Cualquier fallo en los siguientes puntos bloquea de forma inmediata e incondicional la publicación de la release:
* **Elevación de privilegios**: El instalador solicita permisos de Administrador de Windows de forma obligatoria durante el asistente de instalación.
* **Dependencia de Python**: La aplicación compilada no se abre en una máquina limpia que no tenga Python instalado en el sistema.
* **Asistente Inicial Roto**: El First-Run Wizard no persiste los ajustes de Blender o carpetas y obliga a reconfigurar en cada inicio.
* **Procesos Huérfanos**: Al pulsar "Cancelar" en la cola de renderizado, el proceso de fondo `blender.exe` permanece vivo y consumiendo CPU/GPU en Task Manager.
* **Estados Engañosos**: Un renderizado fallido (debido a falta de VRAM, texturas ausentes, etc.) se marca como `Completed` en lugar de `Failed`.
* **Fuga de Secretos**: El ZIP de diagnóstico exportado contiene tokens de Telegram o webhooks de Discord en texto plano sin redactar.
* **Pérdida de Datos**: La desinstalación del programa borra de forma destructiva las carpetas de renders configuradas por el usuario.
* **Progreso Simulado**: El progreso de la barra en renders reales avanza sin una métrica física verídica (porcentaje inventado por temporizador).
* **Consola Saturada**: La UI muestra el flujo sin procesar completo de Blender (ej. spam de muestras de renderizado o inicialización) saturando la memoria o la vista.
* **Falta de Logs Físicos**: Las ejecuciones de Blender no guardan su salida técnica (`stdout`/`stderr` raw) completa en un archivo `.log` en el disco.

---

## 📋 Lista de Pruebas y Validación Manual

### 1. Instalación y Primer Arranque
- [ ] **Instalación limpia**: Ejecutar `IP-Blender-Tool-Setup-[versión].exe` en un Windows limpio sin dependencias de desarrollo.
- [ ] **Accesos directos**: Verificar que se crea el acceso directo en el escritorio y el menú Inicio, e inicia la app sin problemas.
- [ ] **Generación de AppData**: Comprobar que en `%APPDATA%\IP Blender Tool\` se inicializan correctamente `jobs.sqlite` y la configuración por defecto.
- [ ] **Instalación sin admin**: Asegurarse de que el instalador corre bajo el nivel de privilegios del usuario actual (`PrivilegesRequired=lowest`).

### 2. Asistente Wizard de Configuración
- [ ] **Arranque modal**: Confirmar que el wizard se abre inmediatamente al detectar que `first_run_completed` es False, bloqueando el uso de la ventana principal.
- [ ] **Modo de Solo Lectura**: Cancelar el asistente inicial y verificar que la app principal permanece bloqueada, con un banner indicando configuración incompleta.
- [ ] **Autodetección de Blender**: Validar si detecta versiones preinstaladas en rutas estándar de Program Files.
- [ ] **Exploración manual**: Seleccionar `blender.exe` y las carpetas de proyectos y renders mediante los botones **Examinar...**.
- [ ] **Persistencia**: Cerrar el programa tras completar el asistente, volver a abrirlo y validar que no vuelve a mostrarse el wizard.

### 3. Modos de Ingesta y Escaneo
- [ ] **Pestaña IP Legacy**: Ingresar el código `0001`, pulsar "Escanear" y comprobar que localiza los archivos `.blend` correctos en la subcarpeta `03_0001_3D_BLENDER` y asigna la salida a `06_0001_3D_RENDERS`.
- [ ] **Pestaña Carpeta Manual**: Seleccionar una carpeta cualquiera que contenga archivos `.blend`, realizar el escaneo recursivo y verificar que lee las cámaras.
- [ ] **Pestaña Archivo Único**: Escoger un archivo de Blender directamente y comprobar que extrae las cámaras correspondientes.
- [ ] **Test de Timeout**: Cargar un archivo `.blend` con dependencias pesadas o scripts de bloqueo; verificar que el escaneo se interrumpe limpiamente por timeout a los 120 segundos arrojando un error amigable.

### 4. Cola de Renderizado y Ejecución
- [ ] **Encolado de trabajos**: Seleccionar varias cámaras, elegir un perfil de calidad (ej: Borrador) y agregarlos a la cola.
- [ ] **Ejecución no bloqueante**: Iniciar la cola de render. Validar que la interfaz principal sigue respondiendo, se pueden cambiar pestañas y ver el progreso.
- [ ] **Verificación de salida real**: Tras finalizar un render, verificar que el archivo final existe en el disco y tiene un tamaño mayor a 0 bytes antes de marcarse como `Completed`.
- [ ] **Fallo controlado**: Forzar un render fallido (por ejemplo, renombrando una cámara temporalmente). Verificar que la tarea encola reintentos y finalmente cambia su estado a `Failed`.
- [ ] **Cancelación Segura**: Cancelar un trabajo en curso. Comprobar que el proceso secundario de Blender se detiene instantáneamente y no queda ningún subproceso huérfano en ejecución.
- [ ] **Progreso de Animaciones**: Comprobar que el progreso de una animación avanza estrictamente por frames reales completados.
- [ ] **Progreso de Stills / Fijos**: Comprobar que un render fijo sin progreso de Cycles (o que use Eevee) muestra una barra indeterminada en la UI.
- [ ] **Consola Visual Limpia**: Verificar que la consola en la UI no muestra spam repetitivo de Cycles ("Sample X/Y") ni volcado de datos inicial.
- [ ] **Persistencia de Logs Raw**: Validar que la salida completa y sin filtros de Blender queda guardada en `%APPDATA%\IP Blender Tool\logs\job_[job_id]_[camera].log`.
- [ ] **Botón Ver Log Completo**: Validar que el botón abre el log raw del trabajo seleccionado en Notepad.
- [ ] **Botón Copiar Error**: Forzar un error y validar que al hacer clic en el botón se copia el sumario correcto al portapapeles.
- [ ] **Modo Simulado Aislado**: Validar que el avance simulado de progreso no existe en trabajos reales, y que el modo demo simulado se ejecuta exclusivamente en el proyecto `0000`.

### 5. Herramientas de Diagnóstico y Demo
- [ ] **Ejecutar Checks**: Ejecutar el preflight desde la barra lateral y confirmar que todos los tests (Blender, FFmpeg, base de datos) pasan.
- [ ] **Proyecto Demo**: Generar el proyecto demo. Probar a escanearlo y renderizarlo en **Modo Simulado** (con Blender desconfigurado). Verificar que se genera la imagen PNG de prueba en la subcarpeta aislada `demo_renders`.
- [ ] **Exportación ZIP**: Exportar el ZIP de soporte. Abrir el archivo y validar que:
  - Los archivos de logs y la configuración no contienen tokens reales.
  - No incluye la base de datos a menos que se haya marcado explícitamente el checkbox de consentimiento.
  - Si se incluyó la base de datos con consentimiento, las rutas locales no revelan nombres de usuario personales.

### 6. Prueba de Actualización (Update Test)
- [ ] **Instalación de versión previa**: Instalar una versión anterior del software (ej: v0.9.0 o v0.9.5).
- [ ] **Configuración inicial**: Completar el wizard inicial indicando Blender y rutas de proyectos/renders.
- [ ] **Estado previo**: Agregar al menos un trabajo en la cola y dejarlo en estado completado o pendiente.
- [ ] **Instalación sobrepuesta**: Ejecutar el nuevo instalador de la v1.0.0 sobre la versión anterior (sin desinstalar primero).
- [ ] **Verificación de migración**:
  - Validar que los perfiles y rutas anteriores se mantienen intactos.
  - Abrir la cola y verificar que el historial de base de datos se conserva y migró correctamente (añadiendo la nueva columna `blend_path`).
  - La aplicación inicia directamente sin volver a forzar el asistente de configuración inicial de manera innecesaria.

### 7. Control de Procesos, Estadísticas y UI (Pausa/Reanudar/Cancelar y Checkboxes)
- [ ] **Pausar Render**: Iniciar un renderizado de Blender, hacer clic en "Pausa" y comprobar en el Administrador de Tareas que el uso de CPU/GPU de todos los procesos `blender.exe` del árbol de trabajo cae a cero.
- [ ] **Reanudar Render**: Hacer clic en "Reanudar" y verificar que el proceso `blender.exe` continúa renderizando y el progreso progresa.
- [ ] **Cancelar estando Pausado**: Con el render pausado, hacer clic en "Cancelar Actual". Verificar que el proceso se reanuda internamente un instante y luego se cierra por completo, sin dejar procesos `blender.exe` huérfanos.
- [ ] **Advertencia de VRAM**: Validar que al pasar el cursor sobre el botón "Pausa" se muestra el aviso de que pausar el proceso mantiene ocupada la GPU/VRAM.
- [ ] **Visualización de Estadísticas**: Validar que la etiqueta de estadísticas bajo la barra de progreso muestra la memoria, los tiles, las muestras y el tiempo restante de forma legible.
- [ ] **Estadísticas no Disponibles**: Forzar un render o situación donde no haya datos de telemetría disponibles y validar que la etiqueta muestra "Estadísticas no disponibles" o se oculta adecuadamente.
- [ ] **Checkboxes en .exe Compilado**: Instalar la aplicación compilada, ingresar a las listas de cámaras y validar que las casillas (checkboxes) se pueden marcar/desmarcar con clics interactivos, mostrando el indicador de check de forma clara (color azul con checkmark blanco y borde brillante).
- [ ] **Ausencia de Procesos Blender Huérfanos**: Asegurarse de que al terminar o abortar la cola no queden procesos `blender.exe` residuales.

