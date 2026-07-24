[Setup]
AppName=SUBE Local Gateway
AppVersion=1.0
DefaultDirName={pf}\SUBE-Local-Gateway
DefaultGroupName=SUBE Local Gateway
UninstallDisplayIcon={app}\sube-local-gateway.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=SUBE-Local-Gateway-Setup
SetupIconFile=app\favicon.ico

[Files]
Source: "dist\sube-local-gateway.exe"; DestDir: "{app}"

[Icons]
Name: "{userstartup}\SUBE Local Gateway"; Filename: "{app}\sube-local-gateway.exe"
Name: "{userdesktop}\SUBE Local Gateway Logs"; Filename: "{app}\backend.log"
Name: "{group}\SUBE Local Gateway"; Filename: "{app}\sube-local-gateway.exe"
Name: "{group}\Desinstalar"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\sube-local-gateway.exe"; Description: "Start the server now"; Flags: postinstall nowait skipifsilent