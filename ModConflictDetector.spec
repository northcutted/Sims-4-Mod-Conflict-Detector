# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path
from PIL import Image
import io
import site
from ttkthemes import themed_style

# Add the project directory to the path to ensure imports work correctly
root_dir = os.path.dirname(os.path.abspath('__file__'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Get ttkthemes package location for data files
themes_dir = os.path.join(site.getsitepackages()[0], 'ttkthemes', 'themes')

# Convert PNG to ICNS for macOS and ICO for Windows
icon_path = os.path.join(root_dir, 'icon.png')
icns_path = os.path.join(root_dir, 'icon.icns')
ico_path = os.path.join(root_dir, 'icon.ico')


if os.path.exists(icon_path):
    with Image.open(icon_path) as img:
        # Ensure image is square
        size = max(img.size)
        new_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        new_img.paste(img, ((size - img.size[0]) // 2, (size - img.size[1]) // 2))
        
        # Generate icons with required sizes
        icon_sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]
        icons = []
        for s in icon_sizes:
            scaled_img = new_img.resize(s, Image.Resampling.LANCZOS)
            icons.append(scaled_img)
        
        # Save as ICO for Windows
        icons[0].save(ico_path, format='ICO', append_images=icons[1:], sizes=icon_sizes)
        
        if sys.platform == 'darwin':
            # Add larger sizes for macOS
            mac_icons = icons + [
                new_img.resize((512, 512), Image.Resampling.LANCZOS),
                new_img.resize((1024, 1024), Image.Resampling.LANCZOS)
            ]
            # Save as ICNS
            mac_icons[0].save(icns_path, format='ICNS', append_images=mac_icons[1:])

# Use appropriate icon path for each platform
if sys.platform == 'darwin' and os.path.exists(icns_path):
    bundle_icon = icns_path
elif sys.platform == 'win32' and os.path.exists(ico_path):
    bundle_icon = ico_path
else:
    bundle_icon = icon_path

# Create Resources directory if it doesn't exist (for development)
resources_dir = os.path.join(root_dir, 'Resources')
if not os.path.exists(resources_dir):
    os.makedirs(resources_dir)
    # Also copy the icon file to the Resources directory
    from shutil import copy
    copy(icon_path, os.path.join(resources_dir, 'icon.png'))

# Define data files based on platform
data_files = [
    (themes_dir, 'ttkthemes/themes'),  # Include ttkthemes data
    (icon_path, '.'),  # Include icon in root
    (icon_path, 'Resources'),  # Include icon in Resources folder
]

# For macOS, include ICNS file
if sys.platform == 'darwin' and os.path.exists(icns_path):
    data_files.append((icns_path, 'Resources')) 
elif sys.platform == 'win32' and os.path.exists(ico_path):
    data_files.append((ico_path, '.'))  # Include ICO file for Windows

a = Analysis(
    ['mod_conflict_detector.py'],
    pathex=[root_dir],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        'package_parser', 
        'scanner',
        # 'conflict_detector',  # Add the new module
        # 'gui',  # Add the GUI module
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'ttkthemes'
    ],
    hookspath=[root_dir],  # Add our custom hooks directory
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Sims 4 Mod Conflict Detector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Changed to True to show output when run from command line
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=bundle_icon,  # Use icns for macOS, png for other platforms
)

# For macOS, create an app bundle with the proper icon
app = BUNDLE(
    exe,
    name='Sims 4 Mod Conflict Detector.app',
    icon=bundle_icon,
    bundle_identifier='com.sims4modconflictdetector',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'CFBundleDisplayName': 'Sims 4 Mod Conflict Detector',
        'CFBundleName': 'Sims 4 Mod Conflict Detector',
        'CFBundleIdentifier': 'com.sims4modconflictdetector',
        'CFBundlePackageType': 'APPL',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundleExecutable': 'Sims 4 Mod Conflict Detector',
        'LSMinimumSystemVersion': '10.13.0',
        'CFBundleIconFile': os.path.basename(bundle_icon),
        'NSHighResolutionCapable': 'True',
        'NSAppleEventsUsageDescription': 'This app requires access to run properly.',
        'NSRequiresAquaSystemAppearance': 'No',
    }
)
