# -*- coding: utf-8 -*-
"""Nettoyage du texte reconnu : phrases inventées, ponctuation, gros mots."""
import re

# Phrases que Whisper invente quand il n'entend que du silence ou du bruit.
PARASITES = (
    "amara.org",
    "sous-titres réalisés",
    "sous-titres realises",
    "sous-titres par",
    "sous-titres fait par",
    "sous-titres faits par",
    "sous-titrage st'",
    "sous-titrage st ",
    "sous-titrage société radio-canada",
    "sous-titrage france télévisions",
    "merci d'avoir regardé",
    "merci de nous avoir regardé",
    "abonnez-vous",
    "n'oubliez pas de vous abonner",
    "n'hésitez pas à vous abonner",
    "à la prochaine vidéo",
    "www.",
)

GROS_MOTS = (
    r"putains?", r"merdes?", r"merdique", r"connards?", r"connasses?", r"con(?:ne)?s?",
    r"salopes?", r"salauds?", r"encul[ée]e?s?", r"putes?", r"bites?", r"couilles?",
    r"niqu(?:e|er|é|ez|es)", r"foutre", r"chier", r"bordel", r"b[aâ]tards?",
    r"enfoir[ée]e?s?", r"p[ée]tasses?", r"pd", r"fdp", r"ntm", r"ta gueule",
)
_RE_GROS = re.compile(r"(?<!\w)(?:" + "|".join(GROS_MOTS) + r")(?!\w)", re.IGNORECASE)
_RE_PHRASES = re.compile(r"(?<=[.!?…])\s+")
_RE_PONCTUATION = re.compile(r"\s*[.,;:!?…«»\"“”]+\s*")


def _masquer(m):
    mot = m.group(0)
    return mot[0] + "".join("*" if c != " " else " " for c in mot[1:])


def nettoyer(texte, ponctuation=True, filtre=True):
    """Renvoie le texte prêt à écrire, ou "" s'il n'y a rien de valable."""
    t = " ".join((texte or "").split())
    phrases = [p for p in _RE_PHRASES.split(t)
               if not any(x in p.lower() for x in PARASITES)]
    t = " ".join(phrases).strip()
    if not re.search(r"\w", t):
        return ""
    if not ponctuation:
        t = " ".join(_RE_PONCTUATION.sub(" ", t).split())
    if filtre:
        t = _RE_GROS.sub(_masquer, t)
    return t
