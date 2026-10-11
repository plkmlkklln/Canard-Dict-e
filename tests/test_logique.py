# -*- coding: utf-8 -*-
"""Teste la logique du raccourci SANS envoyer de touches au clavier :
les événements sont envoyés directement à l'appli, le collage est simulé."""
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication  # noqa: E402

from dictee import config  # noqa: E402
from tests.outils import dans_gui, preparer  # noqa: E402
from dictee.app import Application  # noqa: E402
from tests.test_appli import FauxMicro  # noqa: E402
from tests.test_reconnaissance import voix  # noqa: E402


class FauxMoteur:
    def charger(self, nom, sur_etape=None):
        return "cpu"

    def transcrire(self, audio, ponctuation=True):
        return "Le chat dort."


def main():
    qapp = QApplication(sys.argv)
    preparer()
    params = config.Parametres(os.path.join(tempfile.mkdtemp(), "p.json"))
    params.update(premier_lancement=False, modele="small", sons=False)
    micro = FauxMicro(voix("Bonjour"))
    appli = Application(qapp, params=params, enregistreur=micro, moteur=FauxMoteur(),
                        services=False)
    ecrits = []
    appli.coller = lambda texte, r: ecrits.append(texte)
    p = appli.pont
    resultats = []

    def verifier(nom, ok):
        resultats.append(ok)
        print(("OK   " if ok else "ECHEC"), nom, flush=True)

    def pause(s=0.4):
        time.sleep(s)

    def appui(duree, autre=False, echap=False):
        appli.raccourci.enfoncee = True
        p.appui.emit(time.time())
        pause(0.05)
        if autre:
            p.autre.emit()
        if echap:
            p.echap.emit()
        pause(duree)
        appli.raccourci.enfoncee = False
        p.relache.emit(time.time())
        pause()

    def scenario():
        while not appli.modele_pret:
            pause(0.1)
        appui(1.0)
        verifier("maintenir puis relâcher écrit", ecrits == ["Le chat dort. "])

        ecrits.clear()
        appui(0.6, autre=True)
        verifier("Ctrl droit + autre touche : rien", not appli.ecoute and ecrits == [])
        appui(0.05, autre=True)
        verifier("Ctrl droit + autre touche rapide : rien", not appli.ecoute and ecrits == [])

        appui(0.05)
        verifier("appui court = mains libres", appli.ecoute and appli.mains_libres)
        p.echap.emit()
        pause()
        verifier("Échap annule", not appli.ecoute and ecrits == [])

        appui(0.6, echap=True)
        verifier("Échap pendant l'appui annule", not appli.ecoute and ecrits == [])

        appui(0.05)
        appui(0.05)
        pause(0.5)
        verifier("2e appui finit le mains libres", not appli.ecoute and ecrits == ["Le chat dort. "])

        dans_gui(appli.clic_micro)
        pause()
        verifier("clic sur le micro = écoute", appli.ecoute and appli.mains_libres)
        dans_gui(appli.clic_micro)
        pause(0.5)
        verifier("2e clic écrit", not appli.ecoute and len(ecrits) == 2)

        # Windows+H : la barre apparaît, écoute tout de suite, puis s'en va.
        pause(3.5)
        verifier("barre cachée quand c'est fini", not appli.barre.isVisible())
        p.win_h.emit()
        pause()
        verifier("Windows+H : barre visible + écoute", appli.barre.isVisible()
                 and appli.ecoute and appli.mains_libres and appli.annonce)
        pause(0.6)
        p.win_h.emit()
        pause(0.5)
        verifier("Windows+H encore : écrit", not appli.ecoute and len(ecrits) == 3)
        pause(2.5)
        verifier("puis la barre disparaît", not appli.barre.isVisible())
        dans_gui(lambda: appli.regler("cacher", False))
        pause()
        verifier("option « cacher » désactivée : barre visible", appli.barre.isVisible())

        # Le filtre clavier : Windows+H est bloqué pour Windows, et lance la dictée.
        from dictee.clavier import Raccourci
        appels, bloques = [], []
        r = Raccourci("ctrl_r", None, None, None, None, lambda: appels.append(1))

        class FauxEcouteur:
            def suppress_event(self):
                bloques.append(1)

        class Ev:
            def __init__(self, vk, flags=0):
                self.vkCode, self.flags = vk, flags

        r._clavier = FauxEcouteur()
        r._filtre(0x100, Ev(0x5B))           # Windows enfoncée
        r._filtre(0x100, Ev(0x48))           # H
        r._filtre(0x100, Ev(0x48))           # répétition automatique de H
        r._filtre(0x101, Ev(0x48))           # H relâché
        r._filtre(0x101, Ev(0x5B))           # Windows relâchée
        verifier("Windows+H attrapé une seule fois", appels == [1] and len(bloques) == 3)
        r._filtre(0x100, Ev(0x48))
        r._filtre(0x101, Ev(0x48))           # H seul : on ne touche à rien
        verifier("H seul laissé tranquille", appels == [1] and len(bloques) == 3)
        r.remplacer_win_h = False
        r._filtre(0x100, Ev(0x5B))
        r._filtre(0x100, Ev(0x48))
        r._filtre(0x101, Ev(0x48))
        r._filtre(0x101, Ev(0x5B))
        verifier("option désactivée : Windows+H normal", appels == [1] and len(bloques) == 3)
        dans_gui(qapp.quit)

    threading.Thread(target=scenario, daemon=True).start()
    qapp.exec()
    print(f"\n{sum(resultats)}/{len(resultats)} tests réussis")
    sys.exit(0 if all(resultats) else 1)


if __name__ == "__main__":
    main()
