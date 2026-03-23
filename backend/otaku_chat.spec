# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("app", include_py_files=False)
datas += [
    ("app/static", "app/static"),
    ("app/data", "app/data"),
]

hiddenimports = ["uvicorn", "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto", "uvicorn.protocols.http.auto"]

a = Analysis(
    ["run_desktop.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="OtakuChat",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)