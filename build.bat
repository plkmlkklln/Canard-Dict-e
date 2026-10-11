@echo off
rem Fabrique dist\CanardDictee\CanardDictee.exe puis "Installer Canard Dictee.exe"
title Fabrication - Dictee vocale
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

echo [1/5] Bibliotheques...
"%PY%" -m pip install -q -r requirements.txt -r requirements-build.txt || goto erreur

echo [2/5] Modeles de reconnaissance (une seule fois, environ 2 Go)...
"%PY%" -c "from faster_whisper.utils import download_model as d; [d(n, output_dir='modeles/'+n) for n in ('small','large-v3-turbo')]" || goto erreur

echo [3/5] Icone...
"%PY%" outils\creer_icone.py || goto erreur

echo [4/5] Programme (PyInstaller)...
"%PY%" -m PyInstaller DicteeVocale.spec --noconfirm --clean || goto erreur

echo [5/5] Installateur (Inno Setup)...
set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
  echo Inno Setup manque. Installe-le : winget install JRSoftware.InnoSetup
  goto erreur
)
rem « build.bat leger » : installateur sans les modèles (pour GitHub, moins de 2 Go)
if /i "%~1"=="leger" (
  "%ISCC%" /Q /DLEGER installateur.iss || goto erreur
) else if /i "%~1"=="github" (
  rem « build.bat github » : version complète coupée en morceaux de moins de 2 Go
  "%ISCC%" /Q /DGITHUB installateur.iss || goto erreur
) else (
  "%ISCC%" /Q installateur.iss || goto erreur
)

echo.
echo Termine ! L'installateur est "Installer Canard Dictee.exe".
pause
exit /b 0

:erreur
echo.
echo Il y a eu un probleme. Lis le message au-dessus.
pause
exit /b 1
