# -*- mode: python ; coding: utf-8 -*-
# اسپک PyInstaller برای ساخت gui.exe
# حالت onedir (پوشه‌ای) انتخاب شده تا اجرای پاپ‌آپ سریع باشد (بدون استخراج هر بار در حالت onefile).
# اجرا:  pyinstaller gui.spec

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    # فونت وزیر و آیکون همراه برنامه بسته‌بندی می‌شوند و در زمان اجرا از کنار exe خوانده می‌شوند
    datas=[('assets/Vazirmatn-Medium.ttf', 'assets'), ('assets/icon.ico', 'assets')],
    hiddenimports=['nh3'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
    name='gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # بدون پنجره‌ی کنسول (مثل pythonw)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='gui',
)
