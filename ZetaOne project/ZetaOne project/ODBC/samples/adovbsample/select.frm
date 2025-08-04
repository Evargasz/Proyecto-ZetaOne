VERSION 5.00
Begin VB.Form Form1 
   BackColor       =   &H00808000&
   Caption         =   "Form1"
   ClientHeight    =   8760
   ClientLeft      =   3330
   ClientTop       =   2160
   ClientWidth     =   10470
   LinkTopic       =   "Form1"
   ScaleHeight     =   8760
   ScaleWidth      =   10470
   Begin VB.CommandButton procInOutTest 
      Caption         =   "Stored Procedure Output"
      Height          =   375
      Left            =   240
      TabIndex        =   21
      Top             =   2880
      Width           =   2055
   End
   Begin VB.CommandButton procInpTest 
      Caption         =   "Stored Procedure Input"
      Height          =   375
      Left            =   240
      TabIndex        =   18
      Top             =   3360
      Width           =   2055
   End
   Begin VB.TextBox ODBCTextBox 
      Height          =   285
      Left            =   5160
      TabIndex        =   16
      Text            =   "Adaptive Server Enterprise"
      Top             =   360
      Width           =   3255
   End
   Begin VB.TextBox ServerPortTextBox 
      BeginProperty DataFormat 
         Type            =   1
         Format          =   "0;(0)"
         HaveTrueFalseNull=   0
         FirstDayOfWeek  =   0
         FirstWeekOfYear =   0
         LCID            =   1033
         SubFormatType   =   1
      EndProperty
      Height          =   285
      Left            =   1440
      TabIndex        =   15
      Text            =   "5000"
      Top             =   2400
      Width           =   1095
   End
   Begin VB.TextBox CatalogTextBox 
      Height          =   285
      Left            =   1440
      TabIndex        =   11
      Text            =   "pubs2"
      Top             =   1680
      Width           =   1095
   End
   Begin VB.TextBox ServerNameTextBox 
      Height          =   285
      IMEMode         =   3  'DISABLE
      Left            =   1440
      TabIndex        =   10
      Text            =   "sample"
      Top             =   2040
      Width           =   1095
   End
   Begin VB.CommandButton cmdTest 
      Caption         =   "Select "
      Height          =   375
      Left            =   240
      TabIndex        =   7
      Top             =   3840
      Width           =   2055
   End
   Begin VB.TextBox passWordTextBox 
      Height          =   285
      IMEMode         =   3  'DISABLE
      Left            =   1440
      PasswordChar    =   "*"
      TabIndex        =   1
      Top             =   1320
      Width           =   1095
   End
   Begin VB.ListBox List1 
      BeginProperty DataFormat 
         Type            =   0
         Format          =   "0"
         HaveTrueFalseNull=   0
         FirstDayOfWeek  =   0
         FirstWeekOfYear =   0
         LCID            =   1033
         SubFormatType   =   0
      EndProperty
      Height          =   3375
      ItemData        =   "select.frx":0000
      Left            =   3120
      List            =   "select.frx":0002
      TabIndex        =   5
      Top             =   1320
      Width           =   6495
   End
   Begin VB.CommandButton cmdExit 
      Caption         =   "Exit"
      Height          =   375
      Left            =   240
      TabIndex        =   3
      Top             =   4320
      Width           =   2055
   End
   Begin VB.TextBox userNameTextBox 
      Height          =   285
      Left            =   1440
      TabIndex        =   0
      Text            =   "sa"
      Top             =   960
      Width           =   1095
   End
   Begin VB.Label Label12 
      BackColor       =   &H00FFFF80&
      Caption         =   $"select.frx":0004
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   975
      Left            =   240
      TabIndex        =   22
      Top             =   7080
      Width           =   9375
   End
   Begin VB.Label Label11 
      BackColor       =   &H00E0E0E0&
      Caption         =   "Copyright (c) 2003-2004 Sybase,Inc"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   480
      TabIndex        =   20
      Top             =   8280
      Width           =   6975
   End
   Begin VB.Label Label10 
      BackColor       =   &H00FFFF80&
      Caption         =   $"select.frx":010E
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   975
      Left            =   240
      TabIndex        =   19
      Top             =   6000
      Width           =   9375
   End
   Begin VB.Label Label9 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00FFFF80&
      Caption         =   "ODBC Driver"
      Height          =   255
      Left            =   3120
      TabIndex        =   17
      Top             =   360
      Width           =   1815
   End
   Begin VB.Label Label7 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00FFFF80&
      Caption         =   "Server Port:"
      DataField       =   "5000"
      Height          =   255
      Left            =   240
      TabIndex        =   14
      Top             =   2400
      Width           =   1095
   End
   Begin VB.Label Label6 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00FFFF80&
      Caption         =   "Initial Catalog:"
      Height          =   255
      Left            =   240
      TabIndex        =   13
      Top             =   1680
      Width           =   1095
   End
   Begin VB.Label Label5 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00FFFF80&
      Caption         =   "Server Name:"
      Height          =   255
      Left            =   240
      TabIndex        =   12
      Top             =   2040
      Width           =   1095
   End
   Begin VB.Label Label4 
      BackColor       =   &H00FFFF80&
      Caption         =   $"select.frx":0210
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   855
      Left            =   240
      TabIndex        =   9
      Top             =   5040
      Width           =   9375
   End
   Begin VB.Label SybSamps 
      BackColor       =   &H00FFFF80&
      Caption         =   "Sample For ODBC / OLEDB"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   735
      Left            =   240
      TabIndex        =   8
      Top             =   120
      Width           =   2295
   End
   Begin VB.Label Label2 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00FFFF80&
      Caption         =   "PASSWORD:"
      Height          =   255
      Left            =   240
      TabIndex        =   6
      Top             =   1320
      Width           =   1095
   End
   Begin VB.Label Label3 
      BackColor       =   &H00FFFF80&
      Caption         =   "Output: Heading contains Columns names and ADO datatype"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   3000
      TabIndex        =   4
      Top             =   840
      Width           =   6495
   End
   Begin VB.Label Label1 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00FFFF80&
      Caption         =   "USER ID:"
      Height          =   255
      Left            =   240
      TabIndex        =   2
      Top             =   960
      Width           =   1095
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
'SybSamps for ADO

