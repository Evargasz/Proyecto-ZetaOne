@echo off
rem build file for the samples

if "_%1%" == "_" goto usage

set FILENAME=%1%
set ACTION=%2%
set MODE=%3%
set DSN=%4%
set UID=%5%
set PWD=%6%

rem set any compiler or linker flags here that will be used by make

set CCFLAGS=-EHsc -I%SYBASE%\DataAccess64\ODBC\include -I%SYBASE%\DataAccess\ODBC\include
set CCCOMP=cl
set OBJEXT=obj
set LINKFLAGS=%DM_LIBRARY%
if "%DM_LIBRARY%" == "" set LINKFLAGS=odbc32.lib
if "%ACTION%" == "compile" goto compile
if "%ACTION%" == "clean" goto clean
if "%ACTION%" == "run" goto run
rem since ACTION is not one of compile,clean,run it must be all
call build %FILENAME% compile %MODE%
call build %FILENAME% run %MODE%
goto end

:compile
set DCCFLAGS=
if "%MODE%" == "unicode" set DCCFLAGS=-D_UNICODE -DUNICODE
call build %FILENAME% clean
pushd %FILENAME%
nmake -f ..\makefile
popd
goto end

:clean
pushd %FILENAME%
del /Q %FILENAME%.exe
del /Q %FILENAME%.obj
popd
goto end

:run
pushd %FILENAME%
if "%DSN%" == "" goto noargs 
%FILENAME%.exe %DSN% %UID% %PWD%
goto finishrun
:noargs
%FILENAME%.exe
:finishrun
popd
goto end

:usage
echo You will need to run vcvarsall.bat before this build script will work
echo vcvarsall.bat can be found in your microsoft visual studio installation directory
echo -
echo build ^<Project Directory^> [^<Action^> [^<MODE^> [^<DSN^> ^<UID^> ^<PWD^>]]]
echo -
echo       ^<Project Directory^>:
echo       The project you want to use
echo -
echo       ^<Action^>:
echo       clean, compile or run
echo       no action will clean compile then run
echo -
echo       ^<MODE^>:
echo       unicode or ansi
echo       The default is ansi
goto end

goto end

:end
