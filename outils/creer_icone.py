# -*- coding: utf-8 -*-
"""Fabrique icone.ico (le canard au chapeau) et les images de l'installateur."""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image  # noqa: E402
from PySide6.QtCore import QBuffer, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QPainter, QPixmap, QRadialGradient  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from dictee.ui import dessiner_icone  # noqa: E402

ICI = os.path.dirname(os.path.abspath(__file__))


def vers_pil(pm):
    tampon = QBuffer()
    tampon.open(QBuffer.WriteOnly)
    pm.save(tampon, "PNG")
    return Image.open(io.BytesIO(bytes(tampon.data())))


def fond(largeur, hauteur, logo=0):
    """Fond sombre du design (#232325) avec une lueur jaune, et le canard si demandé."""
    pm = QPixmap(largeur, hauteur)
    pm.fill(QColor("#232325"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    lueur = QRadialGradient(largeur * 0.9, hauteur * 1.0, hauteur * 0.7)
    lueur.setColorAt(0, QColor(255, 210, 63, 55))
    lueur.setColorAt(1, QColor(255, 210, 63, 0))
    p.fillRect(pm.rect(), lueur)
    if logo:
        p.drawPixmap(int((largeur - logo) / 2), int(hauteur * 0.2), dessiner_icone(logo, fond=False))
    p.end()
    return pm


if __name__ == "__main__":
    app = QApplication(sys.argv)
    vers_pil(dessiner_icone(256)).save(
        os.path.join(ICI, "icone.ico"),
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    for pourcent, k in ((100, 1.0), (150, 1.5), (200, 2.0)):
        fond(int(700 * k), int(540 * k)).save(os.path.join(ICI, f"inst_fond_{pourcent}.png"))
        fond(int(164 * k), int(314 * k), int(110 * k)).save(os.path.join(ICI, f"inst_cote_{pourcent}.png"))
        dessiner_icone(int(58 * k)).save(os.path.join(ICI, f"inst_logo_{pourcent}.png"))
    print("Icône et images créées.")
