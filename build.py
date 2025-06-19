#!/usr/bin/env python3
# build.py - Cross-platform build script for the MIDI REST API Integration app
import os
import sys
import platform
import shutil
import subprocess
import argparse
from pathlib import Path

# Import version information from central location
from version import VERSION as APP_VERSION
from version import APP_NAME, APP_DESCRIPTION, APP_AUTHOR
APP_ICON = "resources/icon"  # Will use .ico for Windows, .icns for macOS

# Define resource files to include
RESOURCE_FILES = [
    ("ui/style.qss", "ui"),
    ("launchpad-mini-demo.json", "."),
    ("launchpad-mini-demo-2.json", ".")
]

def ensure_pyinstaller_installed():
    """Check if PyInstaller is installed, and install it if not."""
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
        return True
    except ImportError:
        print("Installing PyInstaller...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                               check=False, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error installing PyInstaller: {result.stderr}")
            return False
        return True

def get_platform_options():
    """Get platform-specific PyInstaller options."""
    os_name = platform.system().lower()
    
    # Common options for all platforms
    options = {
        "name": APP_NAME,
        "excludes": ["tkinter", "matplotlib", "numpy", "scipy"],
        "clean": True,
        "noconfirm": True,
        "onefile": True,
        "windowed": True,  # Don't show console
        "add_data": [],
    }
    
    # Add resource files
    for src, dst in RESOURCE_FILES:
        if os.path.exists(src):
            path_sep = ";" if os_name == "windows" else ":"
            options["add_data"].append(f"{src}{path_sep}{dst}")
    
    # Platform-specific options
    if os_name == "windows":
        icon_path = f"{APP_ICON}.ico"
        if os.path.exists(icon_path):
            options["icon"] = icon_path
        options["target_name"] = f"{APP_NAME}.exe"
        options["version_info"] = {
            "fileversion": tuple(map(int, APP_VERSION.split("."))),
            "productversion": tuple(map(int, APP_VERSION.split("."))),
            "filedescription": APP_DESCRIPTION,
            "productname": APP_NAME,
            "companyname": APP_AUTHOR,
        }
    elif os_name == "darwin":  # macOS
        icon_path = f"{APP_ICON}.icns"
        if os.path.exists(icon_path):
            options["icon"] = icon_path
        options["target_name"] = APP_NAME
        options["target_arch"] = None  # Let PyInstaller determine architecture
        options["codesign_identity"] = None
        options["entitlements_file"] = None
    else:  # Linux
        icon_path = f"{APP_ICON}.png"
        if os.path.exists(icon_path):
            options["icon"] = icon_path
        options["target_name"] = APP_NAME.lower()
    
    return options, os_name

