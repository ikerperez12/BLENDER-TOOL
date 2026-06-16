# Asistente de Configuración Inicial (First-Run Wizard)

Este documento describe el diseño y el flujo de usuario del **Asistente de Configuración Inicial**, el cual garantiza una experiencia guiada y sencilla para los usuarios que abren **IP Blender Tool** por primera vez.

---

## 🚀 Descripción General

Para evitar que los usuarios tengan que editar archivos de configuración JSON de forma manual o buscar paneles de ajustes complejos al iniciar, la aplicación detecta si es la primera vez que se ejecuta (comprobando si `first_run_completed` está establecido en `False` en la base de datos o si no existen ajustes).

Si no se ha completado la configuración inicial:
1. La ventana principal `MainWindow` se inicia en un estado deshabilitado (el escaneo y la cola de renderizado quedan bloqueados).
2. Se muestra el asistente modal `FirstRunWizard` superpuesto sobre la ventana principal.
3. El usuario debe completar los pasos del asistente para desbloquear todas las funciones.

---

## 🗺️ Pasos del Asistente

El asistente está estructurado como un diálogo paso a paso que consta de 4 páginas principales:

### Paso 1: Localizar Blender (`blender.exe`)
* **Propósito**: Localizar el motor de renderizado de Blender para ejecutar los renders mediante línea de comandos (CLI).
* **Controles de la interfaz**:
  - Etiqueta de autodetección que indica si se encontró Blender en las rutas por defecto (`C:\Program Files\Blender Foundation\Blender *`).
  - Campo de texto que muestra la ruta seleccionada.
  - Botón **Examinar...** que abre un explorador de archivos de Windows para seleccionar `blender.exe` de forma manual.
* **Validación**: La ruta seleccionada debe existir y el archivo debe llamarse obligatoriamente `blender.exe`.

### Paso 2: Configurar Carpetas
* **Propósito**: Definir los directorios base de trabajo del usuario.
* **Controles de la interfaz**:
  - **Directorio de Proyectos**: La carpeta raíz que contiene tus archivos `.blend` o estructuras de proyectos.
  - **Directorio de Renders**: Carpeta de destino predeterminada donde se almacenarán las imágenes y secuencias finales.
  - Botones **Examinar...** en ambos campos para abrir el selector de carpetas nativo de Windows.
* **Validación**: Ambas rutas deben corresponder a carpetas reales y existentes.

### Paso 3: Modo de Proyecto
* **Propósito**: Seleccionar el perfil de ingesta por defecto para el escaneo inicial.
* **Controles de la interfaz**:
  - Selector de perfil (por ejemplo: `IP Legacy`, `Carpeta Manual`, `Archivo Único`).
  - Breve descripción del comportamiento de cada modo para guiar al usuario.
* **Validación**: Debe seleccionarse uno de los perfiles disponibles.

### Paso 4: Probar Configuración
* **Propósito**: Verificar que toda la configuración ingresada sea correcta y funcional antes de guardar.
* **Controles de la interfaz**:
  - Botón **Probar Configuración**.
  - Indicadores de progreso y estado que comprueban:
    1. Ejecución de Blender: Intenta obtener la versión (`blender.exe -v`).
    2. Permisos de escritura en la carpeta de proyectos.
    3. Permisos de escritura en la carpeta de renders.
  - Botón **Finalizar** (solo se habilitará si todas las pruebas del test se completan con éxito).

---

## 🔒 Comportamiento al Cancelar

Si el usuario cierra o cancela el diálogo del asistente sin completarlo:
* La aplicación principal permanece abierta pero en un **Modo de Solo Lectura Deshabilitado**.
* Se mostrará un banner de aviso en la interfaz: `⚠️ Configuración incompleta. Por favor complete el asistente inicial.`
* Las acciones de escaneo e inicio de cola permanecen bloqueadas.
* El usuario aún puede acceder a los botones **⚙ Ajustes** o **Diagnóstico** en la barra lateral para corregir las rutas manualmente, o hacer clic en **Iniciar Asistente** para volver a abrir el flujo guiado.
* Esta restricción de seguridad previene la ejecución de subprocesos rotos o la corrupción de la base de datos por rutas inválidas.
