# 🦆 Canard Dictée

**Écris avec ta voix, partout dans Windows. 100 % hors ligne.**

Canard Dictée est une application de dictée vocale pour Windows 11, pensée pour être **très simple à utiliser**
(au départ pour une personne dyslexique). Un petit canard animé écoute ce que tu dis et l'écrit là où est ton
curseur : navigateur, Word, Discord, n'importe quelle zone de texte.

La reconnaissance vocale tourne **sur ton PC** (Whisper, via faster-whisper) : rien n'est envoyé sur Internet.

---

## ✨ Ce qu'il sait faire

- **Maintiens Ctrl droit et parle**, relâche : le texte s'écrit.
- **Windows + H** : remplace la saisie vocale de Windows. Le canard écoute tout de suite et s'en va quand tu as fini.
- **Mode mains libres** pour les longs textes (un appui court, puis un autre pour finir).
- **Ponctuation et majuscules automatiques** : pas besoin de dire « virgule ».
- **Détection de la fin de parole** intelligente (détecteur de voix Silero : un souffle ou un ventilateur ne compte pas).
- **« Mes mots à retenir »** : prénoms, villes, mots rares… le canard les reconnaît mieux.
- **Filtre des phrases inventées** sur le silence (« Sous-titres réalisés par Amara.org »…) et des gros mots (optionnel).
- **30 costumes** : le canard se déguise selon les mots que tu dis (pizza → chef italien, Halloween → citrouille, Minecraft → canard en cubes…).
- **Skin du canard** au choix, **animations** (il suit la souris des yeux, s'endort si tu ne bouges pas, pleure quand tu le quittes…).
- **3 modèles** : Rapide (petit PC), Équilibré, Précis (conseillé avec une carte NVIDIA).
- Choix du micro, du raccourci, du délai, lancement au démarrage de Windows.

## 📥 Installer (pour les utilisateurs)

1. Va dans l'onglet **Releases** de ce dépôt.
2. Télécharge **`Installer Canard Dictée (léger).exe`**.
3. Double-clique dessus. Si Windows affiche un écran bleu, clique sur « Informations complémentaires » puis « Exécuter quand même ».
4. Suis le canard : il te montre tout en 5 étapes.

> La version légère télécharge le modèle de reconnaissance **une seule fois** au premier lancement
> (environ 1,6 Go). Ensuite, tout marche **sans Internet**.

**Version complète (100 % hors ligne dès l'installation)** : télécharge les **3 fichiers**
`CanardDictee-complet.exe`, `CanardDictee-complet-1.bin` et `CanardDictee-complet-2.bin`,
mets-les **dans le même dossier**, puis double-clique sur `CanardDictee-complet.exe`.

**Configuration conseillée :** Windows 10/11 64 bits, 8 Go de RAM. Une carte NVIDIA rend la reconnaissance
quasi instantanée (sans elle, choisis le modèle « Rapide »).

Le mode d'emploi complet est dans [MODE-EMPLOI.txt](MODE-EMPLOI.txt).

## 🛠️ Fabriquer l'application (pour les développeurs)

Il faut **Python 3.12** et **Inno Setup 6** (`winget install JRSoftware.InnoSetup`).

```bat
build.bat          :: installateur complet, avec les modèles (≈ 3,5 Go, 100 % hors ligne)
build.bat leger    :: installateur léger, sans les modèles (< 2 Go, pour GitHub)
build.bat github   :: installateur complet coupé en morceaux de moins de 2 Go (pour GitHub)
```

`build.bat` installe les bibliothèques, télécharge les modèles, fabrique l'exe (PyInstaller) puis l'installateur (Inno Setup).

Lancer depuis le code, sans fabriquer :

```bat
pip install -r requirements.txt
python main.py
```

### Organisation du code

| Dossier / fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée |
| `dictee/app.py` | Chef d'orchestre : raccourcis, écoute, écriture, paramètres, assistant d'installation |
| `dictee/audio.py` | Micro (toujours prêt, 0,5 s gardée avant l'appui), sons, détection de voix |
| `dictee/moteur.py` | Reconnaissance vocale (faster-whisper) |
| `dictee/texte.py` | Nettoyage du texte (phrases inventées, ponctuation, gros mots) |
| `dictee/clavier.py` | Raccourci global, Windows + H, écriture par le presse-papiers |
| `dictee/lanceur.py` | Détecte si le curseur est dans une zone de texte (UI Automation) |
| `dictee/vocabulaire.py` | « Mes mots à retenir » |
| `dictee/ui.py` | Fenêtres Qt qui affichent l'interface web, icône du canard |
| `dictee/web/` | L'interface du canard (HTML/CSS/JS) : barre, menus, costumes, assistant |
| `outils/` | Icône et images de l'installateur, import du dessin du canard depuis le design |
| `tests/` | Tests (voir ci-dessous) |

### Tests

```bat
python tests\test_texte.py              :: nettoyage du texte
python tests\test_reconnaissance.py     :: reconnaissance (voix de synthèse française de Windows)
python -m tests.test_silence            :: détection de fin de parole
python -m tests.test_costumes           :: mots magiques → costumes
python -m tests.test_logique            :: logique des raccourcis (sans toucher au clavier)
```

⚠️ `tests/test_appli.py` envoie de **vraies touches** au clavier : ne pas toucher au PC pendant qu'il tourne.

## 🙏 Merci à

- [OpenAI Whisper](https://github.com/openai/whisper) et [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — licence MIT
- [Silero VAD](https://github.com/snakers4/silero-vad) — licence MIT
- [Qt for Python (PySide6)](https://doc.qt.io/qtforpython/) — licence LGPL v3
- Police [Nunito](https://fonts.google.com/specimen/Nunito) — SIL Open Font License 1.1
- [Material Symbols](https://fonts.google.com/icons) — licence Apache 2.0
- [pynput](https://github.com/moses-palmer/pynput), [sounddevice](https://python-sounddevice.readthedocs.io/), [uiautomation](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)

## 📄 Licence

Canard Dictée est publié sous licence [Apache 2.0](LICENSE).

