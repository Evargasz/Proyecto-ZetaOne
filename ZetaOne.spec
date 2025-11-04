# -*- mode: python ; coding: utf-8 -*-

# --- CORRECCIÓN: Definir la variable block_cipher ---
block_cipher = None

a = Analysis(
    ['Zlauncher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('imagenes_iconos', 'imagenes_iconos'),
        ('json', 'json')
    ],
    # --- CORRECCIÓN: Limpiar la línea de hiddenimports ---
    hiddenimports=['ttkbootstrap'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ZetaOne',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='imagenes_iconos\\Zeta99.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ZetaOne',
)
