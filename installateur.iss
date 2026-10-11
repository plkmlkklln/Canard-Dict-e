; Installateur Canard Dictée. Compilé par build.bat.
; Inno Setup copie seulement les fichiers (quelques secondes) ; ensuite l'assistant du canard
; (design « Installation » : bienvenue, options, micro, installation, fin) s'ouvre tout seul.
#define Version "2.0.0"

[Setup]
AppId={{6C1E7B54-2D8A-4E0F-9C3B-1A7D5E9F4B21}
AppName=Canard Dictée
AppVersion={#Version}
AppPublisher=Canard Dictée
DefaultDirName={localappdata}\Programs\CanardDictee
UsePreviousAppDir=no
DefaultGroupName=Canard Dictée
DisableProgramGroupPage=yes
DisableDirPage=yes
DisableReadyPage=yes
DisableWelcomePage=yes
DisableFinishedPage=yes
PrivilegesRequired=lowest
OutputDir=.
; Version « légère » (build.bat leger) : sans les modèles vocaux, pour GitHub (fichiers < 2 Go).
; Les modèles sont alors téléchargés une seule fois, au premier lancement.
#ifdef LEGER
OutputBaseFilename=Installer Canard Dictée (léger)
#elif defined(GITHUB)
; Version complète pour GitHub (build.bat github) : coupée en morceaux de moins de 2 Go,
; car GitHub refuse les fichiers plus gros. Noms sans espaces ni accents : GitHub les renomme sinon,
; et l'installateur ne retrouverait plus ses morceaux.
OutputBaseFilename=CanardDictee-complet
DiskSpanning=yes
DiskSliceSize=1900000000
SlicesPerDisk=1
#else
OutputBaseFilename=Installer Canard Dictée
#endif
SetupIconFile=outils\icone.ico
UninstallDisplayIcon={app}\CanardDictee.exe
UninstallDisplayName=Canard Dictée
; Les modèles vocaux ne se compressent presque pas : sans compression, l'installation est bien plus rapide.
#ifdef LEGER
Compression=lzma2/fast
#else
Compression=none
#endif
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
; Si le canard est ouvert, l'installateur demande de le fermer (mises à jour).
AppMutex=DicteeVocale_UneSeuleFois
WizardStyle=modern dark windows11 hidebevels includetitlebar
WizardBackColor=#232325
WizardBackColorDynamicDark=#232325
WizardBackImageFile=outils\inst_fond_100.png,outils\inst_fond_150.png,outils\inst_fond_200.png
WizardImageFile=outils\inst_cote_100.png,outils\inst_cote_150.png,outils\inst_cote_200.png
WizardSmallImageFile=outils\inst_logo_100.png,outils\inst_logo_150.png,outils\inst_logo_200.png
WizardSizePercent=100

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"

[LangOptions]
DialogFontSize=11

[Messages]
SetupWindowTitle=Canard Dictée
WizardInstalling=Le canard prépare ses affaires…
InstallingLabel=Quelques secondes. Ensuite, le canard te dit bonjour.

[InstallDelete]
; Ancienne version « Dictée vocale »
Type: filesandordirs; Name: "{localappdata}\Programs\DicteeVocale"
Type: files; Name: "{userdesktop}\Dictée vocale.lnk"
Type: filesandordirs; Name: "{userprograms}\Dictée vocale"

[Files]
#ifndef APERCU
Source: "dist\CanardDictee\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifndef LEGER
Source: "modeles\small\*"; DestDir: "{app}\modeles\small"; Excludes: ".cache"; Flags: ignoreversion recursesubdirs
Source: "modeles\large-v3-turbo\*"; DestDir: "{app}\modeles\large-v3-turbo"; Excludes: ".cache"; Flags: ignoreversion recursesubdirs
#endif
#endif
Source: "MODE-EMPLOI.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Canard Dictée"; Filename: "{app}\CanardDictee.exe"
Name: "{group}\Mode d'emploi"; Filename: "{app}\MODE-EMPLOI.txt"
Name: "{group}\Désinstaller Canard Dictée"; Filename: "{uninstallexe}"

[Run]
; L'assistant du canard (les options, le test du micro, la fin).
Filename: "{app}\CanardDictee.exe"; Parameters: "--bienvenue"; Flags: nowait skipifsilent

[UninstallRun]
Filename: "taskkill.exe"; Parameters: "/IM CanardDictee.exe /F"; Flags: runhidden; RunOnceId: "Fermer"

[UninstallDelete]
Type: files; Name: "{userdesktop}\Canard Dictée.lnk"

[Code]
// À la désinstallation : on retire aussi le lancement au démarrage de Windows.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'DicteeVocale');
end;
