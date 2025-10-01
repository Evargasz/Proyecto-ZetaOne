; Script de Inno Setup para ZetaOne v1.4.0 (Versión Mejorada)
; Este script maneja instalaciones nuevas y actualizaciones,
; preserva los archivos de configuración del usuario y gestiona los drivers ODBC.
;
; NUEVAS FUNCIONALIDADES EN v1.4.0:
; - AutocompleteEntry mejorado con selección visual
; - Sistema de captura de pantallas y grabación de video
; - Asistente de captura automatizado
; - Mejoras en la interfaz de usuario
; - Correcciones de bugs y optimizaciones

[Setup]
// --- Identificador único para tu aplicación. ¡MUY IMPORTANTE! ---
// No cambies este valor entre versiones. Así Inno Setup sabe que está actualizando la misma app.
AppId={{F7A8E1B2-C3D4-5E6F-A1B2-C3D4E5F6A7B8}}

AppName=ZetaOne
// --- Versión de la aplicación. Increméntala en cada nueva compilación (ej. 1.1, 1.2, 2.0). ---
AppVersion=1.4.0
AppPublisher=BAC Credomatic
DefaultDirName={autopf}\ZetaOne
DefaultGroupName=ZetaOne
OutputDir=.\instalador_generado
OutputBaseFilename=ZetaOne_Setup_v1.4.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
// --- Pide privilegios de administrador, necesario para instalar drivers y escribir en HKLM. ---
PrivilegesRequired=admin

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
// --- Copia el contenido de la aplicación (la carpeta generada por PyInstaller). ---
// 'uninsneveruninstall' en los archivos JSON evita que se borren al desinstalar/actualizar.
// La primera línea copia TODO. Las siguientes solo AÑADEN flags a archivos específicos.
Source: "dist\ZetaOne_v1.4.0\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

// --- Ahora, AÑADIMOS flags a los archivos de configuración para protegerlos. ---
// 'onlyifdoesntexist' evita que se sobrescriba la configuración del usuario en una actualización.
// --- CORRECCIÓN: Se protege el archivo ofuscado 'ambientes.dat' en lugar del antiguo 'ambientes.json' ---
Source: "dist\ZetaOne_v1.4.0\json\ambientes.dat"; DestDir: "{app}\json"; Flags: uninsneveruninstall onlyifdoesntexist
Source: "dist\ZetaOne_v1.4.0\json\ambientesrelacionados.json"; DestDir: "{app}\json"; Flags: uninsneveruninstall onlyifdoesntexist
Source: "dist\ZetaOne_v1.4.0\json\Favoritos.json"; DestDir: "{app}\json"; Flags: uninsneveruninstall onlyifdoesntexist
Source: "dist\ZetaOne_v1.4.0\json\HistorialConsultas.json"; DestDir: "{app}\json"; Flags: uninsneveruninstall onlyifdoesntexist
Source: "dist\ZetaOne_v1.4.0\json\HistorialModificaciones.json"; DestDir: "{app}\json"; Flags: uninsneveruninstall onlyifdoesntexist
Source: "dist\ZetaOne_v1.4.0\json\catalogo_migracion.json"; DestDir: "{app}\json"; Flags: uninsneveruninstall onlyifdoesntexist

// --- Copia los instaladores de los drivers. ---
// El driver de SQL Server se copia a una carpeta temporal para su ejecución.
Source: "msodbcsql.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall
// Los archivos del driver de Sybase se copian a la carpeta de la aplicación.
Source: "ODBC\*"; DestDir: "{app}\ODBC"; Flags: recursesubdirs createallsubdirs

[Icons]
// --- Crea los accesos directos en el menú de inicio y escritorio. ---
Name: "{group}\ZetaOne"; Filename: "{app}\ZetaOne.exe"
Name: "{autodesktop}\ZetaOne"; Filename: "{app}\ZetaOne.exe"; Tasks: desktopicon

[Tasks]
// --- Permite al usuario elegir si quiere un icono en el escritorio. ---
Name: "desktopicon"; Description: "Crear un icono en el escritorio"; GroupDescription: "Accesos directos:";

[Run]
// --- Ejecuta el instalador del driver de SQL Server de forma silenciosa. ---
// 'waituntilterminated' asegura que la instalación del driver termine antes de continuar.
// 'Check: not IsWin64' y 'Check: IsWin64' podrían usarse si tuvieras drivers de 32 y 64 bits.
Filename: "msiexec.exe"; Parameters: "/i ""{tmp}\msodbcsql.msi"" /quiet /qn IACCEPTMSODBCSQLLICENSETERMS=YES"; \
    StatusMsg: "Instalando drivers de SQL Server..."; Flags: waituntilterminated

