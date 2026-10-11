# -*- coding: utf-8 -*-
"""Le détecteur de fin de parole : une voix compte, un bruit de fond (souffle) ne compte pas."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np  # noqa: E402

from dictee.audio import BLOC, Enregistreur  # noqa: E402
from tests.test_reconnaissance import voix  # noqa: E402


def nourrir(rec, signal):
    """Envoie le son morceau par morceau, comme le micro, en vérifiant au fil de l'eau."""
    for i in range(0, len(signal) - BLOC + 1, BLOC):
        rec._rappel(signal[i:i + BLOC].reshape(-1, 1), BLOC, None, None)
        if (i // BLOC) % 3 == 0:
            rec.surveiller()


def main():
    rec = Enregistreur()
    assert rec.charger_vad(), "détecteur de voix absent"
    ok = True

    def verifier(nom, cond):
        nonlocal ok
        ok &= cond
        print(("OK   " if cond else "ECHEC"), nom)

    rng = np.random.default_rng(1)
    souffle = lambda s, niv: rng.normal(0, niv, int(16000 * s)).astype(np.float32)

    # 1. Bruit de fond fort (casque qui souffle, ventilateur) : pas une voix.
    rec.capture = True
    rec.dernier_son = 0.0
    nourrir(rec, souffle(2, 0.02))
    verifier("souffle fort ignoré", not rec.a_parle and rec.dernier_son == 0.0)

    # 2. Une voix : détectée.
    parole = voix("Bonjour, je teste la dictée du canard.")
    nourrir(rec, parole + souffle(len(parole) / 16000, 0.005))
    verifier("voix détectée", rec.a_parle and time.time() - rec.dernier_son < 1)

    # 3. Après la voix, du silence avec souffle : plus de voix détectée.
    t = rec.dernier_son
    time.sleep(0.05)
    nourrir(rec, souffle(1.5, 0.02))
    verifier("silence après la voix : rien de nouveau", rec.dernier_son - t < 0.5)
    print("\nOK détection de silence" if ok else "\nECHEC")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
