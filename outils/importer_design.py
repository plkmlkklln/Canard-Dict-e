# -*- coding: utf-8 -*-
"""Recopie le dessin du canard du design (« Canard Dictée.dc.html ») dans dictee/web/barre.html.

Le design utilise des modèles ({{ ... }}, <sc-if>) ; la page de l'appli est du HTML simple :
  <sc-if value="{{ cos.pizza }}">  ->  <div class="cos" data-cos="pizza">
  ref="{{ refs.nom }}"             ->  id="nom"
  {{ acc }}, {{ cheekOp }}...      ->  variables CSS (var(--acc)...), réglées par barre.js
Usage : python outils/importer_design.py [chemin du design]
"""
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ICI, "..", "dictee", "web", "barre.html")
DESIGN = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    r"~\Pictures\Canard Dictée\Canard Dictée.dc.html")

VARIABLES = {
    "acc": "var(--acc)",
    "cheekOp": "var(--joues)",
    "headZ": "var(--tete-z)",
    "hatDisplay": "block",
}
COSTUMES_SPECIAUX = {"isCuir": "cuir", "isItalie": "italie", "isFrance": "france"}


def convertir(html):
    def sc_if(m):
        val = m.group(1).strip()
        if val.startswith("cos."):
            return f'<div class="cos" data-cos="{val[4:]}">'
        if val in COSTUMES_SPECIAUX:
            return f'<div class="cos" data-cos="{COSTUMES_SPECIAUX[val]}">'
        raise ValueError("sc-if inconnu : " + val)

    html = re.sub(r'<sc-if value="\{\{\s*([^}]+?)\s*\}\}"[^>]*>', sc_if, html)
    html = html.replace("</sc-if>", "</div>")
    html = re.sub(r'ref="\{\{\s*refs\.(\w+)\s*\}\}"', r'id="\1"', html)
    html = re.sub(r'\s*style-hover="[^"]*"', "", html)
    html = html.replace('onClick="{{ toggleListen }}"', 'id="canard-bouton"')

    def variable(m):
        nom = m.group(1).strip()
        if nom not in VARIABLES:
            raise ValueError("valeur inconnue : " + nom)
        return VARIABLES[nom]

    html = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", variable, html)
    return html


def main():
    design = open(DESIGN, encoding="utf-8").read().splitlines(keepends=True)
    debut = next(i for i, l in enumerate(design) if 'onClick="{{ toggleListen }}"' in l)
    fin = next(i for i in range(debut, len(design)) if 'onClick="{{ toggleHelp }}"' in design[i])
    while not design[fin - 1].strip():
        fin -= 1
    bloc = convertir("".join(design[debut:fin]))

    page = open(PAGE, encoding="utf-8", newline="").read()
    a = page.index('    <button id="canard-bouton"')
    b = page.index('    <button id="aide-bouton"')
    page = page[:a] + bloc.rstrip() + "\n\n" + page[b:]
    open(PAGE, "w", encoding="utf-8", newline="").write(page)
    print(f"Canard importé : {fin - debut} lignes, "
          f"{len(re.findall('data-cos=', bloc))} morceaux de costumes.")


if __name__ == "__main__":
    main()
