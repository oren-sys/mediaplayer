# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('libmpv-2.dll', '.'),
        ('d3dcompiler_43.dll', '.'),
    ],
    datas=[
        ('assets/styles/dark.qss', 'assets/styles'),
        ('assets/icons', 'assets/icons'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'shiboken6',
        'src.paths',
        'src.app',
        'src.db.database',
        'src.db.models',
        'src.player.mpv_widget',
        'src.player.controls',
        'src.player.player_window',
        'src.library.scanner',
        'src.library.identifier',
        'src.library.watcher',
        'src.metadata.tmdb_client',
        'src.metadata.filename_parser',
        'src.subtitles.opensubtitles',
        'src.ui.main_window',
        'src.ui.library_view',
        'src.ui.detail_view',
        'src.ui.settings_dialog',
        'src.ui.widgets.sidebar',
        'src.ui.widgets.video_card',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['backports.zstd'],
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
    name='MediaPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MediaPlayer',
)
