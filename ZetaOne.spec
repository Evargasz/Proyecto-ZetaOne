# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ZLauncher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('imagenes_iconos', 'imagenes_iconos'),
        ('json', 'json'),
        ('ODBC', 'ODBC')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=True, # Importante para que no aparezca la consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='imagenes_iconos\\Zeta99.ico' # Añade el ícono a tu ejecutable
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ZetaOne'
)