Sybase Adaptive Server Enterprise ODBC Driver Sample Programs
-------------------------------------------------------------

Purpose
-------
This directory contains sample ODBC applications that illustrate how to use
the Sybase ASE ODBC Driver.

Requirements
------------
These samples assume that
 - pubs2 database is installed on the Sybase ASE server
 - a VC++ compiler is installed
 - Microsoft ODBC driver manager is used
  


Microsoft ODBC Driver Manager
-----------------------
The Microsoft ODBC Driver Manager is included with all Windows installs.


Installing Adaptive Server Enterprise ODBC Driver
-------------------------------------------------
Install the ASE ODBC driver using the regsvr32 tool using the following command:
regsvr32 FULL_INSTALLPATH_TO_DRIVER\sybdrvodb.dll where FULL_INSTALLPATH_TO_DRIVER is 
the complete install path to the driver.


Installing sampledsn DataSource
-------------------------------
Install the ASE ODBC datasource using the Microsoft DataSources Administrator.
Launch the Datasource Administrator from ControlPanel->Administrative Tools->Data Sources

You can install the datasource either as a User DataSource or a System DataSource.


Using Microsoft VisualStudio.NET 2008 to build and run the samples
-------------------------------------------------------------------
Open the odbcsamples.sln using Microsoft Visual Studio.NET 2008. 
To compile the application:
#Right Click the <samplename> project and choose Build to build the sample. 

To run the sample
#Right Click the <samplename> project and choose Debug->Start New Instance to run the sample.


Using batch file to build and run the samples
-----------------------------------------------
To compile the application from the samples directory:
ANSI:
# build <samplename> compile
UNICODE:
# build <samplename> compile unicode

To run the application from the samples directory:
# build <samplename> run

To delete all generated files from the samples directory:
# build <samplename> clean

To link directly to the driver set DM_LIBRARY to the absolute path of sybdrvodb.lib and make sure that the driver dll is reachable from %PATH%
