# -*- coding: utf-8 -*-
"""Reconnaissance vocale locale avec faster-whisper."""
import glob
import logging
import os
import sys
import threading

import numpy as np

from . import vocabulaire

from .config import DOSSIER, dossier_appli

log = logging.getLogger("dictee")

# Les 3 choix du menu : (modèle Whisper, largeur de recherche).
REGLAGES = {
    "rapide": ("small", 1),
    "equilibre": ("large-v3-turbo", 1),
    "precis": ("large-v3-turbo", 5),
}
NOMS_REGLAGES = {"rapide": "Rapide", "equilibre": "Équilibré", "precis": "Précis (conseillé)"}
FREQ_ESSAI = 16000
DOSSIER_MODELES = os.path.join(DOSSIER, "modeles")

# Ce texte d'exemple pousse le modèle à mettre majuscules et ponctuation.
PROMPT = ("Bonjour. Voici un texte en français, bien ponctué, avec des majuscules, "
          "des virgules, des points et des points d'interrogation ?")


def _preparer_cuda():
    """Rend visibles les DLL NVIDIA (cuBLAS, cuDNN) installées avec l'appli."""
    bases = [getattr(sys, "_MEIPASS", None)] + list(sys.path)
    for base in bases:
        if not base or not os.path.isdir(base):
            continue
        for d in glob.glob(os.path.join(base, "nvidia", "*", "bin")):
            try:
                os.add_dll_directory(d)
            except OSError:
                pass
            if d not in os.environ.get("PATH", ""):
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


def gpu_disponible():
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def chemin_local(nom):
    """Chemin du modèle s'il est déjà sur le PC, sinon None."""
    fourni = os.path.join(dossier_appli(), "modeles", nom)
    if os.path.isfile(os.path.join(fourni, "model.bin")):
        return fourni
    from faster_whisper.utils import download_model
    try:
        return download_model(nom, cache_dir=DOSSIER_MODELES, local_files_only=True)
    except Exception:
        return None


class Moteur:
    def __init__(self):
        self.modele = None
        self.nom = None
        self.appareil = None
        self.recherche = 1
        self.verrou = threading.Lock()

    def charger(self, reglage, sur_etape=lambda etape: None):
        """Charge le modèle du réglage (rapide / equilibre / precis).
        Renvoie "cuda" ou "cpu". Ne recharge rien si le bon modèle est déjà prêt."""
        nom, self.recherche = REGLAGES.get(reglage, REGLAGES["equilibre"])
        if self.modele is not None and self.nom == nom:
            return self.appareil
        _preparer_cuda()
        from faster_whisper import WhisperModel
        from faster_whisper.utils import download_model

        chemin = chemin_local(nom)
        if chemin is None:
            sur_etape("telechargement")
            chemin = download_model(nom, cache_dir=DOSSIER_MODELES)
        sur_etape("chargement")

        essais = [("cuda", "float16")] if gpu_disponible() else []
        essais.append(("cpu", "int8"))
        derniere = None
        for appareil, calcul in essais:
            try:
                modele = WhisperModel(chemin, device=appareil, compute_type=calcul,
                                      cpu_threads=max(2, (os.cpu_count() or 4) - 2))
                # Petit essai pour vérifier que tout marche vraiment (DLL NVIDIA...).
                segs, _ = modele.transcribe(np.zeros(FREQ_ESSAI, np.float32), language="fr")
                list(segs)
                # Préchauffe aussi le filtre de silence : la 1re dictée sera aussi rapide.
                segs, _ = modele.transcribe(np.zeros(FREQ_ESSAI, np.float32), language="fr",
                                            vad_filter=True)
                list(segs)
            except Exception as e:  # pas de carte NVIDIA utilisable : on passe au CPU
                log.warning("Echec %s/%s : %s", appareil, calcul, e)
                derniere = e
                continue
            with self.verrou:
                self.modele, self.nom, self.appareil = modele, nom, appareil
            log.info("Modele %s charge sur %s", nom, appareil)
            return appareil
        raise RuntimeError(f"Impossible de charger le modèle : {derniere}")

    def transcrire(self, audio, ponctuation=True):
        with self.verrou:
            if self.modele is None:
                raise RuntimeError("Modèle pas encore prêt")
            segments, _ = self.modele.transcribe(
                audio, language="fr",
                # « Précis » cherche plus large. Sur processeur, toujours simple (bien plus rapide).
                beam_size=self.recherche if self.appareil == "cuda" else 1,
                without_timestamps=True,
                vad_filter=True, vad_parameters={"min_silence_duration_ms": 600},
                initial_prompt=vocabulaire.consigne(PROMPT if ponctuation else "") or None,
                condition_on_previous_text=False)
            morceaux = []
            for s in segments:
                if s.no_speech_prob > 0.6 and s.avg_logprob < -0.8:
                    continue  # probablement du silence
                if s.compression_ratio > 2.6:
                    continue  # répétitions inventées
                morceaux.append(s.text.strip())
        return " ".join(morceaux)
