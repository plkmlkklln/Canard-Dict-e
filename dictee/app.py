# -*- coding: utf-8 -*-
"""Chef d'orchestre : raccourci, micro, reconnaissance, écriture, canard."""
import ctypes
import logging
import logging.handlers
import os
import queue
import sys
import threading
import time

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from . import audio, config, moteur as moteur_mod, texte as texte_mod, ui, vocabulaire
from .clavier import TOUCHES, Raccourci, coller, nom_touche
from .lanceur import Lanceur

log = logging.getLogger("dictee")

APPUI_COURT = 0.35     # secondes : relâché avant = mode mains libres
ANNONCE = 0.25         # secondes : son + animation seulement si la touche reste tenue
DUREE_MIN = 0.4        # secondes : en dessous, on ignore
DUREE_MAX = 300        # secondes : sécurité
SILENCE_TOTAL = 0.003  # niveau sonore max en dessous duquel on n'a rien entendu
QUEUE = 0.2            # secondes d'écoute en plus après la fin (dernier mot pas coupé)
REPOS = 2.5            # secondes avant que la barre s'en aille (option « cacher »)
ATTENTE_PREMIER_MOT = 8   # mains libres : si tu n'as encore rien dit, on attend plus longtemps

DELAIS = [(1, "1 s"), (1.5, "1,5 s"), (2, "2 s"), (3, "3 s"), (5, "5 s"), (10, "10 s"), (0, "Jamais")]
ANCIENS_MODELES = {"small": "rapide", "large-v3-turbo": "equilibre"}


class Pont(QObject):
    """Transporte les événements des autres fils vers le fil de l'interface."""
    appui = Signal(float)
    relache = Signal(float)
    autre = Signal()
    echap = Signal()
    etape = Signal(str)
    pret = Signal(str)
    erreur = Signal(str)
    fini = Signal(str)
    lanceur = Signal(bool)
    win_h = Signal()


def reglage_modele_par_defaut(params):
    m = params["modele"]
    if m in ANCIENS_MODELES:
        m = ANCIENS_MODELES[m]
    if m not in moteur_mod.REGLAGES:
        m = "precis" if moteur_mod.gpu_disponible() else "rapide"
    params["modele"] = m


