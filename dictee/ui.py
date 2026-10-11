# -*- coding: utf-8 -*-
"""Interface Canard Dictée : la barre et l'assistant sont des pages web (dossier web/)
affichées dans des fenêtres Qt transparentes. L'icône est dessinée ici."""
import json
import os

from PySide6.QtCore import QObject, QPoint, QRect, QRectF, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import (QColor, QCursor, QGuiApplication, QIcon, QPainter, QPainterPath,
                           QPixmap, QRegion)
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMenu

from .config import dossier_appli

LARGEUR_BARRE = 420      # largeur fixe de la fenêtre du canard (le plus large menu + ombre)
DOSSIER_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
if not os.path.isdir(DOSSIER_WEB):                       # version installée (.exe)
    DOSSIER_WEB = os.path.join(dossier_appli(), "_internal", "dictee", "web")


# ----------------------------------------------------------------- icône (design « Icône Canard »)
def dessiner_icone(taille=256, fond=True):
    """Le canard au chapeau de cow-boy, dessiné à partir du design (repère 256 px)."""
    pm = QPixmap(taille, taille)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(taille / 256, taille / 256)
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, 256, 256), 58, 58)
    if fond:
        p.fillPath(clip, QColor("#2a2a2c"))
    p.setClipPath(clip)
    p.translate(43, 74)
    p.setPen(Qt.NoPen)

    def ell(x, y, w, h, c, alpha=1.0):
        col = QColor(c)
        col.setAlphaF(alpha)
        p.setBrush(col)
        p.drawEllipse(QRectF(x, y, w, h))

    ell(0, 0, 170, 170, "#E9A90E")
    ell(18, 14, 90, 70, "#FFFFFF", 0.18)               # reflet
    ell(28, 46, 50, 57, "#FFFFFF")
    ell(42, 62, 28, 32, "#1b1b1d")
    ell(47, 67, 11, 11, "#FFFFFF")
    ell(92, 46, 50, 57, "#FFFFFF")
    ell(100, 62, 28, 32, "#1b1b1d")
    ell(105, 67, 11, 11, "#FFFFFF")
    ell(7, 99, 32, 21, "#FF8FA3", 0.85)
    ell(131, 99, 32, 21, "#FF8FA3", 0.85)
    ell(58, 104, 53, 31, "#F07510")                    # bec du bas
    ell(48, 90, 74, 34, "#FF8A1A")                     # bec du haut
    # Chapeau de cow-boy
    p.setBrush(QColor("#8B5E4A"))
    p.drawRoundedRect(QRectF(39, -60, 92, 71), 30, 26)
    ell(67, -60, 35, 18, "#734A3A")
    p.setBrush(QColor("#5A3A2E"))
    p.drawRect(QRectF(39, -4, 92, 14))
    for x, angle in ((-32, -32), (149, 32)):
        p.save()
        p.translate(x + 26.5, -14 + 16)
        p.rotate(angle)
        ell(-26.5, -16, 53, 32, "#7A5242")
        p.restore()
    ell(-11, 0, 191, 28, "#7A5242")
    p.end()
    return pm


def icone_appli():
    icone = QIcon()
    for t in (16, 24, 32, 48, 64, 128, 256):
        icone.addPixmap(dessiner_icone(t))
    return icone


STYLE_MENU = """
QMenu { background: #262628; color: #ececee; border: 1px solid rgba(255,255,255,30);
        border-radius: 12px; padding: 6px; font-family: 'Segoe UI'; font-size: 11pt; }
QMenu::item { padding: 8px 22px 8px 14px; border-radius: 8px; }
QMenu::item:selected { background: #FFD23F; color: #1d1d1f; }
QMenu::separator { height: 1px; background: rgba(255,255,255,20); margin: 4px 6px; }
"""


