# -*- coding: utf-8 -*-
"""Fait parler la voix française de Windows, puis vérifie la reconnaissance.
Usage : python tests/test_reconnaissance.py [small|large-v3-turbo]"""
import os
import subprocess
import sys
import tempfile
import time
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dictee.moteur import Moteur  # noqa: E402
from dictee.texte import nettoyer  # noqa: E402

PHRASE = ("Bonjour, je m'appelle Pierre et j'habite à Lyon. "
          "Est-ce que tu viens manger demain soir avec nous ?")


def voix(texte):
    chemin = os.path.join(tempfile.gettempdir(), "dictee_test.wav")
    ps = ("Add-Type -AssemblyName System.Speech;"
          "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
          "$s.SelectVoice('Microsoft Hortense Desktop');"
          "$f=New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000,"
          "[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,"
          "[System.Speech.AudioFormat.AudioChannel]::Mono);"
          f"$s.SetOutputToWaveFile('{chemin}',$f);$s.Speak($env:TEXTE_TEST);$s.Dispose()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True,
                   env=dict(os.environ, TEXTE_TEST=texte))
    with wave.open(chemin) as w:
        donnees = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return donnees.astype(np.float32) / 32768


def main(nom):
    m = Moteur()
    t = time.time()
    appareil = m.charger({"small":"rapide","large-v3-turbo":"precis"}.get(nom,nom))
    print(f"Modèle {nom} chargé sur {appareil} en {time.time() - t:.1f} s")

    son = voix(PHRASE)
    t = time.time()
    brut = m.transcrire(son)
    print(f"Reconnu en {time.time() - t:.2f} s : {brut!r}")
    propre = nettoyer(brut)
    mots_attendus = ("bonjour", "pierre", "lyon", "demain", "soir")
    manquants = [x for x in mots_attendus if x not in propre.lower()]
    assert not manquants, f"mots manquants : {manquants}"
    assert propre[0].isupper() and "?" in propre and "," in propre, "ponctuation absente"

    # Silence pur et bruit léger : rien ne doit s'écrire.
    for nom_test, signal in (("silence", np.zeros(16000 * 3, np.float32)),
                             ("bruit", np.random.normal(0, 0.003, 16000 * 3).astype(np.float32))):
        r = nettoyer(m.transcrire(signal))
        print(f"{nom_test} -> {r!r}")
        assert r == "", f"texte inventé sur {nom_test}"
    print("OK reconnaissance")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "small")
