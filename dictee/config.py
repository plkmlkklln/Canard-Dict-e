# -*- coding: utf-8 -*-
"""Paramètres de l'appli, enregistrés dans %APPDATA%\\DicteeVocale\\parametres.json."""
import json
import os
import sys

DOSSIER = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "DicteeVocale")
FICHIER = os.path.join(DOSSIER, "parametres.json")
NOM_DEMARRAGE = "DicteeVocale"
NOM_APPLI = "Canard Dictée"

DEFAUTS = {
    "lanceur": False,        # afficher la barre seulement dans une zone de texte
    "ponctuation": True,
    "filtre": True,          # filtrer le langage inadapté
    "sons": True,
    "delai": 1.5,            # secondes de silence avant d'arrêter (mains libres), 0 = jamais
    "costumes": True,        # le canard se déguise selon les mots dits
    "skin": None,            # costume permanent choisi dans « Skin du canard » (None = cow-boy)
    "micro": None,           # nom du micro, None = micro par défaut de Windows
    "touche": "ctrl_r",
    "win_h": True,           # Windows+H ouvre notre dictée (comme l'outil de Windows)
    "cacher": True,          # la barre disparaît quand la dictée est finie
    "modele": None,          # "rapide", "equilibre" ou "precis" ; None = choix auto
    "demarrage": False,
    "ancre": None,           # [x, y] du milieu du bas de la barre du canard
    "premier_lancement": True,
}


def dossier_appli():
    """Dossier de l'exe (version installée) ou du projet (version script)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Parametres(dict):
    def __init__(self, fichier=FICHIER):
        super().__init__(DEFAUTS)
        self.fichier = fichier
        try:
            with open(fichier, encoding="utf-8-sig") as f:   # accepte aussi un BOM
                lu = json.load(f)
            self.update({k: v for k, v in lu.items() if k in DEFAUTS})
        except Exception:
            pass

    def sauver(self):
        os.makedirs(os.path.dirname(self.fichier), exist_ok=True)
        tmp = self.fichier + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dict(self), f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.fichier)

    def regler(self, cle, valeur):
        self[cle] = valeur
        self.sauver()


def commande_demarrage():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --demarrage'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    script = os.path.join(dossier_appli(), "main.py")
    return f'"{pythonw}" "{script}" --demarrage'


def regler_demarrage_windows(actif):
    """Ajoute ou retire l'appli du démarrage de Windows (clé Run de l'utilisateur)."""
    import winreg
    cle = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                         winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
    with cle:
        if actif:
            winreg.SetValueEx(cle, NOM_DEMARRAGE, 0, winreg.REG_SZ, commande_demarrage())
        else:
            try:
                winreg.DeleteValue(cle, NOM_DEMARRAGE)
            except FileNotFoundError:
                pass


def demarrage_windows_actif():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run") as cle:
            winreg.QueryValueEx(cle, NOM_DEMARRAGE)
        return True
    except OSError:
        return False
