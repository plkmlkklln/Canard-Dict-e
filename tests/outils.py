# -*- coding: utf-8 -*-
"""Exécute une fonction dans le fil de l'interface (depuis un fil de test)."""
from PySide6.QtCore import QObject, Signal


class _Relais(QObject):
    executer = Signal(object)


_relais = None


def dans_gui(fonction):
    global _relais
    if _relais is None:
        raise RuntimeError("appeler preparer() dans le fil de l'interface d'abord")
    _relais.executer.emit(fonction)


def preparer():
    global _relais
    _relais = _Relais()
    _relais.executer.connect(lambda f: f())
