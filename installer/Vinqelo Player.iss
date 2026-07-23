#define AppName "Vinqelo Player"
#define AppVersion "0.7.2"
#define AppPublisher "Irán Quintero"
#define AppExeName "Vinqelo Player.exe"

[Setup]
AppId={{A7F4C55B-4F6D-4E89-AF76-AE851702D68B}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=mailto:vinqeloapp@gmail.com
AppSupportURL=mailto:vinqeloapp@gmail.com
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
ShowLanguageDialog=yes
SetupIconFile=..\assets\icons\vinqelo.ico
UninstallDisplayIcon={app}\{#AppExeName}
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=Vinqelo Player Setup {#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
ChangesAssociations=yes
CloseApplications=yes
RestartApplications=no
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Instalador de {#AppName}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"

[CustomMessages]
es.AssociateAudio=Asociar MP3, FLAC, WAV, OGG, M4A y AAC con Vinqelo Player
en.AssociateAudio=Associate MP3, FLAC, WAV, OGG, M4A and AAC with Vinqelo Player
pt.AssociateAudio=Associar MP3, FLAC, WAV, OGG, M4A e AAC ao Vinqelo Player
fr.AssociateAudio=Associer MP3, FLAC, WAV, OGG, M4A et AAC à Vinqelo Player
de.AssociateAudio=MP3, FLAC, WAV, OGG, M4A und AAC mit Vinqelo Player verknüpfen
it.AssociateAudio=Associa MP3, FLAC, WAV, OGG, M4A e AAC a Vinqelo Player

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "fileassoc"; Description: "{cm:AssociateAudio}"; Flags: checkedonce

[Files]
Source: "..\dist\Vinqelo Player Portable.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion
Source: "..\assets\icons\files\*.ico"; DestDir: "{app}\file-icons"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; El idioma elegido al iniciar el asistente también será el idioma inicial de Vinqelo.
Root: HKCU; Subkey: "Software\Vinqelo\Vinqelo Player\interface"; ValueType: string; ValueName: "language"; ValueData: "{language}"
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "Vinqelo Player"; ValueData: "Software\Vinqelo Player\Capabilities"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Vinqelo Player\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "Vinqelo Player"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Vinqelo Player\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Reproductor de música local"; Tasks: fileassoc

Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.mp3"; ValueType: string; ValueName: ""; ValueData: "Vinqelo MP3"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.mp3\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\file-icons\vinqelo-mp3.ico"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.mp3\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.mp3\OpenWithProgids"; ValueType: none; ValueName: "VinqeloPlayer.mp3"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Vinqelo Player\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mp3"; ValueData: "VinqeloPlayer.mp3"; Tasks: fileassoc

Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.flac"; ValueType: string; ValueName: ""; ValueData: "Vinqelo FLAC"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.flac\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\file-icons\vinqelo-flac.ico"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.flac\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.flac\OpenWithProgids"; ValueType: none; ValueName: "VinqeloPlayer.flac"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Vinqelo Player\Capabilities\FileAssociations"; ValueType: string; ValueName: ".flac"; ValueData: "VinqeloPlayer.flac"; Tasks: fileassoc

Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.wav"; ValueType: string; ValueName: ""; ValueData: "Vinqelo WAV"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.wav\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\file-icons\vinqelo-wav.ico"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.wav\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.wav\OpenWithProgids"; ValueType: none; ValueName: "VinqeloPlayer.wav"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Vinqelo Player\Capabilities\FileAssociations"; ValueType: string; ValueName: ".wav"; ValueData: "VinqeloPlayer.wav"; Tasks: fileassoc

Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.ogg"; ValueType: string; ValueName: ""; ValueData: "Vinqelo OGG"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.ogg\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\file-icons\vinqelo-ogg.ico"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.ogg\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.ogg\OpenWithProgids"; ValueType: none; ValueName: "VinqeloPlayer.ogg"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Vinqelo Player\Capabilities\FileAssociations"; ValueType: string; ValueName: ".ogg"; ValueData: "VinqeloPlayer.ogg"; Tasks: fileassoc

Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.m4a"; ValueType: string; ValueName: ""; ValueData: "Vinqelo M4A"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.m4a\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\file-icons\vinqelo-m4a.ico"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.m4a\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.m4a\OpenWithProgids"; ValueType: none; ValueName: "VinqeloPlayer.m4a"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Vinqelo Player\Capabilities\FileAssociations"; ValueType: string; ValueName: ".m4a"; ValueData: "VinqeloPlayer.m4a"; Tasks: fileassoc

Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.aac"; ValueType: string; ValueName: ""; ValueData: "Vinqelo AAC"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.aac\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\file-icons\vinqelo-aac.ico"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\VinqeloPlayer.aac\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.aac\OpenWithProgids"; ValueType: none; ValueName: "VinqeloPlayer.aac"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Vinqelo Player\Capabilities\FileAssociations"; ValueType: string; ValueName: ".aac"; ValueData: "VinqeloPlayer.aac"; Tasks: fileassoc

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