// --- El registro del driver de Sybase se hace ahora en la sección [Registry]. ---
// Es más robusto y gestiona correctamente la desinstalación.
// La línea de regsvr32.exe se ha eliminado para evitar redundancia.

[Registry]
// --- Registro robusto del driver ODBC de Sybase. ---
// Esta es la forma correcta de hacer que el driver aparezca en el "Administrador de Orígenes de Datos ODBC".
// 'uninsdeletekey' asegura que estas claves se eliminen limpiamente al desinstalar.

// --- Para sistemas de 64 bits, se debe escribir en la vista de 64 bits del registro. ---
Root: HKLM64; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver"; ValueType: string; ValueName: "Driver"; ValueData: "{app}\ODBC\dll\sybdrvodb.dll"; Flags: uninsdeletekey
Root: HKLM64; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver"; ValueType: string; ValueName: "Setup"; ValueData: "{app}\ODBC\dll\sybdrvodb.dll"
Root: HKLM64; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers"; ValueType: string; ValueName: "Sybase ASE ODBC Driver"; ValueData: "Installed"

// --- Para compatibilidad, también se registra en la vista de 32 bits (WOW6432Node). ---
Root: HKLM32; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver"; ValueType: string; ValueName: "Driver"; ValueData: "{app}\ODBC\dll\sybdrvodb.dll"; Flags: uninsdeletekey
Root: HKLM32; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver"; ValueType: string; ValueName: "Setup"; ValueData: "{app}\ODBC\dll\sybdrvodb.dll"
Root: HKLM32; Subkey: "SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers"; ValueType: string; ValueName: "Sybase ASE ODBC Driver"; ValueData: "Installed"

[Code]
// --- Sección de código Pascal para lógica avanzada. ---

// Esta función comprueba si un driver ODBC ya está instalado.
function IsOdbcDriverInstalled(DriverName: string): Boolean;
var
  Installed: string;
begin
  // Comprueba tanto en 64 como en 32 bits.
  if RegQueryStringValue(HKLM64, 'SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers', DriverName, Installed) then
  begin
    Result := (Installed = 'Installed');
    if Result then Exit;
  end;
  
  if RegQueryStringValue(HKLM32, 'SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers', DriverName, Installed) then
  begin
    Result := (Installed = 'Installed');
  end
  else
  begin
    Result := False;
  end;
end;

// Detecta si hay una versión anterior de ZetaOne instalada
function GetPreviousVersion(): string;
var
  Version: string;
begin
  Result := '';
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{F7A8E1B2-C3D4-5E6F-A1B2-C3D4E5F6A7B8}_is1', 'DisplayVersion', Version) then
    Result := Version;
end;

// Muestra información sobre la actualización
function InitializeSetup(): Boolean;
var
  PrevVersion: string;
  Msg: string;
begin
  Result := True;
  PrevVersion := GetPreviousVersion();
  
  if PrevVersion <> '' then
  begin
    Msg := 'Se detectó ZetaOne v' + PrevVersion + ' instalado.' + #13#10 + #13#10 +
           'Esta instalación actualizará a la versión 1.4.0 que incluye:' + #13#10 +
           '• AutocompleteEntry mejorado con selección visual' + #13#10 +
           '• Sistema de captura de pantallas y grabación' + #13#10 +
           '• Asistente de captura automatizado' + #13#10 +
           '• Mejoras en la interfaz y corrección de errores' + #13#10 + #13#10 +
           'Sus configuraciones y datos se preservarán.' + #13#10 + #13#10 +
           '¿Desea continuar con la actualización?';
    
    Result := MsgBox(Msg, mbConfirmation, MB_YESNO) = IDYES;
  end
  else
  begin
    Msg := 'Bienvenido al instalador de ZetaOne v1.4.0' + #13#10 + #13#10 +
           'Nuevas funcionalidades incluidas:' + #13#10 +
           '• Sistema completo de migración de datos' + #13#10 +
           '• Interfaz mejorada con selección visual' + #13#10 +
           '• Herramientas de captura y grabación' + #13#10 +
           '• Gestión avanzada de ambientes' + #13#10 + #13#10 +
           '¿Desea continuar con la instalación?';
    
    Result := MsgBox(Msg, mbInformation, MB_YESNO) = IDYES;
  end;
end;