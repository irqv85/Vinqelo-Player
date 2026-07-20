from pathlib import Path
import os


project_root = Path(SPECPATH).parent
vlc_root = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "VideoLAN" / "VLC"

if not (vlc_root / "libvlc.dll").is_file():
    raise FileNotFoundError(f"No se encontró VLC de 64 bits en {vlc_root}")


a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[
        (str(vlc_root / "libvlc.dll"), "."),
        (str(vlc_root / "libvlccore.dll"), "."),
    ],
    datas=[
        (str(project_root / "assets"), "assets"),
        (str(project_root / "database" / "schema.sql"), "database"),
        (str(project_root / "LICENSE"), "."),
        (str(vlc_root / "plugins"), "plugins"),
    ],
    hiddenimports=[
        "vlc",
        "winrt.windows.foundation",
        "winrt.windows.media",
        "winrt.windows.media.interop",
        "winrt.windows.storage.streams",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "store_runtime.py")],
    excludes=["tkinter", "_tkinter"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Vinqelo Player",
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
    icon=[str(project_root / "assets" / "icons" / "vinqelo.ico")],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Vinqelo Player Store Clean",
)