def create_spec_file(options, platform_name):
    """Create a PyInstaller spec file with the given options."""
    # Format the data entries for the spec file
    formatted_datas = []
    for data_entry in options['add_data']:
        # Each data_entry is in the format "src;dst" or "src:dst" depending on platform
        parts = data_entry.split(";" if platform_name == "windows" else ":")
        if len(parts) == 2:
            src, dst = parts
            formatted_datas.append(f"('{src}', '{dst}')")
    
    datas_str = "[" + ", ".join(formatted_datas) + "]"
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas={datas_str},
    hiddenimports=['PyQt6.sip', 'mido.backends.rtmidi'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={options['excludes']},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
"""

    if options.get("onefile", False):
        # Add icon parameter only if it exists
        icon_param = ""
        if "icon" in options and os.path.exists(options["icon"]):
            icon_param = f", icon='{options['icon']}'"
            
        spec_content += f"""
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{options["name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={not options.get('windowed', False)}{icon_param}
)
"""
    else:
        # Add icon parameter only if it exists
        icon_param = ""
        if "icon" in options and os.path.exists(options["icon"]):
            icon_param = f", icon='{options['icon']}'"
            
        spec_content += f"""
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{options["name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={not options.get('windowed', False)}{icon_param}
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{options["name"]}',
)
"""
    # Add macOS bundle for macOS builds
    if platform_name == "darwin":
        # Add icon parameter only if it exists
        icon_param = ""
        if "icon" in options and os.path.exists(options["icon"]):
            icon_param = f", icon='{options['icon']}'"
            
        spec_content += f"""
app = BUNDLE(
    coll,
    name='{options["name"]}.app'{icon_param},
    bundle_identifier=None,
    info_plist={{
        'CFBundleShortVersionString': '{APP_VERSION}',
        'CFBundleVersion': '{APP_VERSION}',
        'NSHighResolutionCapable': 'True',
    }},
)
"""

    spec_file = f"{options['name']}_{platform_name}.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    return spec_file

def build_executable(platform_name, spec_file):
    """Run PyInstaller to build the executable."""
    print(f"Building executable for {platform_name}...")
    
    cmd = [sys.executable, "-m", "PyInstaller", spec_file, "--noconfirm"]
    
    if platform_name == "darwin":
        cmd.append("--target-architecture=universal2")
    
    result = subprocess.run(cmd, check=False)
    
    if result.returncode != 0:
        print(f"Error building executable for {platform_name}")
        return False
    else:
        print(f"Successfully built executable for {platform_name}")
        return True

def setup_resources_directory():
    """Create a resources directory if it doesn't exist and ensure an icon is present."""
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    # Check for icon files or create placeholders
    icon_files = {
        "icon.ico": "Windows",
        "icon.icns": "macOS",
        "icon.png": "Linux"
    }
    
    for icon_file, platform_name in icon_files.items():
        icon_path = resources_dir / icon_file
        if not icon_path.exists():
            print(f"Note: No icon file found for {platform_name} at {icon_path}")
            print(f"      You may want to add an appropriate icon file at this location.")

def main():
    parser = argparse.ArgumentParser(description="Build executable for MIDI REST API Integration")
    parser.add_argument("--platform", choices=["windows", "macos", "linux", "all"], 
                        default=platform.system().lower(),
                        help="Target platform(s) to build for (default: current platform)")
    args = parser.parse_args()
    
    if args.platform == "macos":
        args.platform = "darwin"
    
    # Create resources directory if needed
    setup_resources_directory()
    
    # Check if PyInstaller is installed
    if not ensure_pyinstaller_installed():
        sys.exit(1)
    
    # Get current platform
    current_platform = platform.system().lower()
    
    # Determine target platforms
    if args.platform == "all":
        if current_platform == "windows":
            print("Warning: Building for macOS and Linux from Windows is not supported.")
            print("         Only the Windows executable will be built.")
            target_platforms = ["windows"]
        elif current_platform == "darwin":
            print("Warning: Building for Windows and Linux from macOS is not supported.")
            print("         Only the macOS executable will be built.")
            target_platforms = ["darwin"]
        else:  # Linux
            print("Warning: Building for Windows and macOS from Linux is not supported.")
            print("         Only the Linux executable will be built.")
            target_platforms = ["linux"]
    else:
        if args.platform != current_platform and args.platform != "linux" and current_platform == "linux":
            print(f"Error: Cannot build for {args.platform} from {current_platform}.")
            sys.exit(1)
        target_platforms = [args.platform]
    
    # Build for each target platform
    for platform_name in target_platforms:
        options, detected_platform = get_platform_options()
        
        # Override the detected platform with the target platform
        if platform_name != detected_platform:
            print(f"Warning: Building for {platform_name} on {detected_platform}.")
            print("         Cross-platform builds may not work correctly.")
        
        # Create spec file
        spec_file = create_spec_file(options, platform_name)
        
        # Build executable
        if build_executable(platform_name, spec_file):
            # Copy to output directory
            output_dir = os.path.join("dist", f"{APP_NAME}-{APP_VERSION}-{platform_name}")
            os.makedirs(output_dir, exist_ok=True)
            
            # Copy built files to output directory
            if platform_name == "darwin":  # macOS
                src = os.path.join("dist", f"{APP_NAME}.app")
                dst = os.path.join(output_dir, f"{APP_NAME}.app")
            else:  # Windows and Linux
                src = os.path.join("dist", options["target_name"])
                dst = os.path.join(output_dir, options["target_name"])
            
            if os.path.exists(src):
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy(src, dst)
                print(f"Copied build to {output_dir}")
            else:
                print(f"Warning: Could not find built executable at {src}")
    
    print("Build process completed.")

if __name__ == "__main__":
    main()
