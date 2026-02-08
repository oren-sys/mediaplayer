[Setup]
AppName=MediaPlayer
AppVersion=1.0.0
AppId={{B8F3A2E1-4D7C-4F9A-8E2B-1A3C5D7F9E0B}
AppPublisher=MediaPlayer
AppPublisherURL=https://github.com
DefaultDirName={autopf}\MediaPlayer
DefaultGroupName=MediaPlayer
UninstallDisplayIcon={app}\MediaPlayer.exe
OutputDir=installer_output
OutputBaseFilename=MediaPlayer-Setup-1.1.0
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
SetupIconFile=
LicenseFile=
PrivilegesRequired=lowest
CloseApplications=force
RestartApplications=no

[InstallDelete]
; Clean old installation files before overwriting (preserves data/ folder with DB and posters)
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\MediaPlayer.exe"
Type: files; Name: "{app}\.env.example"
Type: files; Name: "{app}\SearchO.exe"

[Files]
Source: "dist\MediaPlayer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".env.example"; DestDir: "{app}"; DestName: ".env.example"; Flags: ignoreversion
Source: ".env"; DestDir: "{app}"; DestName: ".env"; Flags: ignoreversion onlyifdoesntexist
Source: "C:\Users\Oren\Projects\SearchO\dist\SearchO.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MediaPlayer"; Filename: "{app}\MediaPlayer.exe"
Name: "{group}\Uninstall MediaPlayer"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MediaPlayer"; Filename: "{app}\MediaPlayer.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\SearchO.exe"; Flags: runhidden nowait skipifsilent
Filename: "{app}\MediaPlayer.exe"; Description: "Launch MediaPlayer"; Flags: nowait postinstall skipifsilent

[Registry]
; Register file associations for common video formats
Root: HKCU; Subkey: "Software\Classes\.mp4\OpenWithProgids"; ValueType: string; ValueName: "MediaPlayer.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.mkv\OpenWithProgids"; ValueType: string; ValueName: "MediaPlayer.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.avi\OpenWithProgids"; ValueType: string; ValueName: "MediaPlayer.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.webm\OpenWithProgids"; ValueType: string; ValueName: "MediaPlayer.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.flv\OpenWithProgids"; ValueType: string; ValueName: "MediaPlayer.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.mov\OpenWithProgids"; ValueType: string; ValueName: "MediaPlayer.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.wmv\OpenWithProgids"; ValueType: string; ValueName: "MediaPlayer.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\MediaPlayer.Video"; ValueType: string; ValueName: ""; ValueData: "Video File"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\MediaPlayer.Video\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\MediaPlayer.exe"" ""%1"""; Flags: uninsdeletekey
