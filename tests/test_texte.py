# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dictee.texte import nettoyer  # noqa: E402


def test_parasites():
    assert nettoyer("Sous-titres réalisés par la communauté d'Amara.org") == ""
    assert nettoyer("Merci d'avoir regardé cette vidéo !") == ""
    assert nettoyer("Bonjour à tous. Sous-titres réalisés par Amara.org") == "Bonjour à tous."
    assert nettoyer("...") == ""
    assert nettoyer("  ") == ""


def test_ponctuation():
    assert nettoyer("Bonjour, ça va ? Oui.", ponctuation=True) == "Bonjour, ça va ? Oui."
    assert nettoyer("Bonjour, ça va ? Oui.", ponctuation=False) == "Bonjour ça va Oui"
    assert nettoyer("Aujourd'hui, c'est l'été.", ponctuation=False) == "Aujourd'hui c'est l'été"


def test_gros_mots():
    assert nettoyer("Putain, c'est génial.") == "P*****, c'est génial."
    assert nettoyer("Putain, c'est génial.", filtre=False) == "Putain, c'est génial."
    assert nettoyer("Il est con.") == "Il est c**."
    # pas de faux positifs dans des mots normaux
    assert nettoyer("Le concert de Concarneau, connaître.") == "Le concert de Concarneau, connaître."
    assert nettoyer("Une bitte d'amarrage ? Non, un habitant.") == "Une bitte d'amarrage ? Non, un habitant."


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f()
            print("OK", nom)
