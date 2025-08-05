@echo off

if "_%1%"=="_"  goto usage
if "_%2%"=="_" goto usage

isql -version> nul 2>&1
if NOT "%ERRORLEVEL%"=="0"  goto setsybase


:runsql
isql -U%2 -P%3 -S%1 -o %TMP%\version.log < getversion.sql

rem If there is any error running isql display a message to user
IF NOT ERRORLEVEL 0 goto error

rem Set the variable that getversion.sql determined
for /f "usebackq delims=" %%i in (`findstr "SET" %TMP%\version.log`) do %%i

rem Check if ASEVERSION is set properly
if "_%ASEVERSION%" == "_"  goto error

rem install common stored procedures
if "%ASEVERSION%" LEQ "150" goto common120
:commoncurrent
isql -U%2 -P%3 -S%1 -o%TMP%\sp_drv_common_%ASEVERSION%.log < sp_drv_common_%ASEVERSION%.sql
IF NOT ERRORLEVEL 0 goto error
del /Q %TMP%\sp_drv_common_%ASEVERSION%.log
goto version

:common120
isql -U%2 -P%3 -S%1 -o%TMP%\sp_drv_common_120.log < sp_drv_common_120.sql
IF NOT ERRORLEVEL 0 goto error
del /Q %TMP%\sp_drv_common_120.log

:version
if "%ASEVERSION%" GEQ "150" goto mda
echo Installing sp_version...
isql -U%2 -P%3 -S%1 -o %TMP%\sp_version.log < sp_version.sql
IF NOT ERRORLEVEL 0 goto error
del /Q %TMP%\sp_version.log

:mda
echo Wait...!!! Running ODBC MetaData SQL
isql -U%2 -P%3 -S%1 -o%TMP%\odbc_mda_%ASEVERSION%.log < odbc_mda_%ASEVERSION%.sql
IF NOT ERRORLEVEL 0 goto error
del /Q %TMP%\odbc_mda_%ASEVERSION%.log

:Success
echo ODBC Metadata SQL's Completed Sucessfully
echo .
echo NOTE: If there are any errors Please check %TMP%\odbc_mda_%ASEVERSION%.log file
goto end

:usage
echo.
echo.
echo USAGE: install_odbc_sprocs ^<server^> ^<user^> [^<pass^>]
echo.
echo.
echo Example : Windows, This Batch can be run thru Windows Only
echo ---------------------------------------------------------------------
echo USAGE :install_odbc_sprocs  myaseserver login1 pass1  - where myaseserver is the ServerName running on machine: Mymachine
echo.
goto end

:error
 echo Not Able to get Connection to your ASE Server : ^<%1%^>
 echo Pls. Check the Parameters Passed are Correct or
 echo Check if ASE server is up and running...
 goto end

:setsybase
 if not exist "%SYBASE%\SYBASE.BAT" goto nosybase
 CALL "%SYBASE%\SYBASE.BAT"
 set PATH=%PATH%;%windir%\system32
 goto runsql
 
 :nosybase
 echo Either SYBASE is not installed of Envirnoment variable SYBASE is not Set...
 goto end

:end
set ASEVERSION=
del /Q %TMP%\version.log