' Copyright (c) 2003-2004  Sybase, Inc.


'
Dim sql As String       ' sql statement
Dim connStr As String   ' connection string
Dim sybConn As ADODB.Connection 'ADO Connection object
Dim sybCmd As ADODB.Command 'ADO Command object
Dim lstr As String      ' String that contains record data
Dim errLoop As ADODB.Error      'ADO Error object
Dim strError As String
Dim fieldStr As String  ' field info string
Dim sybRst As ADODB.Recordset   'ADO Recordset object
Dim sybFld As ADODB.Field       'ADO Field object
Dim sybFld2 As ADODB.Field      'ADO Field Object to collect column info
Dim sybParameter As ADODB.Parameter 'ADO Parameter object


Option Explicit

Private Sub cmdExit_Click()
On Error Resume Next
Unload Me
Set Form1 = Nothing
End Sub
Private Sub cmdTest_Click()

Dim firstRow As Boolean ' true if on first Row - to be used to make field string
Dim tmpStr As String


On Error GoTo ErrTrap

Set sybConn = New ADODB.Connection
Set sybRst = New ADODB.Recordset
Set sybCmd = New ADODB.Command
Init
sql = "select * from ado_table"

' This informs the Recordset object, sybRst to use Connection object sybConn.
' When the Recordset object is opened below, then the application uses sybConn
' to access the ASE database.
sybRst.ActiveConnection = sybConn

'If you want to limit records returned from ASE you can do it here with the
' MaxRecords Recordset property.
'sybRst.MaxRecords = 5

'This is where we open the Recordset object. Note that there are a variety of settings.
'Open recordset object: sql string (sql), connection object (sybConn), cursor type,
' lock type, option : in this case we send adCmdText
sybRst.Open sql, sybConn, adOpenForwardOnly, adLockReadOnly, adCmdText
' Get Column Names - this is very crude and will not line up with the
' output below of the actual data, but it gives you an idea on how to gather this
' type of information
TraverseRecordset
'Message Boxes are one way to get debug info.
'In this case we get the RecordCount from this select
MsgBox "RecordCount is " & sybRst.RecordCount
'Debug.Print will display the info in the Immediate Window down below
'Debug.Print "RecordCount is " & sybRst.RecordCount

