# -*- coding: utf-8 -*-
"""Micro (enregistrement) et petits sons."""
import collections
import io
import threading
import time
import wave

import numpy as np
import sounddevice as sd

try:
    import winsound
except ImportError:  # hors Windows
    winsound = None

FREQ = 16000


# ----------------------------------------------------------------- sons
def _fabriquer_son(notes, volume=0.22):
    sr = 44100
    parties = []
    for freq, ms in notes:
        n = int(sr * ms / 1000)
        t = np.arange(n) / sr
        enveloppe = np.minimum(1.0, np.minimum(t / 0.006, (n / sr - t) / 0.025))
        parties.append(np.sin(2 * np.pi * freq * t) * enveloppe * volume)
    donnees = (np.concatenate(parties) * 32767).astype("<i2")
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(donnees.tobytes())
    return tampon.getvalue()


SON_DEBUT = _fabriquer_son([(660, 60), (990, 90)])
SON_FIN = _fabriquer_son([(990, 60), (660, 90)])
SON_ANNULE = _fabriquer_son([(420, 140)])


def jouer(son):
    if winsound is None:
        return
    # SND_MEMORY ne marche pas en asynchrone : on joue dans un petit fil.
    threading.Thread(target=winsound.PlaySound,
                     args=(son, winsound.SND_MEMORY | winsound.SND_NODEFAULT),
                     daemon=True).start()


# ----------------------------------------------------------------- micros
def _api_wasapi():
    for i, h in enumerate(sd.query_hostapis()):
        if "WASAPI" in h["name"]:
            return i
    return None


def lister_micros():
    """Liste des noms de micros (sans doublons)."""
    api = _api_wasapi()
    noms = []
    for d in sd.query_devices():
        if d["max_input_channels"] > 0 and (api is None or d["hostapi"] == api):
            if d["name"] not in noms:
                noms.append(d["name"])
    return noms


def _trouver(nom):
    """Index du micro portant ce nom (WASAPI de préférence), sinon None."""
    if not nom:
        return None
    api = _api_wasapi()
    candidats = [i for i, d in enumerate(sd.query_devices())
                 if d["max_input_channels"] > 0 and d["name"] == nom]
    for i in candidats:
        if sd.query_devices(i)["hostapi"] == api:
            return i
    return candidats[0] if candidats else None


BLOC = 480            # 30 ms par morceau de son : réaction rapide
AVANT = 0.5           # secondes gardées AVANT l'appui (le début du 1er mot n'est jamais perdu)


class Enregistreur:
    """Micro toujours prêt (16 kHz mono). On ne garde le son que pendant la dictée,
    plus une petite mémoire des 0,5 dernières secondes."""

    def __init__(self):
        self.flux = None
        self.nom = None
        self.nom_reel = None
        self.capture = False
        self.morceaux = []
        self.avant = collections.deque(maxlen=int(AVANT * FREQ / BLOC) + 1)
        self.verrou = threading.Lock()
        self.niveau = 0.0          # 0..1, pour l'animation
        self.dernier_son = 0.0     # moment où on a entendu une voix
        self.max_rms = 0.0
        self.bruit = 0.004
        self.a_parle = False       # une voix a été entendue depuis le début de la dictée
        self.vad = None            # détecteur de voix Silero (reconnaît une VOIX, pas un bruit)
        self._vad_ok = None

    def charger_vad(self):
        if self._vad_ok is None:
            try:
                from faster_whisper.vad import get_vad_model
                self.vad = get_vad_model()
                self._vad_ok = True
            except Exception:
                self._vad_ok = False   # sans lui, on garde la mesure du volume
        return self._vad_ok

    def surveiller(self):
        """À appeler souvent pendant la dictée : met à jour « dernier_son »
        seulement si une vraie voix est entendue dans les 0,4 dernières secondes."""
        if not self.capture or not self._vad_ok:
            return
        with self.verrou:
            morceaux = self.morceaux[-14:]          # 14 × 30 ms ≈ 0,4 s
        if not morceaux:
            return
        x = np.concatenate(morceaux)
        n = len(x) // 512 * 512
        if n == 0:
            return
        probas = np.asarray(self.vad(x[-n:])).reshape(-1)
        if probas[-4:].max() > 0.5:                 # voix dans les ~130 dernières ms
            self.dernier_son = time.time()
            self.a_parle = True

    @property
    def actif(self):
        return self.capture

    def _rappel(self, indata, frames, temps, status):
        x = indata[:, 0].copy()
        rms = float(np.sqrt(np.mean(x * x)) + 1e-9)
        with self.verrou:
            if not self.capture:
                self.avant.append(x)
                self.bruit = 0.97 * self.bruit + 0.03 * min(rms, 0.05)
                return
            self.morceaux.append(x)
        self.max_rms = max(self.max_rms, rms)
        self.niveau = min(1.0, rms * 12)
        if not self._vad_ok and rms > max(0.012, self.bruit * 3):   # secours sans Silero
            self.dernier_son = time.time()
            self.a_parle = True

    def _creer_flux(self, index):
        reglages = None
        if index is not None and sd.query_devices(index)["hostapi"] == _api_wasapi():
            reglages = sd.WasapiSettings(auto_convert=True)
        return sd.InputStream(device=index, samplerate=FREQ, channels=1, dtype="float32",
                              blocksize=BLOC, callback=self._rappel, extra_settings=reglages)

    def ouvrir(self, nom_micro=None):
        """Prépare le micro (ne fait rien s'il est déjà prêt)."""
        if self.flux is not None and self.flux.active and nom_micro == self.nom:
            return
        self.fermer()
        index = _trouver(nom_micro)
        trouve = index is not None
        try:
            flux = self._creer_flux(index)
        except Exception:
            if index is None:
                raise
            flux = self._creer_flux(None)  # micro choisi absent : micro par défaut
            trouve = False
        flux.start()
        self.flux, self.nom = flux, nom_micro
        self.nom_reel = nom_micro if trouve else None   # micro vraiment utilisé (None = défaut)

    @property
    def micro_manquant(self):
        """Vrai si le micro choisi n'est pas (encore) là : on utilise celui de Windows en attendant."""
        return bool(self.nom) and self.nom_reel != self.nom

    def rechercher_micro(self):
        """Au démarrage du PC, le micro USB arrive parfois après l'appli.
        On redemande la liste des micros à Windows et on passe sur le bon s'il est là."""
        if not self.micro_manquant or self.capture:
            return False
        nom = self.nom
        self.fermer()
        try:
            sd._terminate()                # la liste des micros n'est relue qu'à l'initialisation
            sd._initialize()
        except Exception:
            pass
        self.nom = None
        self.ouvrir(nom)
        return not self.micro_manquant

    def fermer(self):
        flux, self.flux = self.flux, None
        if flux is not None:
            try:
                flux.stop()
                flux.close()
            except Exception:
                pass
        with self.verrou:
            self.avant.clear()

    def demarrer(self, nom_micro=None):
        self.ouvrir(nom_micro)
        with self.verrou:
            self.morceaux = list(self.avant)
            self.avant.clear()
            self.capture = True
        self.niveau = 0.0
        self.max_rms = 0.0
        self.dernier_son = time.time()
        self.a_parle = False

    def arreter(self):
        """Arrête la dictée et renvoie l'audio (numpy float32, 16 kHz). Le micro reste prêt."""
        with self.verrou:
            self.capture = False
            audio = (np.concatenate(self.morceaux) if self.morceaux
                     else np.zeros(0, dtype=np.float32))
            self.morceaux = []
        self.niveau = 0.0
        return audio
