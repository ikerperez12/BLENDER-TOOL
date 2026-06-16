# Troubleshooting Guide - IP Blender Tool

This document covers typical errors, explanation of root causes, and resolutions when running **IP Blender Tool**.

---

## 🔍 1. Blender / FFmpeg Not Found
### Symptom
- Project scanning fails with a popup error.
- Compiling video sequences fails, leaving only frame folders.

### Resolution
1. Open **⚙ Ajustes** in the top right.
2. Confirm the paths point to valid executables:
   - Blender: `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`
   - FFmpeg: `ffmpeg` (or select absolute path to `ffmpeg.exe` manually).
3. If using standard installations, click **Examinar...** to locate the `.exe` paths.

---

## 🔒 2. SQLite Database Locked (`database is locked`)
### Symptom
- Application freezes or outputs SQL lock warnings.

### Resolution
- The database is configured with **WAL** (Write-Ahead Logging) and a 5-second busy timeout to allow concurrent read/writes.
- If locked, check if multiple instances of `IP Blender Tool` are running simultaneously. Close background python threads via Task Manager or reboot.

---

## 🧠 3. GPU Out of Memory (`CUDA out of memory`)
### Symptom
- Render logs show `CUDA Error: Out of Memory` and the camera status is set to `Failed`.

### Resolution
- **Decrease resolution percentage**: Change the output resolution slider from `100%` to `50%` or use the **Borrador** profile.
- **Change Render Device**: Go to Settings (or in the scene file configuration) and change device to **CPU** to render using RAM instead of VRAM.

---

## ⚠️ 4. Missing Textures / Assets
### Symptom
- Project scan shows warning counts. Render output has purple textures or missing details.

### Resolution
- Open the `.blend` file in Blender UI, run `File -> External Data -> Report Missing Files` to locate them.
- If assets are moved, click `File -> External Data -> Find Missing Files` and select the folders to reload paths, then save the `.blend` file and re-scan in IP Blender Tool.

---

## 🔒 5. Permission Denied / No se puede escribir en carpeta
### Symptom
- Project scanning fails with access denied errors.
- Renders say `Failed` immediately and logs complain about permission issues writing output files.

### Resolution
- The application needs write access to the configured project root and renders directory. 
- Right-click the folder in Windows Explorer -> `Propiedades` -> `Seguridad` and ensure the current user has `Modificar` / `Escribir` permissions.
- Avoid setting projects root inside protected system directories like `C:\Program Files` or raw system drive root directories without admin privileges.

---

## 📂 6. Path Too Long (Windows MAX_PATH limitations)
### Symptom
- Render files are not saved, or scanner cannot find the `.blend` file even though it exists.
- Errors in logs mentioning `FileNotFoundError` with long filesystem paths.

### Resolution
- Windows has a default 260-character limit (`MAX_PATH`) for paths.
- Store your projects closer to the drive root (e.g. `C:\Proyectos\`) rather than deeply nested under many folders (e.g. `C:\Users\Username\Documents\Work\OldArchive\Projects\2026\ClientName\ProjectCode\...`).
- Alternatively, enable Windows Long Paths in the Windows Registry: set `LongPathsEnabled` to `1` under `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`.

---

## 🎥 7. Camera Not Found
### Symptom
- Render starts but fails immediately. The logs show: `Exception: Camera 'Camara A' not found in scene`.

### Resolution
- Re-scan the project within the IP Blender Tool interface.
- If you renamed or deleted the camera in the `.blend` file, the scanner needs to update its database snapshot.
- Make sure you save the `.blend` file in Blender before clicking "Re-escanear" or "Ingestar" in the tool.

---

## 🖼️ 8. Montage Image Not Replaced (Montaje)
### Symptom
- The camera renders successfully but the compositor step fails, or the final JPEG image contains the old/background image instead of the new render.

### Resolution
- Check if your Montage scene is configured properly in Blender. The compositor node setup must contain an Image Input node labeled exactly as configured (e.g., matching the compositor search logic or using active camera background).
- Ensure that the path configured for the montage `.blend` file in Settings matches a valid, readable `.blend` file that contains the rendering setup.
- Open the diagnostic package or look at the job log to see the specific Python exception thrown by `update_compositor.py`.

---

## 🛡️ 9. Installer Blocked by Windows SmartScreen / Antivirus
### Symptom
- Windows SmartScreen shows a blue warning: "Windows protegió su PC. Microsoft Defender SmartScreen evitó el inicio de una aplicación no reconocida..." when running the installer `.exe`.

### Resolution
- This is normal for newly compiled binaries that do not have a paid digital signature (Code Signing Certificate).
- Click **"Más información"** on the SmartScreen dialog, then click **"Ejecutar de todas formas"**.
- If your antivirus blocks it, add an exclusion rule for the installation directory (`%LOCALAPPDATA%\Programs\IP Blender Tool` or the folder you chose).

---

## ⚙️ 10. App Opens but Settings are Missing
### Symptom
- Every time you open the app, it runs the First-Run Wizard or defaults to empty settings.

### Resolution
- Check if your Windows user profile has access to `%APPDATA%` (usually `C:\Users\<Name>\AppData\Roaming`).
- IP Blender Tool writes its settings to `%APPDATA%\IP Blender Tool\settings.json`. If this folder is write-protected or resides on a read-only network drive, settings cannot be persisted.
- Check the collapsible Diagnostics panel in the UI to inspect the status of settings storage.

---

## 🔍 11. Render says Completed but File Not Found
### Symptom
- The job status turns `Completed` but no image file appears in the renders folder.

### Resolution
- IP Blender Tool v1.0.0 validates output files: if the file size is 0 bytes or doesn't exist, it marks the job as `Failed` rather than `Completed`.
- If this occurs, inspect the job logs (right-click the job and click "Ver Logs") to see if Blender had an internal error (such as missing libraries or python crashes) after rendering but before writing the file.

---

## 🛑 12. Blender Process Remains After Cancel
### Symptom
- You cancelled a render job in the queue, but your CPU/GPU utilization remains at 100% or you see multiple `blender.exe` processes in Task Manager.

### Resolution
- IP Blender Tool terminates the entire subprocess tree when a job is cancelled.
- If a process remains, it could be due to a Windows handle lock. You can safely close them from the Windows Task Manager (`Ctrl + Shift + Esc`), look for `blender` or `blender.exe` and select `Finalizar tarea`.
- Restarting the render queue from the UI will clean up queue states automatically.

