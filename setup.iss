[Setup]
AppName=TEG Carwash Ticket Generator
AppVersion=1.0
DefaultDirName={pf}\TEGCarwash
DefaultGroupName=TEG Carwash
OutputDir=Output
OutputBaseFilename=TEGCarwashSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\teg_app.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TEG Carwash"; Filename: "{app}\teg_app.exe"
Name: "{commondesktop}\TEG Carwash"; Filename: "{app}\teg_app.exe"

