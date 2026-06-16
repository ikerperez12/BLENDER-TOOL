# Seguridad y Privacidad (Security & Privacy)

Este documento detalla cómo **IP Blender Tool** maneja los datos de configuración, aísla el estado de la aplicación y protege la privacidad del usuario al generar archivos de diagnóstico.

---

## 🔒 1. Almacenamiento Local y Aislamiento de Estado

Para cumplir con las mejores prácticas de seguridad de Windows y permitir la ejecución del software sin privilegios administrativos:
* **Directorio de Instalación**: Los ejecutables, scripts de Blender y librerías compiladas se instalan en la carpeta local de programas del usuario:
  `%LOCALAPPDATA%\Programs\IP Blender Tool\`
  Esta ruta de instalación garantiza que el programa pueda actualizarse y ejecutarse de forma segura sin requerir permisos elevados.
* **Directorio de Datos del Usuario**: El archivo de configuración de perfiles, los logs y el archivo de base de datos SQLite se almacenan aislados en la carpeta de datos de aplicación roaming:
  `%APPDATA%\IP Blender Tool\`
  - Base de datos local: `%APPDATA%\IP Blender Tool\jobs.sqlite`
  - Archivo de log local: `%APPDATA%\IP Blender Tool\app.log`
* **Ejecución 100% Local**: La aplicación procesa los archivos `.blend` y lanza los renders localmente mediante subprocesos en la máquina del usuario. Los proyectos no se suben a ningún servidor y el archivo original de Blender no sufre modificaciones destructivas.

---

## 🌐 2. Notificaciones y Red (Telegram y Discord)

* **Desactivadas por Defecto**: Las notificaciones de Telegram y Discord están desactivadas por defecto al instalar la aplicación.
* **Sin Recopilación de Datos**: La aplicación no recopila telemetría ni sube capturas de renders, proyectos o logs a internet de forma automática.
* **Comunicación Directa**: Si el usuario activa manualmente las integraciones de Telegram o Discord en Ajustes, la aplicación enviará solicitudes HTTP directas desde su máquina a los endpoints de la API de Telegram y los Webhooks de Discord. No hay intermediarios ni servidores intermedios alojados por IP Blender Tool.

---

## 🛡️ 3. Anonimización de Datos en Diagnósticos (ZIP redacted)

La barra lateral de la aplicación incluye una función para **"Exportar ZIP de Diagnóstico"** para facilitar el soporte técnico. Para proteger los datos privados del usuario antes de compartir este archivo, el sistema aplica un filtrado y anonimización automáticos:

1. **Eliminación de Secretos**:
   - **Tokens de Telegram**: Se eliminan de la configuración exportada y se reemplazan por `[REDACTED_SECRET]`.
   - **IDs de Chat de Telegram**: Reemplazados por `[REDACTED_SECRET]`.
   - **Webhooks de Discord**: URLs completas reemplazadas por `[REDACTED_SECRET]`.
2. **Anonimización de Rutas del Sistema**:
   - El exportador inspecciona los logs y la configuración antes de empaquetar, buscando las rutas que contienen el nombre de usuario de Windows (por ejemplo, `C:\Users\juan_perez\...`) y reemplazándolo de forma genérica con variables del sistema (por ejemplo, `C:\Users\<USER>\...`).
3. **Control e Inclusión de la Base de Datos**:
   - **Por Defecto (Solo Esquema)**: De forma predeterminada, el ZIP de diagnóstico solo exporta la estructura SQL vacía de la base de datos para depurar problemas de diseño.
   - **Consentimiento del Usuario (Sanitizada)**: El archivo real `jobs.sqlite` solo se incluirá en el ZIP si el usuario activa de forma explícita la casilla **"Incluir base de datos (sanitizada)"** en la interfaz. Si se activa, se genera una copia temporal en la cual se anonimizan todas las rutas personales de proyectos, nombres de archivos de renders y sumarios de errores antes de adjuntarse al paquete comprimido.
