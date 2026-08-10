; Inno Setup Script for Clipper AI Desktop
; Compatible with Inno Setup 6.x

#define MyAppName "Clipper AI Desktop"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Toolbox Ninja AI"
#define MyAppExeName "ClipperAIDesktop.exe"

[Setup]
AppId={{C82B9A1A-9D45-4D62-81B3-9A1F4C50D111}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Clipper AI Desktop
DisableProgramGroupPage=yes
OutputBaseFilename=ClipperAI_Desktop_v1.0_Setup
OutputDir=output_installer
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\ClipperAIDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