'Housecleaning - close all ADO objects used
'field objects are destroyed when Recordset object is destroyed
Finish

Exit Sub

'Basic error handling when error is trapped
ErrTrap:
ErrorProcess
End Sub




Private Sub procInpTest_Click()

On Error GoTo ErrTrap
Set sybConn = New ADODB.Connection
Set sybRst = New ADODB.Recordset
Set sybCmd = New ADODB.Command
Set sybParameter = sybCmd.CreateParameter

Init
' SQL Statement to send to ASE
sybCmd.ActiveConnection = sybConn
sql = "if exists (select 1 from sysobjects where name = 'sp_ado_c3_c4') drop procedure sp_ado_c3_c4"
sybCmd.CommandText = sql
sybCmd.Execute
sql = "create procedure sp_ado_c3_c4 (@inp integer) as select c3, c4 from ado_table where c1=@inp"
sybCmd.CommandText = sql
sybCmd.Execute
' This informs the Recordset object, sybRst to use Connection object sybConn.
' When the Recordset object is opened below, then the application uses sybConn
' to access the ASE database.
sql = "sp_ado_c3_c4"
sybCmd.CommandType = adCmdStoredProc
sybCmd.CommandText = sql
' setup for the parameter
sybParameter.Name = "@inp"          ' Only useful here, on the client.  No named parameters are sent in TDS
sybParameter.Type = adInteger       ' Set the Type to the ADO data type as defined in the
' ado specification. Supported datatypes for Sybase are listed in the ADO reference
' guide at the www.datadirect-technologies.com webpage, however these are listed as
' oledb datatypes.  You need to corelate these to ADO types.

sybParameter.Direction = adParamInput ' designates the direction of the parameter

sybCmd.Parameters.Append sybParameter   ' associates this parameter with the Command object
sybCmd.Parameters(0).Value = 1          ' Set the value through the Command object

Set sybParameter = Nothing      ' We no longer need the parameter object so we clean
' it out now.

' This sample sproc returns a result set, so we use the ADO Recordset to
' hold the results.  This is why we do the "Set sybRecordset = " on the Execute
'sybCommand.Execute
Set sybRst = sybCmd.Execute()
' Since we have a result set we process this information
TraverseRecordset


Finish

Exit Sub
ErrTrap:
ErrorProcess
End Sub


Private Sub procInOutTest_Click()
Dim sybParameter As ADODB.Parameter 'ADO Parameter object
On Error GoTo ErrTrap
Set sybConn = New ADODB.Connection
Set sybRst = New ADODB.Recordset
Set sybCmd = New ADODB.Command
Set sybParameter = sybCmd.CreateParameter
'Initialize the table ado_table & insert values
Init
' SQL Statement to send to ASE
sybCmd.ActiveConnection = sybConn
sql = "if exists (select 1 from sysobjects where name = 'sp_ado_out_c3_c4') drop procedure sp_ado_out_c3_c4"
sybCmd.CommandText = sql
sybCmd.Execute
sql = "create procedure sp_ado_out_c3_c4 (@out integer output) as  select @out=300 select c3,c4 from ado_table"
sybCmd.CommandText = sql
sybCmd.Execute
sql = "sp_ado_out_c3_c4"
sybCmd.CommandTimeout = 10
sybCmd.ActiveConnection = sybConn
sybCmd.CommandType = adCmdStoredProc
sybCmd.CommandText = sql


' setup for the parameter
sybParameter.Name = "@out"
sybParameter.Type = adInteger
sybParameter.Direction = adParamOutput
sybCmd.Parameters.Append sybParameter
sybCmd.Parameters(0).Value = 0
Set sybRst = sybCmd.Execute()
TraverseRecordset
'Must close the record set before accessing the output parameter
sybRst.Close

List1.AddItem "======================================="
List1.AddItem "Output parameter value : " & sybCmd.Parameters(0).Value
List1.AddItem "======================================="

