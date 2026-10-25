#ifndef MyAppName
#define MyAppName "OpenLaunchDeck"
#endif
#ifndef MyAppVersion
#define MyAppVersion "0.2.11"
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
AppPublisherURL=https://github.com/Riqqqque/OpenLaunchDeck
AppSupportURL=https://github.com/Riqqqque/OpenLaunchDeck/issues/new/choose
AppUpdatesURL=https://github.com/Riqqqque/OpenLaunchDeck/releases/latest
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
UninstallDisplayIcon={app}\OpenLaunchDeck.ico
VersionInfoDescription=Launchpad Mini MK3 macro deck for Windows
SetupIconFile=..\openlaunchdeck\resources\icons\openlaunchdeck.ico
SetupLogging=yes
; Upgrades wipe {app}\_internal first, so the uninstall log only needs this version's
; files. Appending (the default) grows unins000.dat with every upgrade.
UninstallLogMode=overwrite

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\OpenLaunchDeck\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\openlaunchdeck\resources\icons\openlaunchdeck.ico"; DestDir: "{app}"; DestName: "OpenLaunchDeck.ico"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\OpenLaunchDeck.ico"; IconIndex: 0; AppUserModelID: "Rique.OpenLaunchDeck"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\OpenLaunchDeck.ico"; IconIndex: 0; AppUserModelID: "Rique.OpenLaunchDeck"; Tasks: desktopicon

[Run]
; Setup is 32-bit, so {sys} is SysWOW64 on 64-bit Windows, which has no ie4uinit.exe.
Filename: "{sysnative}\ie4uinit.exe"; Parameters: "-show"; Flags: runhidden waituntilterminated skipifdoesntexist; Check: IsWin64
Filename: "{sys}\ie4uinit.exe"; Parameters: "-show"; Flags: runhidden waituntilterminated skipifdoesntexist; Check: not IsWin64
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
; In-app one-click updates run silently with /RELAUNCH=1, so reopen the app (as the signed-in user, not elevated).
Filename: "{app}\{#MyAppExeName}"; Flags: nowait runasoriginaluser; Check: RelaunchAfterSilentUpdate

[Messages]
BeveledLabel=Profiles and settings are stored in AppData and are preserved during updates.

[Code]
function RelaunchAfterSilentUpdate: Boolean;
begin
  Result := WizardSilent and (ExpandConstant('{param:RELAUNCH|0}') = '1');
end;
