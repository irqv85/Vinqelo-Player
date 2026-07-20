# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('C:\\Program Files\\VideoLAN\\VLC\\libvlc.dll', '.'),
        ('C:\\Program Files\\VideoLAN\\VLC\\libvlccore.dll', '.'),
    ],
    datas=[
        ('assets', 'assets'),
        ('database\\schema.sql', 'database'),
        ('LICENSE', '.'),
        ('C:\\Program Files\\VideoLAN\\VLC\\plugins', 'plugins'),
    ],
    hiddenimports=[
        'vlc',
        'winrt.windows.foundation',
        'winrt.windows.media',
        'winrt.windows.media.interop',
        'winrt.windows.storage.streams',
    ],
    runtime_hooks=['packaging\\store_runtime.py'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
splash = Splash(
    'assets\\icons\\vinqelo-logo.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    minify_script=True,
    always_on_top=True,
)
exe = EXE(
    pyz,
    a.scripts,
    splash,
    splash.binaries,
    [],
    exclude_binaries=True,
    name='Vinqelo Player',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=['assets\\icons\\vinqelo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Vinqelo Player Store',
)
