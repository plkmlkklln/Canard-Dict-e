# -*- coding: utf-8 -*-
"""Teste la détection des costumes dans la vraie page du canard (barre.html)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtWebEngineCore import QWebEnginePage  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from dictee.ui import DOSSIER_WEB  # noqa: E402

CAS = [
    ("On commande des pizzas ce soir ?", "italie"),
    ("Vive la FRANCE et les croissants", "france"),
    ("Ça c'est un vrai mème mdr", "frog"),
    ("J'ai trouvé un trésor sur le bateau", "pirate"),
    ("Bonne fête ! Il y a un gâteau", "anniv"),
    ("Je suis trop fatiguée, il me faut un café", "cafe"),
    ("Je t'aime mon cœur", "amour"),
    ("J'ai reçu mon salaire, 2000 euros", "riche"),
    ("Le Père Noël arrive avec la neige", "noel"),
    ("La fusée va sur la Lune", "astro"),
    ("Ce soir il y a match de foot", "sport"),
    ("J'écoute ma playlist de rap", "musique"),
    ("Il pleut, je suis triste", "pluie"),
    ("Je fais du judo et du karaté", "ninja"),
    ("La police mène l'enquête", "detective"),
    ("Je suis malade, j'ai de la fièvre", "malade"),
    ("C'est un peu sexy tout ça", "cuir"),
    ("Règle 34 : il existe forcément", "cuir"),
    ("Des menottes et un fouet", "cuir"),
    ("C'est du XXX", "cuir"),
    # Les nouveaux costumes du design
    ("Le flocage du maillot est prêt", "flocage"),
    ("Joyeux Halloween, voici des bonbons !", "citrouille"),
    ("Cette maison est hantée par un fantôme", "fantome"),
    ("La sorcière prépare une potion magique", "sorciere"),
    ("C'est la marche des fiertés LGBT", "fierte"),
    ("J'ai regardé un film Ghibli, Totoro", "manga"),
    ("Un furry en fursuit de renard, uwu", "furry"),
    ("Je construis un château en Lego", "brique"),
    ("Iron Man met son armure", "armure"),
    ("Un vampire gothique dans les ténèbres", "goth"),
    ("Le président Trump à la Maison Blanche", "president"),
    ("On joue à Minecraft en 8 bits", "pixel"),
    ("J'ai regardé South Park, c'est un dessin animé", "cartoon"),
    # Le thème le plus présent gagne (2 mots sport contre 1 mot France).
    ("En France le match de foot", "sport"),
    # Pas de faux costumes sur des phrases normales
    ("Bonjour, je vous envoie le dossier demain matin.", None),
    ("Il a 34 ans et habite au numéro 34.", None),
    ("Le but de la réunion est simple.", None),
    ("Je t'appelle lundi.", None),
]


def main():
    app = QApplication(sys.argv)
    page = QWebEnginePage()
    resultats = []

    def fini(ok):
        code = "JSON.stringify(%s.map(t => { const m = trouverCostume(t); return m ? m.key : null; }))" \
               % json.dumps([c[0] for c in CAS], ensure_ascii=False)
        page.runJavaScript(code, 0, recu)

    def recu(texte):
        trouves = json.loads(texte)
        for (phrase, attendu), trouve in zip(CAS, trouves):
            ok = trouve == attendu
            resultats.append(ok)
            print(("OK   " if ok else "ECHEC"), f"{phrase!r} -> {trouve} (attendu {attendu})")
        app.quit()

    page.loadFinished.connect(fini)
    page.load(QUrl.fromLocalFile(os.path.join(DOSSIER_WEB, "barre.html")))
    app.exec()
    print(f"\n{sum(resultats)}/{len(CAS)} tests réussis")
    sys.exit(0 if resultats and all(resultats) else 1)


if __name__ == "__main__":
    main()
