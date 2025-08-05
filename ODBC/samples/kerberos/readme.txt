ADO Kerberos Sample
-------------------

Purpose 
--------
The Kerberos sample demonstrates the connection string format for the various Windows related data access products, the ODBC drivers and OLE DB Providers that access Sybase ASE.

Sybase Products:
-----------------
When using ODBC Data Source Administrator to setup Kerberos use the Security tab.  The properties are described below
and are the same names for both ODBC and OLEDB.  There is no GUI tool at this time for the OLE DB Provider to setup
Data Sources.

AuthenticationClient (Authentication Client as seen in the GUI):  Set this to the Kerberos software that you are using.  
Currently the values are:
mitkerberos  (Use MIT Kerberos) - when using MIT
cybersafekerberos (Use CyberSafe Kerberos) - when using CyberSafe
activedirectory (Use Active Directory) - when using Microsoft Active Directory

UserPrincipal (User Principal): The User to acquire credentials for. This is the User name registered with the Kerberos KDC.  
For mitkerberos and cybersafekerberos, if you used kinit or leash32 to get your ticket, then this parameter is optional.
If the authenticate client is activedirectory (activedirectory can be used when the windows domain
controller is the KDC), the UserPrincipal is optional and client need not use kinit in this senario. 

ServerPrincipal (Server Principal): The name of the ASE configured in the KDC.

Examples of connection strings:

ODBC:
Driver={Adaptive Server Enterprise};Server=aseHost;Port=12530;AuthenticationClient=mitkerberos;ServerPrincipal=kerbASE@KERB_TEST;UserPrincipal=kerbUser@KERB_TEST;

OLEDB:
Provider=ASEOLEDB;Data Source=aseHost:12530;AuthenticationClient=mitkerberos;ServerPrincipal=kerbASE@KERB_TEST;UserPrincipal=kerbUser@KERB_TEST;


The application
----------------
This application is self explanatory.  You pick the option of which product to use.  All of the Kerberos fields are provided and you
can edit each value to plug in your own values.  The MsgBox and Debug.Print statements are provided to demonstrate what is going
on as the run of the application progresses.  Once connected the application executes a simple SQL Statement, select count(*) from
sysobjects.  This is done so you can verify the connectivity.
