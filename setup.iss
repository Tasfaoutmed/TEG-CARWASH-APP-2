[Setup]
AppName=TEG Carwash
AppVersion=1.0
DefaultDirName={pf}\TEG Carwash
DefaultGroupName=TEG Carwash
OutputDir=dist
OutputBaseFilename=TEG_Carwash_Installer
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico

[Files]
; includes the generated exe
Source: "dist\teg_app.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TEG Carwash"; Filename: "{app}\teg_app.exe"
Name: "{commondesktop}\TEG Carwash"; Filename: "{app}\teg_app.exe"
