# -*- mode: python ; coding: utf-8 -*-
# Recette PyInstaller. Lancer avec : python -m PyInstaller DicteeVocale.spec --noconfirm
import os

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

import nvidia.cublas

binaires = collect_dynamic_libs("ctranslate2")
# Carte NVIDIA : seules ces deux DLL servent (vérifié). Si absentes, l'appli marche sur le processeur.
dossier_cublas = os.path.join(list(nvidia.cublas.__path__)[0], "bin")
for nom in ("cublas64_12.dll", "cublasLt64_12.dll"):
    binaires.append((os.path.join(dossier_cublas, nom), "nvidia/cublas/bin"))

donnees = collect_data_files("faster_whisper") + collect_data_files("uiautomation")
donnees += collect_dynamic_libs("uiautomation")
donnees.append(("dictee/web", "dictee/web"))      # l'interface du canard (pages + polices)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaires,
    datas=donnees,
    hiddenimports=collect_submodules("pynput") + ["comtypes.stream", "comtypes.client",
                                                  "uiautomation"],
    excludes=["tkinter", "matplotlib", "PySide6.QtQuick3D", "PySide6.QtPdf",
              "PySide6.QtSql", "PySide6.QtTest", "PySide6.Qt3DCore", "PySide6.QtCharts",
              "PySide6.QtDataVisualization", "PySide6.QtMultimedia", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CanardDictee",
    console=False,
    icon="outils/icone.ico",
    version=None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="CanardDictee")