def nouveau_menu():
    m = QMenu()
    m.setStyleSheet(STYLE_MENU)
    m.setWindowFlags(m.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
    m.setAttribute(Qt.WA_TranslucentBackground)
    return m


# ----------------------------------------------------------------- fenêtre web commune
class FenetreWeb(QWebEngineView):
    def __init__(self, page, pont, drapeaux):
        super().__init__()
        self.setWindowFlags(drapeaux)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.page().setBackgroundColor(Qt.transparent)
        reglages = self.page().settings()
        reglages.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        reglages.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        self.pont = pont
        self.canal = QWebChannel(self.page())
        self.canal.registerObject("pont", pont)
        self.page().setWebChannel(self.canal)
        self.setWindowIcon(icone_appli())
        self.load(QUrl.fromLocalFile(os.path.join(DOSSIER_WEB, page)))
        # Les yeux du canard suivent la souris, même en dehors de la fenêtre.
        self._yeux = QTimer(self)
        self._yeux.timeout.connect(self._suivre_souris)
        self._yeux.start(33)
        self.source_niveau = lambda: 0.0

    def _suivre_souris(self):
        if not self.isVisible():
            return
        pos = QCursor.pos() - self.pos()
        self.pont.souris.emit(pos.x(), pos.y())
        self.pont.niveau.emit(float(self.source_niveau()))

    def deplacer(self):
        fenetre = self.windowHandle()
        if fenetre is not None:
            fenetre.startSystemMove()


# ----------------------------------------------------------------- la barre
class PontBarre(QObject):
    # vers la page
    etat = Signal(str)
    evenement = Signal(str, str)
    niveau = Signal(float)
    souris = Signal(int, int)
    # vers l'appli
    demande_ecouter = Signal()
    demande_reglage = Signal(str, object)
    demande_quitter = Signal()
    demande_masquer = Signal()
    demande_retenir = Signal(float)
    demande_micros = Signal()
    demande_mes_mots = Signal()

    def __init__(self):
        super().__init__()
        self.fenetre = None
        self.page_prete = False
        self._attente = []

    @Slot()
    def pret(self):
        self.page_prete = True
        for f in self._attente:
            f()
        self._attente.clear()

    def quand_pret(self, f):
        if self.page_prete:
            f()
        else:
            self._attente.append(f)

    @Slot()
    def ecouter(self):
        self.demande_ecouter.emit()

    @Slot(str, bool)
    def reglage(self, cle, valeur):
        self.demande_reglage.emit(cle, valeur)

    @Slot(str, str)
    def choix(self, cle, valeur_json):
        self.demande_reglage.emit(cle, json.loads(valeur_json))

    @Slot()
    def quitter(self):
        self.demande_quitter.emit()

    @Slot()
    def masquer(self):
        self.demande_masquer.emit()

    @Slot()
    def mesMots(self):
        self.demande_mes_mots.emit()

    @Slot()
    def panneauOuvert(self):
        self.demande_micros.emit()

    @Slot(float)
    def retenir(self, secondes):
        self.demande_retenir.emit(secondes)

    @Slot(str)
    def zones(self, rectangles_json):
        if self.fenetre is not None:
            self.fenetre.appliquer_zones(json.loads(rectangles_json))

    @Slot()
    def deplacer(self):
        if self.fenetre is not None:
            self.fenetre.deplacer()


class Barre(FenetreWeb):
    """La barre flottante avec le canard. Ne prend jamais le focus :
    le curseur reste dans ta zone de texte."""
    deplacee = Signal(int, int)

    def __init__(self):
        pont = PontBarre()
        super().__init__("barre.html", pont, Qt.FramelessWindowHint | Qt.Tool
                         | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus)
        pont.fenetre = self
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowTitle("Canard Dictée")
        self.ancre = QPoint(0, 0)      # milieu du bas de la fenêtre
        # La fenêtre ne change JAMAIS de taille (sinon l'image saute pendant les animations).
        # Seules les parties visibles (canard, menus, bulles) attrapent la souris :
        # ailleurs, les clics passent aux fenêtres de derrière (masque).
        self.resize(LARGEUR_BARRE, self.hauteur_fixe())
        self.appliquer_zones([[LARGEUR_BARRE // 2 - 150, self.height() - 175, 300, 175]])
        self._sauver = QTimer(self)
        self._sauver.setSingleShot(True)
        self._sauver.timeout.connect(lambda: self.deplacee.emit(self.ancre.x(), self.ancre.y()))

    def placer(self, position=None):
        if position:
            x, y = position
            for s in QGuiApplication.screens():
                if s.availableGeometry().adjusted(-40, -40, 40, 40).contains(QPoint(x, y - 10)):
                    self.ancre = QPoint(x, y)
                    self._poser()
                    return
        ecran = QGuiApplication.primaryScreen().availableGeometry()
        self.ancre = QPoint(ecran.center().x(), ecran.bottom() - 12)
        self._poser()

    def hauteur_max_panneau(self):
        ecran = self.screen().availableGeometry() if self.screen() else \
            QGuiApplication.primaryScreen().availableGeometry()
        return max(240, min(640, ecran.height() - 190))

    def hauteur_fixe(self):
        # barre (16 + 72) + écart (52) + plus grand menu + ombre + place pour le petit rebond
        return 16 + 72 + 52 + self.hauteur_max_panneau() + 30 + 40

    def _poser(self):
        self.setGeometry(QRect(self.ancre.x() - LARGEUR_BARRE // 2,
                               self.ancre.y() - self.hauteur_fixe(),
                               LARGEUR_BARRE, self.hauteur_fixe()))

    def appliquer_zones(self, rectangles):
        zone = QRegion()
        for x, y, l, h in rectangles:
            zone = zone.united(QRegion(int(x), int(y), int(l) + 1, int(h) + 1))
        if not zone.isEmpty():
            self.setMask(zone)

    def moveEvent(self, e):
        super().moveEvent(e)
        nouvelle = QPoint(self.x() + self.width() // 2, self.y() + self.height())
        if nouvelle != self.ancre:
            self.ancre = nouvelle
            self._sauver.start(600)

    def showEvent(self, e):
        super().showEvent(e)
        self.evenement("entree")

    def etat(self, donnees):
        texte = json.dumps(donnees, ensure_ascii=False)
        self.pont.quand_pret(lambda: self.pont.etat.emit(texte))

    def evenement(self, nom, donnee=""):
        if not isinstance(donnee, str):
            donnee = json.dumps(donnee, ensure_ascii=False)
        self.pont.quand_pret(lambda: self.pont.evenement.emit(nom, donnee))

    def message(self, texte, duree=0):
        self.evenement("message", {"texte": texte, "duree": duree})


# ----------------------------------------------------------------- l'assistant d'installation
class PontAssistant(QObject):
    etat = Signal(str)
    niveau = Signal(float)
    souris = Signal(int, int)
    progression = Signal(int, str)
    demande_micro = Signal(object)
    demande_test = Signal(bool)
    demande_installer = Signal(dict)
    demande_terminer = Signal(bool)

    def __init__(self):
        super().__init__()
        self.fenetre = None
        self.page_prete = False
        self.etat_initial = "{}"

    @Slot()
    def pret(self):
        self.page_prete = True
        self.etat.emit(self.etat_initial)

    @Slot(str)
    def choisirMicro(self, valeur_json):
        self.demande_micro.emit(json.loads(valeur_json))

    @Slot(bool)
    def testerMicro(self, actif):
        self.demande_test.emit(actif)

    @Slot(str)
    def installer(self, options_json):
        self.demande_installer.emit(json.loads(options_json))

    @Slot(bool)
    def terminer(self, lancer):
        self.demande_terminer.emit(lancer)

    @Slot()
    def ouvrirDossier(self):
        os.startfile(dossier_appli())

    @Slot()
    def deplacer(self):
        if self.fenetre is not None:
            self.fenetre.deplacer()


class FenetreAssistant(FenetreWeb):
    def __init__(self):
        pont = PontAssistant()
        super().__init__("installation.html", pont, Qt.FramelessWindowHint | Qt.Window)
        pont.fenetre = self
        self.setWindowTitle("Installer Canard Dictée")
        self.resize(708, 492)

    def montrer(self):
        ecran = QGuiApplication.primaryScreen().availableGeometry()
        self.move(ecran.center() - self.rect().center())
        self.show()
        self.raise_()
        self.activateWindow()
