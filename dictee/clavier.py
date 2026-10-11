# -*- coding: utf-8 -*-
"""Raccourci clavier global et écriture du texte (par le presse-papiers)."""
import time

import pyperclip
from pynput import keyboard, mouse

Key = keyboard.Key

# Touches proposées. Pas AltGr : elle sert sur le clavier AZERTY.
TOUCHES = {
    "ctrl_r": "Ctrl droit",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "insert": "Inser",
    "pause": "Pause",
    "scroll_lock": "Arrêt défil",
    "menu": "Touche Menu",
}


def nom_touche(code):
    return TOUCHES.get(code, code)


VK_H, VK_LWIN, VK_RWIN = 0x48, 0x5B, 0x5C
VK_MASQUE = 0xE8      # touche "vide" : empêche le menu Démarrer de s'ouvrir
DEPUIS_PROGRAMME = 0x10   # drapeau Windows : touche simulée par un programme


def _masquer_touche_windows():
    """Après avoir bloqué Windows+H, on envoie une touche vide. Sinon Windows croit
    qu'on a appuyé sur Windows tout seul et ouvre le menu Démarrer au relâchement."""
    import ctypes
    ctypes.windll.user32.keybd_event(VK_MASQUE, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_MASQUE, 0, 2, 0)


class Raccourci:
    """Surveille le clavier. Appelle les fonctions données (depuis un autre fil)."""

    def __init__(self, code, sur_appui, sur_relache, sur_autre, sur_echap, sur_win_h=None):
        self.regler(code)
        self.sur_appui = sur_appui
        self.sur_relache = sur_relache
        self.sur_autre = sur_autre
        self.sur_echap = sur_echap
        self.sur_win_h = sur_win_h
        self.remplacer_win_h = True   # Windows+H ouvre notre dictée au lieu de celle de Windows
        self.enfoncee = False
        self.ignorer = False          # vrai pendant qu'on colle le texte nous-mêmes
        self._win = False
        self._h_bas = False
        self._clavier = None
        self._souris = None

    def regler(self, code):
        self.code = code
        self.touche = getattr(Key, code, Key.ctrl_r)

    def _filtre(self, msg, data):
        """Voit chaque touche AVANT Windows : permet d'attraper Windows+H."""
        if data.flags & DEPUIS_PROGRAMME:
            return True
        bas = msg in (0x100, 0x104)          # WM_KEYDOWN, WM_SYSKEYDOWN
        if data.vkCode in (VK_LWIN, VK_RWIN):
            self._win = bas
        elif data.vkCode == VK_H and self.remplacer_win_h and self.sur_win_h and (
                self._win or self._h_bas):
            if bas and not self._h_bas:
                self._h_bas = True
                _masquer_touche_windows()
                self.sur_win_h()
            elif not bas:
                self._h_bas = False
            self._clavier.suppress_event()   # Windows ne voit pas ce H
        return True

    def demarrer(self):
        self._clavier = keyboard.Listener(on_press=self._appui, on_release=self._relache,
                                          win32_event_filter=self._filtre)
        self._souris = mouse.Listener(on_click=self._clic)
        self._clavier.start()
        self._souris.start()

    def arreter(self):
        for e in (self._clavier, self._souris):
            if e is not None:
                e.stop()

    def _appui(self, touche, *_):
        if self.ignorer:
            return
        if touche == self.touche:
            if not self.enfoncee:          # pas la répétition automatique
                self.enfoncee = True
                self.sur_appui(time.time())
            return
        if touche == Key.esc:
            self.sur_echap()
        elif self.enfoncee:
            self.sur_autre()               # ex. Ctrl droit + C : raccourci normal

    def _relache(self, touche, *_):
        if self.ignorer:
            return
        if touche == self.touche and self.enfoncee:
            self.enfoncee = False
            self.sur_relache(time.time())

    def _clic(self, x, y, bouton, presse, *_):
        if presse and self.enfoncee:
            self.sur_autre()               # ex. Ctrl + clic


def coller(texte, raccourci=None):
    """Écrit le texte là où est le curseur, puis remet l'ancien presse-papiers."""
    try:
        ancien = pyperclip.paste()
    except Exception:
        ancien = None
    for _ in range(5):
        try:
            pyperclip.copy(texte)
            break
        except Exception:
            time.sleep(0.05)
    time.sleep(0.05)
    controle = keyboard.Controller()
    if raccourci is not None:
        raccourci.ignorer = True
    try:
        with controle.pressed(Key.ctrl):
            controle.press("v")
            controle.release("v")
    finally:
        time.sleep(0.05)
        if raccourci is not None:
            raccourci.ignorer = False
    time.sleep(0.4)   # laisse l'appli lire le presse-papiers
    if ancien is not None:
        try:
            if pyperclip.paste() == texte:
                pyperclip.copy(ancien)
        except Exception:
            pass
