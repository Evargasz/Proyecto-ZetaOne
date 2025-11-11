; Script de Inno Setup para ZetaOne v1.4.1

[Setup]
; --- Identificador ÚNICO de la aplicación. ¡No cambiar en futuras versiones! ---
; Esto es lo que permite que el instalador pise y reemplace versiones anteriores.
AppId={{E5D9F8A0-B3C1-4E6F-9D8A-7C6B4A1E9F0F}}

AppName=ZetaOne
AppVersion=1.4.1
AppPublisher=BAC
DefaultDirName={sd}\ZetaOne
DefaultGroupName=ZetaOne
DisableProgramGroupPage=yes
OutputDir=.\instalador_generado
OutputBaseFilename=ZetaOne_Setup_v1.4.1
; --- CORRECCIÓN: Ruta del icono ajustada a la estructura del proyecto ---
SetupIconFile=imagenes_iconos\Zeta99.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Pide permisos de administrador, necesarios para instalar drivers y escribir en C:\
PrivilegesRequired=admin
; --- SOLUCIÓN: Asegurar que la instalación sea siempre para todos los usuarios ---
PrivilegesRequiredOverridesAllowed=commandline


[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un icono en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
; 1. Copia la aplicación completa (generada por PyInstaller)
Source: "dist\ZetaOne\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 2. Copia los instaladores de los drivers y requisitos
;    (Asegúrate de que estos archivos estén en la raíz de tu proyecto)
Source: "msodbcsql.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "ODBC\*"; DestDir: "{app}\ODBC"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; --- SOLUCIÓN: Limpiar accesos directos antiguos que pudieran existir en el perfil del usuario ---
Type: files; Name: "{userprograms}\ZetaOne\ZetaOne.lnk"
Type: dirifempty; Name: "{userprograms}\ZetaOne"

[Icons]
; Crea los accesos directos en el Menú Inicio y Escritorio
Name: "{commonprograms}\ZetaOne\ZetaOne"; Filename: "{app}\ZetaOne.exe"
Name: "{autodesktop}\ZetaOne"; Filename: "{app}\ZetaOne.exe"; Tasks: desktopicon

[Run]
; 3. Ejecuta el instalador del driver de SQL Server de forma silenciosa
Filename: "msiexec.exe"; Parameters: "/i ""{tmp}\msodbcsql.msi"" /quiet /qn IACCEPTMSODBCSQLLICENSETERMS=YES"; \
    StatusMsg: "Instalando drivers de SQL Server..."; Flags: waituntilterminated

[Registry]
; 4. Registra el driver ODBC de Sybase de forma robusta en el registro de Windows
;    Esto asegura que aparezca en el "Administrador de Orígenes de Datos ODBC".
Root: HKLM; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver"; ValueType: string; ValueName: "Driver"; ValueData: "{app}\ODBC\dll\sybdrvodb.dll"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver"; ValueType: string; ValueName: "Setup"; ValueData: "{app}\ODBC\dll\sybdrvodb.dll"
Root: HKLM; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers"; ValueType: string; ValueName: "Sybase ASE ODBC Driver"; ValueData: "Installed"