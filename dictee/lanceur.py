# -*- coding: utf-8 -*-
"""Lanceur : détecte si le curseur est dans une zone de texte (UI Automation)."""
import logging
import os
import threading
import time

log = logging.getLogger("dictee")

# Fenêtres de navigateur : leur "document" n'est pas forcément modifiable.
CLASSES_NAVIGATEUR = ("Chrome_RenderWidgetHostHWND", "MozillaWindowClass")


def est_zone_de_texte(ctrl, auto):
    if ctrl is None or ctrl.ProcessId == os.getpid():
        return False
    type_ctrl = ctrl.ControlType
    if type_ctrl in (auto.ControlType.EditControl, auto.ControlType.ComboBoxControl):
        try:
            motif = ctrl.GetPattern(auto.PatternId.ValuePattern)
            if motif is not None and motif.IsReadOnly:
                return False
        except Exception:
            pass
        return type_ctrl == auto.ControlType.EditControl or bool(ctrl.IsKeyboardFocusable)
    if type_ctrl == auto.ControlType.DocumentControl:
        return ctrl.ClassName not in CLASSES_NAVIGATEUR
    return False


class Lanceur(threading.Thread):
    def __init__(self, sur_changement, intervalle=0.4):
        super().__init__(daemon=True)
        self.sur_changement = sur_changement
        self.intervalle = intervalle
        self.actif = False
        self._fin = threading.Event()

    def arreter(self):
        self._fin.set()

    def run(self):
        try:
            import uiautomation as auto
        except Exception as e:
            log.warning("UI Automation indisponible : %s", e)
            return
        precedent = None
        with auto.UIAutomationInitializerInThread():
            while not self._fin.is_set():
                if self.actif:
                    try:
                        dedans = est_zone_de_texte(auto.GetFocusedControl(), auto)
                    except Exception:
                        dedans = False
                    if dedans != precedent:
                        precedent = dedans
                        self.sur_changement(dedans)
                else:
                    precedent = None
                time.sleep(self.intervalle)
