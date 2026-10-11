# -*- coding: utf-8 -*-
"""Photos de l'interface (barre, paramètres, aide, écoute, costume, assistant).
N'envoie aucune touche. Usage : python -m tests.apercu_canard <dossier_sortie>"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from dictee import config  # noqa: E402
from dictee.app import Application, Assistant  # noqa: E402
from tests.test_appli import FauxMicro  # noqa: E402
from tests.test_logique import FauxMoteur  # noqa: E402

import numpy as np  # noqa: E402

SORTIE = sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir()


def photo(fenetre, nom):
    g = fenetre.frameGeometry()
    img = QGuiApplication.primaryScreen().grabWindow(0, g.x(), g.y(), g.width(), g.height())
    img.save(os.path.join(SORTIE, nom + ".png"))
    print("photo", nom, g.width(), "x", g.height(), flush=True)


def main():
    qapp = QApplication(sys.argv)
    params = config.Parametres(os.path.join(tempfile.mkdtemp(), "p.json"))
    params.update(premier_lancement=False, sons=False, cacher=False)
    micro = FauxMicro(np.zeros(16000, np.float32))
    appli = Application(qapp, params=params, enregistreur=micro, moteur=FauxMoteur(),
                        services=False)
    appli.barre.show()
    b = appli.barre
    etapes = [
        (2500, lambda: photo(b, "1_barre")),
        (100, lambda: b.evenement("panneau")),
        (900, lambda: photo(b, "2_parametres")),
        (100, lambda: b.page().runJavaScript("S.sub='modele'; rendre();")),
        (700, lambda: photo(b, "3_sous_menu")),
        (100, lambda: b.evenement("aide")),
        (900, lambda: photo(b, "4_aide")),
        (100, lambda: b.evenement("fermer")),
        (100, appli.clic_micro),
        (1200, lambda: photo(b, "5_ecoute")),
        (100, appli.clic_micro),
        (1500, lambda: b.evenement("texte", "On mange une pizza ce soir ?")),
        (1300, lambda: photo(b, "6_costume_pizza")),
        (100, lambda: b.evenement("texte", "Je suis malade, j'ai de la fièvre.")),
        (1300, lambda: photo(b, "7_costume_malade")),
        (100, lambda: b.evenement("pleurer")),
        (1000, lambda: photo(b, "8_pleure")),
        (100, lambda: garde.update(a=Assistant(qapp, params, micro, FauxMoteur(), lambda l: None))),
        (1500, lambda: photo(garde["a"].fenetre, "9_assistant")),
        (100, lambda: garde["a"].fenetre.page().runJavaScript("aller(1)")),
        (800, lambda: photo(garde["a"].fenetre, "10_assistant_options")),
        (100, lambda: garde["a"].fenetre.page().runJavaScript("aller(2)")),
        (800, lambda: photo(garde["a"].fenetre, "11_assistant_micro")),
        (100, qapp.quit),
    ]
    garde = {}
    t = 0
    for delai, f in etapes:
        t += delai
        QTimer.singleShot(t, f)
    qapp.exec()


if __name__ == "__main__":
    main()
