Ado Visual Basic sample

Purpose
-------
The adovbsample is a Visual Basic project that uses the ADO API to demonstrate some 
simple concepts in writing ADO code and applying it to applications that connect to Sybase ASE, 
using the Sybase ASE ODBC Driver .   


Select
-------
Demonstrates a SELECT statememt on the table ado_table. 
This table contains an integer datatype, character datatype, numeric datatype and datetime datetype.  
The sample also demonstrates how to gather some metadata information such as column name and 
datatype through the ADO field object.  Data from the select statement is displayed.  


Stored Procedure Input
----------------------
Demonstrates how to send one INPUT parameter and the response contains a result set 
(for the ADO Recordset).


Stored Procedure Output
-----------------------
Demonstrates how to retrieve an output parameter when the stored procedure returns a result set 
and an output parameter value. Note that the Sybase ASE ODBC Driver can only retrieve the 
output parameter value AFTER closing the Recordset when using the DEFAULT CursorLocation of 
adUseServer. If there is no result set returned by the stored procedure you will be able to 
retrieve the output parameter value immediately after execution.


Procedure
----------
Using Microsoft Visual Studio.NET 2003
--------------------------------------

Open the Solution file using Microsoft Visual Studio.NET 2003. 

To compile the sample
#Select the adovbsample project.Choose Build->adovbsample to build the sample.

To run the sample
#Right Click the adovbsample project and choose Debug->Start New Instance to run the sample.

