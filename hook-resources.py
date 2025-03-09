"""
PyInstaller hook to ensure Resources directory is properly created
"""

from PyInstaller.utils.hooks import collect_all

# This ensures Resources directory will be created in the bundle
datas = [
    ('icon.png', 'Resources'),
    ('icon.icns', 'Resources'),
]