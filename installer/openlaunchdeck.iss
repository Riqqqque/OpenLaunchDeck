#ifndef MyAppName
#define MyAppName "OpenLaunchDeck"
#endif
#ifndef MyAppVersion
#define MyAppVersion "0.1.11"
#endif
#define MyAppPublisher "Rique"
#define MyAppExeName "OpenLaunchDeck.exe"
#ifndef MyAppCompression
#define MyAppCompression "lzma"
#endif
#ifndef MyAppSolidCompression
#define MyAppSolidCompression "yes"
#endif

[Setup]
AppId={{6F195CC4-2DC0-40C7-A03D-99B2F61F1A0F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UsePreviousAppDir=yes
AllowNoIcons=yes
OutputDir=..\dist\installer
OutputBaseFilename=OpenLaunchDeckSetup-{#MyAppVersion}
Compression={#MyAppCompression}
SolidCompression={#MyAppSolidCompression}
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\openlaunchdeck\resources\icons\openlaunchdeck.ico
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\OpenLaunchDeck\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{sys}\ie4uinit.exe"; Parameters: "-show"; Flags: runhidden waituntilterminated skipifdoesntexist
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Messages]
BeveledLabel=Profiles and settings are stored in AppData and are preserved during updates.