Finish


Exit Sub
ErrTrap:
ErrorProcess
End Sub

'Initialize the tables required for the test
' create ado_table & insert values
Private Sub Init()
'Connection object information
sybConn.CursorLocation = adUseServer
sybConn.ConnectionTimeout = 10  'login timeout

If ODBCOption.Value = True Then
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'Sybase Connection string
connStr = "DRIVER=" + ODBCTextBox.Text + ";Database=" + CatalogTextBox.Text + ";Server=" + ServerNameTextBox.Text + ";Port=" + ServerPortTextBox.Text
Else
If OLEDBOption.Value = True Then
connStr = "Provider=" + OLEDBTextBox.Text + ";Data Source=" + ServerNameTextBox.Text + ":" + ServerPortTextBox.Text + "Initial Catalog=" + CatalogTextBox.Text
End If
End If
MsgBox "Connect String is " & connStr
sybConn.Open connStr, userNameTextBox.Text, passWordTextBox.Text


' SQL Statement to send to ASE
sybCmd.ActiveConnection = sybConn
sql = "if exists (select 1 from sysobjects where name = 'sp_ado_insert') drop procedure sp_ado_insert"
sybCmd.CommandText = sql
sybCmd.Execute
sql = "if exists (select 1 from sysobjects where name = 'ado_table') drop table ado_table"
sybCmd.CommandText = sql
sybCmd.Execute
sql = "create table ado_table(c1 int, c2 char(20),c3 numeric(10,2),c4 datetime)"
sybCmd.CommandText = sql
sybCmd.Execute
sql = "create proc sp_ado_insert (@id integer = 5) as declare @a integer declare @b numeric (10,2)   select @a = 1   select @b = 12345.67 while @a <= @id begin insert into ado_table values (@a, 'xyz', @b, getdate()) select @a = @a + 1   select @b = @b + 789.02  End"
sybCmd.CommandText = sql
sybCmd.Execute
sql = "sp_ado_insert"
sybCmd.CommandText = sql
sybCmd.Execute
Exit Sub
End Sub

'House cleaning
'Close open connections
Private Sub Finish()
If sybRst.State = adStateOpen Then
sybRst.Close
End If
If sybConn.State = adStateOpen Then
sybConn.Close
End If

Set sybParameter = Nothing
Set sybRst = Nothing
Set sybCmd = Nothing
Set sybConn = Nothing
Exit Sub
End Sub

Private Sub ErrorProcess()
If Err.Number = 5 Then
    lstr = lstr & Err.Description & ","
    Resume Next
End If
'We get description of error, the ADO number and the Source
MsgBox "There has been an error" & vbCrLf & "  " & Err.Description & "  " & Err.Number & "  " & Err.Source
' Another method to collect error information
' Enumerate Errors collection and display
' properties of each Error object.
For Each errLoop In sybConn.Errors
      strError = "Error #" & errLoop.Number & vbCr & _
         "   " & errLoop.Description & vbCr & _
         "   (Source: " & errLoop.Source & ")" & vbCr & _
         "   (SQL State: " & errLoop.SQLState & ")" & vbCr & _
         "   (NativeError: " & errLoop.NativeError & ")" & vbCr
      

   Debug.Print strError
Next
Exit Sub
End Sub

Private Sub TraverseRecordset()
fieldStr = ""
List1.AddItem "================================================================"

For Each sybFld2 In sybRst.Fields
    fieldStr = fieldStr & sybFld2.Name & ", "           'column name
    fieldStr = fieldStr & sybFld2.Type & ",    "        'ADO datatype
  
Next
fieldStr = Left(fieldStr, Len(fieldStr) - 1)
List1.AddItem fieldStr
List1.AddItem "================================================================"

' This loops over the sybRst object and will display the data values in each row
Do While Not sybRst.EOF
    lstr = "  "
    For Each sybFld In sybRst.Fields
        lstr = lstr & sybFld.Value & ",    "
    Next
    lstr = Left(lstr, Len(lstr) - 1)
    List1.AddItem lstr
    sybRst.MoveNext
Loop
List1.AddItem "================================================================"

Exit Sub
End Sub


