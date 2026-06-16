import os
import subprocess
import sys
import shutil
import hashlib

VERSION = "1.0.0-rc2"

def find_iscc():
    """Tries to find the Inno Setup compiler (ISCC.exe)."""
    # 1. Check if 'iscc' is in the system PATH
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(["iscc", "/?"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        return "iscc"
    except Exception:
        pass

    # 2. Check common installation directories on Windows (system and user scopes)
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    paths = [
        os.path.join(local_appdata, r"Programs\Inno Setup 6\ISCC.exe") if local_appdata else "",
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    for p in paths:
        if p and os.path.exists(p):
            return p
            
    return None

def clean_previous_builds():
    """Deletes build, dist, and releases folders for a clean build."""
    print("Limpiando directorios de compilación anteriores...")
    dirs_to_clean = ["build", "dist", "releases"]
    for d in dirs_to_clean:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"  Carpeta eliminada: {d}")
            except Exception as e:
                print(f"  Advertencia: No se pudo eliminar la carpeta {d}: {e}")

def run_verification():
    """Runs pre-flight verification script verify.py."""
    print("Ejecutando verificación pre-compilación...")
    try:
        subprocess.run([sys.executable, "verify.py"], check=True)
        print("SUCCESS: Verificación pre-compilación aprobada.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Falló la verificación de verify.py: {e}")
        return False

def verify_bundle():
    """Verifies that the compiled dist bundle has all necessary files."""
    print("Verificando empaquetado de scripts de Blender...")
    check_paths = [
        os.path.join("dist", "IPBlenderTool", "_internal", "blender_scripts", "scan_scene.py"),
        os.path.join("dist", "IPBlenderTool", "_internal", "blender_scripts", "render_camera.py"),
        os.path.join("dist", "IPBlenderTool", "_internal", "blender_scripts", "update_compositor.py"),
    ]
    all_ok = True
    for p in check_paths:
        if os.path.exists(p):
            print(f"  [OK] Empaquetado: {p}")
        else:
            print(f"  [ERROR] Faltante en bundle: {p}")
            all_ok = False
    return all_ok

def generate_checksum(file_path):
    """Calculates SHA256 checksum for a file and writes a .sha256 file next to it."""
    print(f"Generando checksum SHA256 para {file_path}...")
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()
        checksum_file = f"{file_path}.sha256"
        with open(checksum_file, "w", encoding="utf-8") as f:
            f.write(f"{checksum} *{os.path.basename(file_path)}\n")
        print(f"SUCCESS: Checksum generado en: {checksum_file} ({checksum})")
        return checksum_file
    except Exception as e:
        print(f"ERROR: No se pudo generar el checksum: {e}")
        return None

def organize_release():
    """Organizes compiled outputs into releases/[version]/ folder."""
    print(f"Organizando archivos de lanzamiento en releases/{VERSION}/...")
    src_installer = os.path.join("releases", f"IP-Blender-Tool-Setup-{VERSION}.exe")
    if not os.path.exists(src_installer):
        print(f"ERROR: No se encontró el instalador en: {src_installer}")
        return False
        
    dest_dir = os.path.join("releases", VERSION)
    os.makedirs(dest_dir, exist_ok=True)
    
    # 1. Move Installer
    dest_installer = os.path.join(dest_dir, f"IP-Blender-Tool-Setup-{VERSION}.exe")
    try:
        shutil.move(src_installer, dest_installer)
        print(f"  Instalador movido a: {dest_installer}")
    except Exception as e:
        print(f"ERROR: No se pudo mover el instalador: {e}")
        return False
        
    # 2. Generate and Move Checksum
    checksum_file = generate_checksum(dest_installer)
    
    # 3. Copy CHANGELOG.md / Release Notes
    changelog_src = "CHANGELOG.md"
    if os.path.exists(changelog_src):
        try:
            shutil.copy(changelog_src, os.path.join(dest_dir, "CHANGELOG.md"))
            print("  CHANGELOG.md copiado a la carpeta de release.")
        except Exception as e:
            print(f"  Advertencia: No se pudo copiar CHANGELOG.md: {e}")
            
    notes_src = os.path.join("release_notes", "v1.0.0.md")
    if os.path.exists(notes_src):
        try:
            shutil.copy(notes_src, os.path.join(dest_dir, f"release_notes_v{VERSION}.md"))
            print(f"  Notas de lanzamiento copiadas a la carpeta de release como release_notes_v{VERSION}.md.")
        except Exception as e:
            print(f"  Advertencia: No se pudo copiar notas de lanzamiento: {e}")
            
    print(f"SUCCESS: Carpeta de release {VERSION} organizada con éxito.")
    return True

def main():
    print("=== INICIANDO PROCESO DE COMPILACIÓN DE PRODUCCIÓN ===")
    
    # Step 1: Clean previous builds
    clean_previous_builds()
    
    # Step 2: Run pre-compilation verify tests
    if not run_verification():
        print("ERROR: La compilación se detuvo porque fallaron los tests de verificación.")
        sys.exit(1)
        
    # Step 3: Run PyInstaller
    print("\n[Paso 3] Ejecutando PyInstaller para crear bundle onedir...")
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "IPBlenderTool.spec"], check=True)
        print("SUCCESS: PyInstaller finalizado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Error al ejecutar PyInstaller: {e}")
        sys.exit(1)
        
    # Step 4: Verify scripts in bundle
    if not verify_bundle():
        print("ERROR: La compilación se detuvo porque faltan scripts internos en el bundle.")
        sys.exit(1)
        
    # Step 5: Locate Inno Setup and build installer
    print("\n[Paso 5] Buscando Inno Setup Compiler (ISCC.exe)...")
    iscc_path = find_iscc()
    if not iscc_path:
        print("ERROR: No se pudo localizar ISCC.exe. Inno Setup debe estar instalado.")
        sys.exit(1)
        
    print(f"SUCCESS: Compilador Inno Setup encontrado en: {iscc_path}")
    print("Ejecutando compilación del instalador...")
    
    iss_file = os.path.join("installer", "ip_blender_tool.iss")
    try:
        # Create output directory for setup before building
        os.makedirs("releases", exist_ok=True)
        subprocess.run([iscc_path, iss_file], check=True)
        print("SUCCESS: Instalador compilado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Error al ejecutar Inno Setup Compiler: {e}")
        sys.exit(1)
        
    # Step 6: Organize release folder and calculate checksum
    if not organize_release():
        print("ERROR: No se pudo organizar el directorio de releases.")
        sys.exit(1)
        
    print("\n=== PROCESO DE COMPILACIÓN COMPLETADO SATISFACTORIAMENTE ===")

if __name__ == "__main__":
    main()
