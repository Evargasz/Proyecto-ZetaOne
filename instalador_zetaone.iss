; Script de Inno Setup para ZetaOne

[Setup]
AppName=ZetaOne
AppVersion=1.0
AppPublisher=Tu Nombre o Empresa
DefaultDirName={autopf}\ZetaOne
DefaultGroupName=ZetaOne
OutputDir=.\instalador_generado
OutputBaseFilename=ZetaOne_Setup_v1.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Copia todo el contenido de tu ejecutable (la carpeta dist/ZetaOne)
Source: "dist\ZetaOne\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copia los instaladores de los drivers a una carpeta temporal durante la instalación
Source: "msodbcsql.msi"; DestDir: "{tmp}"
Source: "ODBC\*"; DestDir: "{app}\ODBC"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Crea los accesos directos
Name: "{group}\ZetaOne"; Filename: "{app}\ZetaOne.exe"
Name: "{autodesktop}\ZetaOne"; Filename: "{app}\ZetaOne.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear un icono en el escritorio"; GroupDescription: "Accesos directos:";

[Run]
; Ejecuta el instalador del driver de SQL Server de forma silenciosa
Filename: "msiexec.exe"; Parameters: "/i ""{tmp}\msodbcsql.msi"" /quiet /qn IACCEPTMSODBCSQLLICENSETERMS=YES"; \
    StatusMsg: "Instalando drivers de SQL Server..."; Flags: waituntilterminated

; Registra el driver ODBC de Sybase de forma silenciosa
; NOTA: Asegúrate de que el usuario tenga permisos de administrador.
Filename: "{sys}\regsvr32.exe"; Parameters: "/s ""{app}\ODBC\dll\sybdrvodb.dll"""; \
    StatusMsg: "Registrando drivers de Sybase..."; Flags: waituntilterminated

[Registry]
; Esta sección es más robusta para registrar el driver de Sybase.
; Define el driver para que aparezca en el "Administrador de Orígenes de Datos ODBC".
Root: HKLM; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver"; ValueType: string; ValueName: "Driver"; ValueData: "{app}\ODBC\dll\sybdrvodb.dll"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver"; ValueType: string; ValueName: "Setup"; ValueData: "{app}\ODBC\dll\sybdrvodb.dll"
Root: HKLM; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers"; ValueType: string; ValueName: "Sybase ASE ODBC Driver"; ValueData: "Installed"