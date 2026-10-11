# -*- coding: utf-8 -*-
"""Test de bout en bout : vraie appli, vraies touches simulées, vraie zone de texte.
Le micro est remplacé par la voix de synthèse française de Windows.
Les touches ne sont envoyées que si la fenêtre de test est au premier plan."""
import ctypes
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QLineEdit  # noqa: E402
from pynput import keyboard  # noqa: E402

from dictee import config  # noqa: E402
from tests.outils import dans_gui, preparer  # noqa: E402
from dictee.app import Application  # noqa: E402
from dictee.clavier import coller  # noqa: E402
from tests.test_reconnaissance import voix  # noqa: E402

PHRASE = "Le chat dort sur le canapé du salon."
user32 = ctypes.windll.user32


class FauxMicro:
    def __init__(self, son):
        self.son = son
        self.niveau = 0.0
        self.max_rms = 0.0
        self.dernier_son = 0.0
        self.demarrages = 0

    def demarrer(self, nom=None):
        self.demarrages += 1
        self.niveau, self.max_rms, self.dernier_son = 0.4, 0.2, time.time()
        self.actif = True

    def arreter(self):
        self.niveau = 0.0
        return self.son

    def ouvrir(self, nom=None):
        pass

    def fermer(self):
        pass


def main():
    qapp = QApplication(sys.argv)
    preparer()
    params = config.Parametres(os.path.join(tempfile.mkdtemp(), "p.json"))
    params.update(premier_lancement=False, modele="large-v3-turbo", delai=1)
    micro = FauxMicro(voix(PHRASE))
    appli = Application(qapp, params=params, enregistreur=micro)
    appli.barre.show()

    zone = QLineEdit()
    zone.setWindowTitle("Zone de test dictée")
    zone.resize(700, 50)
    zone.show()

    def premier_plan():
        return user32.GetForegroundWindow() == int(zone.winId())

    def coller_prudent(texte, raccourci):
        if premier_plan():
            coller(texte, raccourci)
        else:
            print("!! fenêtre de test pas au premier plan : collage sauté")
    appli.coller = coller_prudent

    clav = keyboard.Controller()
    resultats = []

    def attendre(cond, delai=30):
        fin = time.time() + delai
        while time.time() < fin:
            if cond():
                return True
            time.sleep(0.1)
        return False

    def verifier(nom, ok):
        resultats.append((nom, ok))
        print(("OK   " if ok else "ECHEC"), nom, flush=True)

    def scenario():
        assert attendre(lambda: appli.modele_pret, 120), "modèle pas prêt"
        dans_gui(lambda: (zone.activateWindow(), zone.raise_(), zone.setFocus()))
        time.sleep(1)
        if not premier_plan():
            # Astuce Windows pour autoriser une fenêtre à passer devant.
            clav.press(keyboard.Key.alt); clav.release(keyboard.Key.alt)
            user32.SetForegroundWindow(int(zone.winId()))
            time.sleep(0.5)
        if not premier_plan():
            print("Impossible de mettre la fenêtre de test devant : arrêt prudent.")
            dans_gui(qapp.quit)
            return

        # 1. Maintenir Ctrl droit 1,5 s puis relâcher -> le texte s'écrit.
        clav.press(keyboard.Key.ctrl_r); time.sleep(1.5)
        verifier("écoute pendant l'appui + annonce", appli.ecoute and appli.annonce)
        clav.release(keyboard.Key.ctrl_r)
        verifier("texte écrit (maintenir)", attendre(lambda: "canapé" in zone.text()))
        print("   ->", repr(zone.text()))
        verifier("bon texte", zone.text().strip() == PHRASE)

        # 2. Appui court -> mains libres ; 2e appui -> écrit.
        dans_gui(zone.clear); time.sleep(0.3)
        clav.press(keyboard.Key.ctrl_r); time.sleep(0.1); clav.release(keyboard.Key.ctrl_r)
        time.sleep(0.5)
        verifier("mains libres actif", appli.ecoute and appli.mains_libres and appli.annonce)
        clav.press(keyboard.Key.ctrl_r); time.sleep(0.1); clav.release(keyboard.Key.ctrl_r)
        verifier("texte écrit (mains libres)", attendre(lambda: "canapé" in zone.text()))

        # 3. Mains libres + silence -> s'arrête tout seul (délai = 1 s).
        dans_gui(zone.clear); time.sleep(0.3)
        clav.press(keyboard.Key.ctrl_r); time.sleep(0.1); clav.release(keyboard.Key.ctrl_r)
        micro.dernier_son = time.time() - 5
        verifier("arrêt auto après silence", attendre(lambda: not appli.ecoute, 5))
        attendre(lambda: "canapé" in zone.text())

        # 4. Ctrl droit + A (raccourci normal) -> pas de dictée.
        dans_gui(lambda: zone.setText("abc")); time.sleep(0.3)
        n = micro.demarrages
        clav.press(keyboard.Key.ctrl_r); time.sleep(0.05)
        clav.press("a"); clav.release("a")
        verifier("Ctrl+A annule la dictée", not appli.ecoute)
        time.sleep(0.6)
        clav.release(keyboard.Key.ctrl_r); time.sleep(1.5)
        verifier("rien écrit après Ctrl+A", zone.text() == "abc" and appli.occupe == 0)
        verifier("Ctrl+A a bien sélectionné", zone.selectedText() == "abc")

        # 5. Échap annule.
        dans_gui(lambda: zone.setText("")); time.sleep(0.3)
        clav.press(keyboard.Key.ctrl_r); time.sleep(0.1); clav.release(keyboard.Key.ctrl_r)
        time.sleep(0.4)
        clav.press(keyboard.Key.esc); clav.release(keyboard.Key.esc)
        time.sleep(1.5)
        verifier("Échap annule", not appli.ecoute and zone.text() == "")

        # 6. AltGr (é, @...) ne déclenche rien.
        clav.press(keyboard.Key.alt_gr); time.sleep(0.6); clav.release(keyboard.Key.alt_gr)
        verifier("AltGr ignoré", not appli.ecoute and micro.demarrages == n + 2)

        # 7. Presse-papiers restauré.
        import pyperclip
        verifier("presse-papiers restauré", pyperclip.paste() == "AVANT-TEST")

        # 8. Autre raccourci : F9.
        dans_gui(lambda: appli.regler("touche", "f9")); time.sleep(0.3)
        clav.press(keyboard.Key.f9); time.sleep(1.2); clav.release(keyboard.Key.f9)
        verifier("raccourci F9", attendre(lambda: "canapé" in zone.text()))
        dans_gui(qapp.quit)

    import pyperclip
    pyperclip.copy("AVANT-TEST")
    threading.Thread(target=scenario, daemon=True).start()
    qapp.exec()
    appli.raccourci.arreter()
    echecs = [n for n, ok in resultats if not ok]
    print(f"\n{len(resultats) - len(echecs)}/{len(resultats)} tests réussis")
    sys.exit(1 if echecs or not resultats else 0)


if __name__ == "__main__":
    main()
