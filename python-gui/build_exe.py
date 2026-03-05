"""
Build script to create a standalone .exe for M2CIDSmile Tool.
Run this from the python-gui/ directory:
    python build_exe.py
"""

import os
import sys
import subprocess
import shutil

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Find customtkinter path
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)

    # Find certifi CA bundle for SSL
    certifi_ca = None
    try:
        import certifi
        certifi_ca = certifi.where()
        certifi_dir = os.path.dirname(certifi.__file__)
    except ImportError:
        print("  WARNING: certifi not installed. Installing it...")
        subprocess.run([sys.executable, "-m", "pip", "install", "certifi"], check=True)
        import certifi
        certifi_ca = certifi.where()
        certifi_dir = os.path.dirname(certifi.__file__)

    print("=" * 55)
    print("  M2CIDSmile Tool — EXE Builder")
    print("=" * 55)
    print(f"  CustomTkinter: {ctk_path}")
    print(f"  Certifi CA:    {certifi_ca}")
    print(f"  Source:         {script_dir}")
    print()

    # Clean previous builds
    for folder in ["build", "dist"]:
        path = os.path.join(script_dir, folder)
        if os.path.exists(path):
            print(f"  Cleaning {folder}/...")
            shutil.rmtree(path)

    spec_file = os.path.join(script_dir, "M2CIDSmile.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # Build with PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",                        # Single .exe file
        "--windowed",                       # No console window
        "--name", "M2CIDSmile",             # Output name
        "--icon", os.path.join(script_dir, "app_icon.ico"),
        # Bundle the icon file so the GUI window can use it too
        "--add-data", os.path.join(script_dir, "app_icon.ico") + ";.",
        # Bundle customtkinter assets (themes, fonts, etc.)
        "--add-data", f"{ctk_path};customtkinter",
        # Bundle certifi CA certificates for SSL on any Windows PC
        "--add-data", f"{certifi_dir};certifi",
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "customtkinter",
        "--hidden-import", "darkdetect",
        "--hidden-import", "certifi",
        "--hidden-import", "packaging",
        "--hidden-import", "packaging.version",
        "--hidden-import", "packaging.specifiers",
        "--hidden-import", "packaging.requirements",
        # Collect all customtkinter + certifi submodules
        "--collect-all", "customtkinter",
        "--collect-all", "certifi",
        # The main script
        "m2cidsmile_gui.py",
    ]

    print("  Building .exe (this may take 1-3 minutes)...")
    print()
    print("  Command:", " ".join(cmd[2:]))
    print()

    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode != 0:
        print("\n  ERROR: Build failed!")
        sys.exit(1)

    # Check output
    exe_path = os.path.join(script_dir, "dist", "M2CIDSmile.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print()
        print("=" * 55)
        print(f"  SUCCESS! Built: dist/M2CIDSmile.exe")
        print(f"  Size: {size_mb:.1f} MB")
        print()
        print(f"  Full path: {exe_path}")
        print("=" * 55)
        print()
        print("  You can distribute this .exe to any Windows PC.")
        print("  No Python installation required!")
        print()
        print("  Bundled components:")
        print("    - Python runtime")
        print("    - CustomTkinter (GUI framework)")
        print("    - SSL certificates (certifi)")
        print("    - All required dependencies")
    else:
        print("\n  ERROR: .exe not found after build!")
        sys.exit(1)


if __name__ == "__main__":
    main()
