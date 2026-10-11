# -*- coding: utf-8 -*-
"""« Mes mots à retenir » : prénoms, lieux, mots rares que Whisper doit s'attendre à entendre.
Mesuré : avec ces mots dans la consigne, les mots rares sont bien mieux reconnus,
et une phrase qui n'en parle pas n'est pas modifiée."""
import os
import subprocess

from .config import DOSSIER

FICHIER = os.path.join(DOSSIER, "mes-mots.txt")
MAX_MOTS = 60          # la consigne de Whisper est limitée en longueur

EXPLICATION = """# MES MOTS À RETENIR
# Écris ici les mots que le canard reconnaît mal :
# prénoms, noms de famille, villes, marques, mots de ton métier...
# Un mot (ou un nom) par ligne. Puis enregistre (Ctrl + S) et ferme.
# Les lignes qui commencent par # sont ignorées.
#
# Exemples (enlève le # devant pour les utiliser) :
# Canard Dictée
# raclette
"""

_cache = {"date": None, "mots": []}


def creer_si_absent():
    if not os.path.exists(FICHIER):
        os.makedirs(DOSSIER, exist_ok=True)
        with open(FICHIER, "w", encoding="utf-8") as f:
            f.write(EXPLICATION)


def lire():
    """Les mots du fichier (relu seulement s'il a changé)."""
    try:
        date = os.path.getmtime(FICHIER)
    except OSError:
        return []
    if date != _cache["date"]:
        mots = []
        try:
            with open(FICHIER, encoding="utf-8-sig") as f:
                for ligne in f:
                    ligne = ligne.strip()
                    if ligne and not ligne.startswith("#") and ligne not in mots:
                        mots.append(ligne)
        except OSError:
            pass
        _cache.update(date=date, mots=mots[:MAX_MOTS])
    return _cache["mots"]


def consigne(base):
    mots = lire()
    if not mots:
        return base
    return base + " Mots à connaître : " + ", ".join(mots) + "."


def ouvrir():
    creer_si_absent()
    subprocess.Popen(["notepad.exe", FICHIER])