class Application:
    def __init__(self, qapp, params=None, enregistreur=None, moteur=None, services=True):
        self.qapp = qapp
        self.params = params or config.Parametres()
        self.rec = enregistreur or audio.Enregistreur()
        self.moteur = moteur or moteur_mod.Moteur()
        self.pont = Pont()
        self.file = queue.Queue()
        self.coller = coller

        # État
        self.ecoute = False
        self.mains_libres = False
        self.annonce = False
        self.ignorer_relache = False
        self.t_appui = 0.0
        self.t_debut = 0.0
        self.modele_pret = False
        self.occupe = 0
        self._jeton_message = 0
        self._fin_prevue = None
        self._retenir_jusqua = 0.0
        self.quitte = False
        self.micros = []
        reglage_modele_par_defaut(self.params)

        # Interface : le canard
        self.barre = ui.Barre()
        self.barre.source_niveau = lambda: self.rec.niveau if self.ecoute else 0.0
        b = self.barre.pont
        b.demande_ecouter.connect(self.clic_micro)
        b.demande_reglage.connect(self.regler)
        b.demande_quitter.connect(self.quitter)
        b.demande_masquer.connect(self.masquer)
        b.demande_retenir.connect(self.retenir)
        b.demande_micros.connect(self.rafraichir_micros)
        b.demande_mes_mots.connect(self.ouvrir_mes_mots)
        self.barre.deplacee.connect(lambda x, y: self.params.regler("ancre", [x, y]))
        self.barre.placer(self.params["ancre"])
        self.qapp.setWindowIcon(ui.icone_appli())

        p = self.pont
        p.appui.connect(self.sur_appui)
        p.relache.connect(self.sur_relache)
        p.autre.connect(self.sur_autre_touche)
        p.echap.connect(self.sur_echap)
        p.etape.connect(self.sur_etape)
        p.pret.connect(self.sur_modele_pret)
        p.erreur.connect(self.sur_erreur_modele)
        p.fini.connect(self.sur_fini)
        p.lanceur.connect(self.sur_lanceur)
        p.win_h.connect(self.sur_win_h)

        self.raccourci = Raccourci(self.params["touche"], p.appui.emit, p.relache.emit,
                                   p.autre.emit, p.echap.emit, p.win_h.emit)
        self.raccourci.remplacer_win_h = self.params["win_h"]
        self.lanceur = Lanceur(p.lanceur.emit)
        self.lanceur.actif = self.params["lanceur"]
        self._cacher = QTimer()
        self._cacher.setSingleShot(True)
        self._cacher.timeout.connect(self._cacher_si_inutile)

        self.minuterie = QTimer()
        self.minuterie.timeout.connect(self._tic)
        self.minuterie.start(50)
        # Micro choisi pas encore là (PC qui démarre, casque éteint) : on le cherche toutes les 10 s.
        self._chercheur = QTimer()
        self._chercheur.timeout.connect(self._chercher_micro)
        self._chercheur.start(10_000)

        threading.Thread(target=self._travailleur, daemon=True).start()
        self.tray = None
        if services:
            self.raccourci.demarrer()
            self.lanceur.start()
            self._creer_tray()
        self.publier()
        self.message("Je me prépare…")
        self.charger_modele()

    # ------------------------------------------------------------ état du canard
    def publier(self):
        """Envoie tout l'état à la page du canard."""
        p = self.params
        micros = self.micros
        self.barre.etat({
            "ecoute": self.ecoute and self.annonce,
            "reflechit": self.occupe > 0,
            "pret": self.modele_pret,
            "nomTouche": nom_touche(p["touche"]),
            "skin": p["skin"],
            "maxPanneau": self.barre.hauteur_max_panneau(),
            "reglages": {
                "lanceur": p["lanceur"], "ponctuation": p["ponctuation"], "filtre": p["filtre"],
                "sons": p["sons"], "win_h": p["win_h"], "cacher": p["cacher"],
                "costumes": p["costumes"], "demarrage": config.demarrage_windows_actif(),
            },
            "navs": [
                {"cle": "delai", "icone": "timer", "titre": "Délai avant d'arrêter",
                 "options": DELAIS, "valeur": p["delai"]},
                {"cle": "micro", "icone": "mic", "titre": "Choisir le microphone",
                 "options": [[None, "Micro par défaut de Windows"]] + [[n, n] for n in micros]
                 + ([[p["micro"], p["micro"] + " (pas branché)"]]
                    if p["micro"] and p["micro"] not in micros else []),
                 "valeur": p["micro"]},         # ton choix reste affiché, même débranché
                {"cle": "touche", "icone": "keyboard", "titre": "Raccourci clavier",
                 "options": [[k, v] for k, v in TOUCHES.items()], "valeur": p["touche"]},
                {"cle": "modele", "icone": "neurology", "titre": "Modèle de reconnaissance",
                 "options": [[k, v] for k, v in moteur_mod.NOMS_REGLAGES.items()],
                 "valeur": p["modele"]},
            ],
        })

    def rafraichir_micros(self):
        """Relit la liste des micros (seulement quand on ouvre les paramètres : c'est lent)."""
        try:
            self.micros = audio.lister_micros()
        except Exception:
            self.micros = []
        self.publier()

    def message(self, texte, duree=0):
        self._jeton_message += 1
        self.barre.message(texte, duree)
        if duree:
            jeton = self._jeton_message
            QTimer.singleShot(int(duree * 1000), lambda: self._message_repos(jeton))

    def _message_repos(self, jeton):
        if jeton == self._jeton_message and not self.ecoute and self.occupe == 0:
            self._repos()

    def _repos(self):
        """Rien à faire : avec l'option « cacher », la barre s'en va."""
        if self.params["cacher"]:
            self._cacher_si_inutile()

    def retenir(self, secondes):
        self._retenir_jusqua = time.time() + secondes
        self._cacher.start(int(secondes * 1000) + 100)

    def mettre_a_jour_mode(self):
        self.publier()

    # ------------------------------------------------------------ modèle
    def charger_modele(self):
        self.modele_pret = False
        self.publier()
        reglage = self.params["modele"]

        def travail():
            try:
                appareil = self.moteur.charger(reglage, self.pont.etape.emit)
                self.pont.pret.emit(appareil)
            except Exception as e:
                log.exception("Chargement du modele")
                self.pont.erreur.emit(str(e))

        threading.Thread(target=travail, daemon=True).start()

    def sur_etape(self, etape):
        if etape == "telechargement":
            self.message("Je télécharge le modèle… Patiente.")
        else:
            self.message("Je me prépare…")

    def sur_modele_pret(self, appareil):
        self.modele_pret = True
        self.publier()
        self.preparer_micro()
        if not self.ecoute:
            self.message("Coin ! Je suis prêt.", 2.5)
        if self.params["premier_lancement"]:
            self.params.regler("premier_lancement", False)
            self.barre.show()
            self.ouvrir_aide()

    def preparer_micro(self):
        """Micro ouvert à l'avance : l'écoute démarre sans attendre."""
        try:
            self.rec.ouvrir(self.params["micro"])
        except Exception:
            log.exception("Micro")  # on réessaiera au moment de parler
        if hasattr(self.rec, "charger_vad"):
            threading.Thread(target=self.rec.charger_vad, daemon=True).start()

    def _chercher_micro(self):
        if self.ecoute or not getattr(self.rec, "micro_manquant", False):
            return
        try:
            if self.rec.rechercher_micro():
                log.info("Micro retrouvé : %s", self.params["micro"])
                self.rafraichir_micros()
        except Exception:
            log.exception("Recherche du micro")

    def sur_erreur_modele(self, erreur):
        self.message("Problème avec le modèle. Regarde le journal.")
        self.barre.show()

    # ------------------------------------------------------------ raccourci clavier
    def sur_appui(self, t):
        if self.ecoute:
            if self.mains_libres:          # 2e appui : on arrête
                self.ignorer_relache = True
                self.arreter()
            return
        if not self.modele_pret:
            self.ignorer_relache = True
            self.barre.show()
            self.message("Je me prépare… Encore un instant.", 3)
            return
        self.t_appui = t
        if not self.demarrer(annoncer=False):
            self.ignorer_relache = True
            return
        QTimer.singleShot(int(ANNONCE * 1000), self._annoncer_si_tenu)

    def _annoncer_si_tenu(self):
        if self.ecoute and not self.annonce and self.raccourci.enfoncee:
            self.annoncer()

    def sur_relache(self, t):
        if self.ignorer_relache:
            self.ignorer_relache = False
            return
        if not self.ecoute or self.mains_libres:
            return
        if t - self.t_appui < APPUI_COURT:
            self.mains_libres = True
            self.annoncer()
        else:
            self.arreter()

    def sur_autre_touche(self):
        # Ctrl droit utilisé pour un raccourci normal (Ctrl+C...) : on annule sans bruit.
        if self.ecoute and not self.mains_libres:
            self.ignorer_relache = True
            self.annuler(silencieux=not self.annonce)

    def sur_echap(self):
        if self.ecoute:
            if self.raccourci.enfoncee:
                self.ignorer_relache = True
            self.annuler()

    def sur_win_h(self):
        """Windows+H : la barre apparaît et écoute tout de suite (mains libres).
        Windows+H encore une fois : on arrête."""
        self.barre.show()
        self.clic_micro()

    def clic_micro(self):
        if self.ecoute:
            self.arreter()
        elif not self.modele_pret:
            self.message("Je me prépare… Encore un instant.", 3)
        elif self.demarrer(annoncer=False):
            self.mains_libres = True
            self.annoncer()

    # ------------------------------------------------------------ écoute
    def demarrer(self, annoncer=True):
        self._finir_arret()  # une dictée se termine encore ? on la finit d'abord
        try:
            self.rec.demarrer(self.params["micro"])
        except Exception:
            log.exception("Micro")
            self.barre.show()
            self.message("Je ne trouve pas de micro.", 5)
            return False
        self.ecoute = True
        self.mains_libres = False
        self.annonce = False
        self.t_debut = time.time()
        if annoncer:
            self.annoncer()
        return True

    def annoncer(self):
        if self.annonce:
            return
        self.annonce = True
        self._cacher.stop()
        if self.params["sons"]:
            audio.jouer(audio.SON_DEBUT)
        self.barre.show()
        self.barre.evenement("fermer")
        self.barre.evenement("coin")       # « Coin ! » et une pirouette
        self.message("")
        self.publier()

    def annuler(self, silencieux=False):
        self.rec.arreter()
        self.ecoute = False
        self.mains_libres = False
        etait_annonce, self.annonce = self.annonce, False
        self.publier()
        if not silencieux:
            if self.params["sons"]:
                audio.jouer(audio.SON_ANNULE)
            self.message("Annulé.", 2)
        elif etait_annonce:
            self.message("", 1)

    def arreter(self):
        duree = time.time() - self.t_debut
        self.ecoute = False
        self.mains_libres = False
        self.annonce = False
        if self.params["sons"]:
            audio.jouer(audio.SON_FIN)
        self.publier()
        # On écoute encore un tout petit peu : le dernier mot n'est pas coupé.
        self._fin_prevue = duree
        QTimer.singleShot(int(QUEUE * 1000), self._finir_arret)

    def _finir_arret(self):
        if self._fin_prevue is None:
            return
        duree, self._fin_prevue = self._fin_prevue, None
        enregistre = self.rec.arreter()
        max_rms = self.rec.max_rms
        if duree < DUREE_MIN:
            self.message("Trop court. Parle un peu plus.", 3)
        elif max_rms < SILENCE_TOTAL:
            self.message("Je n'ai rien entendu.", 3)
        else:
            self.occupe += 1
            self.file.put(enregistre)
        self.publier()

    def _tic(self):
        if not self.ecoute:
            return
        self._tics = getattr(self, "_tics", 0) + 1
        if self._tics % 2 == 0 and hasattr(self.rec, "surveiller"):
            self.rec.surveiller()            # détecteur de voix, toutes les 100 ms
        maintenant = time.time()
        delai = self.params["delai"]
        if maintenant - self.t_debut > DUREE_MAX:
            self.arreter()
        elif self.mains_libres and delai:
            # Tu as parlé puis tu te tais : on arrête vite. Pas encore parlé : on attend plus.
            attente = delai if getattr(self.rec, "a_parle", True) else max(delai, ATTENTE_PREMIER_MOT)
            if maintenant - self.rec.dernier_son > attente:
                self.arreter()

    # ------------------------------------------------------------ transcription
    def _travailleur(self):
        while True:
            enregistre = self.file.get()
            if enregistre is None:
                return
            try:
                while not self.modele_pret:
                    time.sleep(0.2)
                brut = self.moteur.transcrire(enregistre, self.params["ponctuation"])
                propre = texte_mod.nettoyer(brut, self.params["ponctuation"],
                                            self.params["filtre"])
                log.info("Reconnu : %r -> %r", brut, propre)
                if propre:
                    self.coller(propre + " ", self.raccourci)
                self.pont.fini.emit(propre)
            except Exception:
                log.exception("Transcription")
                self.pont.fini.emit("\0")

    def sur_fini(self, propre):
        self.occupe = max(0, self.occupe - 1)
        self.publier()
        if self.ecoute:
            return
        if propre == "\0":
            self.message("Oups, un problème. Réessaie.", 4)
        elif propre:
            self.barre.evenement("texte", propre)   # le canard se déguise si un mot magique est dit
            self._jeton_message += 1
            jeton = self._jeton_message
            QTimer.singleShot(int(REPOS * 1000), lambda: self._message_repos(jeton))
        else:
            self.message("Je n'ai rien compris.", 3)

    # ------------------------------------------------------------ lanceur
    def sur_lanceur(self, dans_texte):
        if not self.params["lanceur"]:
            return
        if dans_texte:
            self._cacher.stop()
            self.barre.show()
        else:
            self._cacher.start(1500)

    def _cacher_si_inutile(self):
        reste = self._retenir_jusqua - time.time()
        if reste > 0:
            self._cacher.start(int(reste * 1000) + 100)
            return
        if ((self.params["lanceur"] or self.params["cacher"]) and not self.ecoute
                and self.occupe == 0 and self.modele_pret and not self.quitte):
            self.barre.evenement("fermer")
            self.barre.hide()

    def masquer(self):
        if self.ecoute:
            self.annuler(silencieux=True)
        self.barre.hide()
        if self.tray and not getattr(self, "_deja_dit_cache", False):
            self._deja_dit_cache = True          # une fois : dire où il est parti
            self.tray.showMessage(config.NOM_APPLI,
                                  "Je suis caché ici, près de l'horloge.\n"
                                  "Clique sur moi (ou sur mon icône du Bureau) pour me revoir.",
                                  ui.icone_appli(), 5000)

    # ------------------------------------------------------------ paramètres
    def regler(self, cle, valeur):
        if cle == "demarrage":
            try:
                config.regler_demarrage_windows(valeur)
            except Exception:
                log.exception("Demarrage Windows")
            self.publier()
            return
        self.params.regler(cle, valeur)
        if cle == "lanceur":
            self.lanceur.actif = valeur
            if not valeur:
                self.barre.show()
        elif cle == "win_h":
            self.raccourci.remplacer_win_h = valeur
        elif cle == "cacher":
            if not valeur:
                self.barre.show()
        elif cle == "micro":
            if not self.ecoute:
                self.preparer_micro()
        elif cle == "touche":
            self.raccourci.regler(valeur)
        elif cle == "modele":
            self.message("Je change de modèle…")
            self.charger_modele()
        self.publier()

    def ouvrir_mes_mots(self):
        self.barre.evenement("fermer")
        try:
            vocabulaire.ouvrir()
        except Exception:
            log.exception("Mes mots")

    def ouvrir_reglages(self):
        self.montrer_barre()
        self.barre.evenement("panneau")

    def ouvrir_aide(self):
        self.montrer_barre()
        self.barre.evenement("aide")

    # ------------------------------------------------------------ icône de notification
    def _creer_tray(self):
        self.tray = QSystemTrayIcon(ui.icone_appli(), self.qapp)
        self.tray.setToolTip(config.NOM_APPLI)
        m = ui.nouveau_menu()
        for texte, fonction in (("Afficher le canard", self.montrer_barre),
                                ("Paramètres", self.ouvrir_reglages),
                                ("Aide", self.ouvrir_aide)):
            a = QAction(texte, m)
            a.triggered.connect(fonction)
            m.addAction(a)
        m.addSeparator()
        q = QAction("Quitter", m)
        q.triggered.connect(self.quitter)
        m.addAction(q)
        self._menu_tray = m
        self.tray.setContextMenu(m)
        self.tray.activated.connect(
            lambda raison: self.montrer_barre()
            if raison in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
        self.tray.show()

    def montrer_barre(self):
        self._cacher.stop()
        self.barre.show()
        self.barre.raise_()

    def quitter(self):
        """Le canard pleure un peu (« Snif… à bientôt »), puis l'appli se ferme."""
        if self.quitte:
            return
        self.quitte = True
        self.barre.show()
        self.barre.evenement("pleurer")
        QTimer.singleShot(2600, self._fermer)

    def _fermer(self):
        self.raccourci.arreter()
        self.lanceur.arreter()
        self.rec.arreter()
        self.rec.fermer()
        self.file.put(None)
        if self.tray:
            self.tray.hide()
        self.qapp.quit()


# ---------------------------------------------------------------- assistant d'installation
class Assistant:
    """Les 5 étapes du design « Installation » : bienvenue, options, micro, installation, fin.
    Les fichiers sont déjà copiés : l'étape « Installation » règle tout et prépare le modèle."""

    def __init__(self, qapp, params, rec, moteur, quand_fini):
        self.qapp, self.params, self.rec, self.moteur = qapp, params, rec, moteur
        self.quand_fini = quand_fini
        self.test = False
        reglage_modele_par_defaut(params)
        self.fenetre = ui.FenetreAssistant()
        self.fenetre.source_niveau = lambda: self.rec.niveau if self.test else 0.0
        p = self.fenetre.pont
        p.demande_micro.connect(lambda v: params.regler("micro", v))
        p.demande_test.connect(self.tester)
        p.demande_installer.connect(self.installer)
        p.demande_terminer.connect(self.terminer)
        try:
            micros = audio.lister_micros()
        except Exception:
            micros = []
        import json
        p.etat_initial = json.dumps({
            "chemin": config.dossier_appli(),
            "espace": f"Espace utilisé : {taille_dossier(config.dossier_appli())}",
            "mics": [[None, "Micro par défaut de Windows"]] + [[n, n] for n in micros],
            "mic": params["micro"] if params["micro"] in micros else None,
            "opts": {"bureau": True, "demarrage": True, "win_h": params["win_h"]},
        }, ensure_ascii=False)
        self.fenetre.montrer()

    def tester(self, actif):
        try:
            if actif:
                self.rec.demarrer(self.params["micro"])
            else:
                self.rec.arreter()
            self.test = actif
        except Exception:
            log.exception("Test micro")
            self.test = False

    def installer(self, options):
        prog = self.fenetre.pont.progression

        def travail():
            try:
                prog.emit(5, "Copie des fichiers…")
                time.sleep(0.6)
                # Version « légère » : le modèle n'est pas fourni, on le télécharge (une seule fois).
                nom_modele = moteur_mod.REGLAGES.get(self.params["modele"], ("small", 1))[0]
                phase = ("Téléchargement du modèle vocal (une seule fois, quelques minutes)…"
                         if moteur_mod.chemin_local(nom_modele) is None
                         else "Installation du modèle vocal…")
                prog.emit(20, phase)
                fini = threading.Event()

                def avancer():                 # la barre avance pendant le chargement
                    pct, attente = 20, 0.25 if "Installation" in phase else 4.0
                    while not fini.wait(attente) and pct < 72:
                        pct += 1
                        prog.emit(pct, phase)
                threading.Thread(target=avancer, daemon=True).start()
                try:
                    self.moteur.charger(self.params["modele"])
                finally:
                    fini.set()
                prog.emit(78, "Réglage du micro…")
                self.params["win_h"] = bool(options.get("win_h", True))
                self.params["premier_lancement"] = False
                self.params.sauver()
                time.sleep(0.5)
                prog.emit(90, "Le canard enfile son chapeau…")
                raccourci_bureau(bool(options.get("bureau", True)))
                config.regler_demarrage_windows(bool(options.get("demarrage", True)))
                time.sleep(0.6)
            except Exception:
                log.exception("Installation")
            prog.emit(100, "C'est prêt !")

        threading.Thread(target=travail, daemon=True).start()

    def terminer(self, lancer):
        if self.test:
            self.tester(False)
        self.fenetre.close()
        self.quand_fini(lancer)


def taille_dossier(dossier):
    total = 0
    for racine, _, fichiers in os.walk(dossier):
        for f in fichiers:
            try:
                total += os.path.getsize(os.path.join(racine, f))
            except OSError:
                pass
    return f"{total / 1e9:.1f} Go".replace(".", ",")


def raccourci_bureau(creer):
    """Crée (ou retire) l'icône « Canard Dictée » sur le Bureau."""
    if not getattr(sys, "frozen", False):
        return
    import comtypes.client
    shell = comtypes.client.CreateObject("WScript.Shell", dynamic=True)
    bureau = shell.SpecialFolders("Desktop")
    chemin = os.path.join(bureau, config.NOM_APPLI + ".lnk")
    if not creer:
        if os.path.exists(chemin):
            os.remove(chemin)
        return
    lien = shell.CreateShortcut(chemin)
    lien.TargetPath = sys.executable
    lien.WorkingDirectory = os.path.dirname(sys.executable)
    lien.IconLocation = sys.executable + ",0"
    lien.Description = "Écris avec ta voix"
    lien.Save()


# ---------------------------------------------------------------- lancement
def _preparer_journal():
    os.makedirs(config.DOSSIER, exist_ok=True)
    gestion = logging.handlers.RotatingFileHandler(
        os.path.join(config.DOSSIER, "journal.txt"), maxBytes=500_000, backupCount=1,
        encoding="utf-8")
    gestion.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(gestion)
    log.setLevel(logging.INFO)


def _deja_lance():
    ctypes.windll.kernel32.CreateMutexW(None, False, "DicteeVocale_UneSeuleFois")
    return ctypes.windll.kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS


SONNETTE = "CanardDictee_Reveil"


def _sonner_le_canard():
    """Le canard tourne déjà (peut-être caché) : on lui demande de se montrer.
    Renvoie False si personne n'a répondu."""
    from PySide6.QtNetwork import QLocalSocket
    prise = QLocalSocket()
    prise.connectToServer(SONNETTE)
    if not prise.waitForConnected(1500):
        return False
    prise.write(b"montrer")
    prise.flush()
    prise.waitForBytesWritten(1000)
    prise.disconnectFromServer()
    return True


def _ecouter_la_sonnette(qapp, quand_on_sonne):
    """Le canard qui tourne attend qu'on double-clique à nouveau sur son icône."""
    from PySide6.QtNetwork import QLocalServer
    QLocalServer.removeServer(SONNETTE)          # nettoie une sonnette laissée par un plantage
    serveur = QLocalServer(qapp)

    def nouvelle():
        prise = serveur.nextPendingConnection()
        if prise is not None:
            prise.readyRead.connect(lambda: (prise.readAll(), quand_on_sonne()))
            prise.disconnected.connect(prise.deleteLater)

    serveur.newConnection.connect(nouvelle)
    serveur.listen(SONNETTE)
    return serveur


def main():
    # Dans l'exe sans console, stdout/stderr n'existent pas : on les remplace.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    _preparer_journal()
    if _deja_lance():
        # Déjà ouvert (souvent juste caché) : on le fait réapparaître, sans message.
        if "--demarrage" in sys.argv:
            return
        from PySide6.QtCore import QCoreApplication
        _ = QCoreApplication(sys.argv)
        if not _sonner_le_canard():
            ctypes.windll.user32.MessageBoxW(
                None, "Canard Dictée est déjà ouvert.\n"
                      "Regarde l'icône du canard près de l'horloge.", config.NOM_APPLI, 0x40)
        return
    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)
    qapp.setApplicationName(config.NOM_APPLI)
    qapp.setWindowIcon(ui.icone_appli())
    params = config.Parametres()
    rec = audio.Enregistreur()
    moteur = moteur_mod.Moteur()
    garde = {}

    def lancer_appli(au_demarrage=False):
        appli = Application(qapp, params=params, enregistreur=rec, moteur=moteur)
        garde["appli"] = appli
        if not ((params["lanceur"] or params["cacher"]) and au_demarrage):
            appli.barre.show()

    if "--bienvenue" in sys.argv:
        def fin(lancer):
            if lancer:
                lancer_appli()
            else:
                qapp.quit()
        garde["assistant"] = Assistant(qapp, params, rec, moteur, fin)
    else:
        lancer_appli("--demarrage" in sys.argv)

    def quand_on_sonne():                      # double-clic sur l'icône alors qu'il tourne déjà
        log.info("Icône relancée : le canard réapparaît")
        if "appli" in garde:
            garde["appli"].montrer_barre()
        elif "assistant" in garde:
            f = garde["assistant"].fenetre
            f.show(); f.raise_(); f.activateWindow()
    garde["sonnette"] = _ecouter_la_sonnette(qapp, quand_on_sonne)
    log.info("Demarrage")
    sys.exit(qapp.exec())
