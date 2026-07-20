# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('C:\\Program Files\\VideoLAN\\VLC\\libvlc.dll', '.'), ('C:\\Program Files\\VideoLAN\\VLC\\libvlccore.dll', '.')],
    datas=[('assets', 'assets'), ('database\\schema.sql', 'database'), ('LICENSE', '.'), ('C:\\Program Files\\VideoLAN\\VLC\\plugins', 'plugins')],
    hiddenimports=['vlc', 'winrt.windows.foundation', 'winrt.windows.media', 'winrt.windows.media.interop', 'winrt.windows.storage.streams'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
splash = Splash(
    'build\\vinqelo-splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    splash,
    splash.binaries,
    [],
    name='Vinqelo Player Portable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icons\\vinqelo.ico'],
)
