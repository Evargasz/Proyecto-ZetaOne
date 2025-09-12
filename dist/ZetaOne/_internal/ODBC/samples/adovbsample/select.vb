Option Strict Off
Option Explicit On
Imports VB = Microsoft.VisualBasic
Friend Class Form1
	Inherits System.Windows.Forms.Form
#Region "Windows Form Designer generated code "
	Public Sub New()
		MyBase.New()
		If m_vb6FormDefInstance Is Nothing Then
			If m_InitializingDefInstance Then
				m_vb6FormDefInstance = Me
			Else
				Try 
					'For the start-up form, the first instance created is the default instance.
					If System.Reflection.Assembly.GetExecutingAssembly.EntryPoint.DeclaringType Is Me.GetType Then
						m_vb6FormDefInstance = Me
					End If
				Catch
				End Try
			End If
		End If
		'This call is required by the Windows Form Designer.
		InitializeComponent()
	End Sub
	'Form overrides dispose to clean up the component list.
	Protected Overloads Overrides Sub Dispose(ByVal Disposing As Boolean)
		If Disposing Then
			If Not components Is Nothing Then
				components.Dispose()
			End If
		End If
		MyBase.Dispose(Disposing)
	End Sub
	'Required by the Windows Form Designer
	Private components As System.ComponentModel.IContainer
	Public ToolTip1 As System.Windows.Forms.ToolTip
	Public WithEvents procInOutTest As System.Windows.Forms.Button
	Public WithEvents procInpTest As System.Windows.Forms.Button
    Public WithEvents ODBCTextBox As System.Windows.Forms.TextBox
    Public WithEvents ServerPortTextBox As System.Windows.Forms.TextBox
	Public WithEvents CatalogTextBox As System.Windows.Forms.TextBox
	Public WithEvents ServerNameTextBox As System.Windows.Forms.TextBox
	Public WithEvents cmdTest As System.Windows.Forms.Button
	Public WithEvents passWordTextBox As System.Windows.Forms.TextBox
	Public WithEvents List1 As System.Windows.Forms.ListBox
	Public WithEvents cmdExit As System.Windows.Forms.Button
	Public WithEvents userNameTextBox As System.Windows.Forms.TextBox
	Public WithEvents Label12 As System.Windows.Forms.Label
	Public WithEvents Label11 As System.Windows.Forms.Label
	Public WithEvents Label10 As System.Windows.Forms.Label
	Public WithEvents Label9 As System.Windows.Forms.Label
    Public WithEvents Label7 As System.Windows.Forms.Label
	Public WithEvents Label6 As System.Windows.Forms.Label
	Public WithEvents Label5 As System.Windows.Forms.Label
	Public WithEvents Label4 As System.Windows.Forms.Label
	Public WithEvents SybSamps As System.Windows.Forms.Label
	Public WithEvents Label2 As System.Windows.Forms.Label
	Public WithEvents Label3 As System.Windows.Forms.Label
	Public WithEvents Label1 As System.Windows.Forms.Label
	'NOTE: The following procedure is required by the Windows Form Designer
	'It can be modified using the Windows Form Designer.
	'Do not modify it using the code editor.
    Public WithEvents Label8 As System.Windows.Forms.Label
    Public WithEvents OLEDBTextBox As System.Windows.Forms.TextBox
    Public WithEvents OLEDBOption As System.Windows.Forms.RadioButton
    Public WithEvents ODBCOption As System.Windows.Forms.RadioButton
    <System.Diagnostics.DebuggerStepThrough()> Private Sub InitializeComponent()
        Me.components = New System.ComponentModel.Container
        Me.ToolTip1 = New System.Windows.Forms.ToolTip(Me.components)
        Me.procInOutTest = New System.Windows.Forms.Button
        Me.procInpTest = New System.Windows.Forms.Button
        Me.ODBCTextBox = New System.Windows.Forms.TextBox
        Me.ServerPortTextBox = New System.Windows.Forms.TextBox
        Me.CatalogTextBox = New System.Windows.Forms.TextBox
        Me.ServerNameTextBox = New System.Windows.Forms.TextBox
        Me.cmdTest = New System.Windows.Forms.Button
        Me.passWordTextBox = New System.Windows.Forms.TextBox
        Me.List1 = New System.Windows.Forms.ListBox
        Me.cmdExit = New System.Windows.Forms.Button
        Me.userNameTextBox = New System.Windows.Forms.TextBox
        Me.Label12 = New System.Windows.Forms.Label
        Me.Label11 = New System.Windows.Forms.Label
        Me.Label10 = New System.Windows.Forms.Label
        Me.Label9 = New System.Windows.Forms.Label
        Me.Label7 = New System.Windows.Forms.Label
        Me.Label6 = New System.Windows.Forms.Label
        Me.Label5 = New System.Windows.Forms.Label
        Me.Label4 = New System.Windows.Forms.Label
        Me.SybSamps = New System.Windows.Forms.Label
        Me.Label2 = New System.Windows.Forms.Label
        Me.Label3 = New System.Windows.Forms.Label
        Me.Label1 = New System.Windows.Forms.Label
        Me.OLEDBTextBox = New System.Windows.Forms.TextBox
        Me.Label8 = New System.Windows.Forms.Label
        Me.OLEDBOption = New System.Windows.Forms.RadioButton
        Me.ODBCOption = New System.Windows.Forms.RadioButton
        Me.SuspendLayout()
        '
        'procInOutTest
        '
        Me.procInOutTest.BackColor = System.Drawing.SystemColors.Control
        Me.procInOutTest.Cursor = System.Windows.Forms.Cursors.Default
        Me.procInOutTest.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.procInOutTest.ForeColor = System.Drawing.SystemColors.ControlText
        Me.procInOutTest.Location = New System.Drawing.Point(16, 192)
        Me.procInOutTest.Name = "procInOutTest"
        Me.procInOutTest.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.procInOutTest.Size = New System.Drawing.Size(137, 25)
        Me.procInOutTest.TabIndex = 25
        Me.procInOutTest.Text = "Stored Procedure Output"
        '
        'procInpTest
        '
        Me.procInpTest.BackColor = System.Drawing.SystemColors.Control
        Me.procInpTest.Cursor = System.Windows.Forms.Cursors.Default
        Me.procInpTest.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.procInpTest.ForeColor = System.Drawing.SystemColors.ControlText
        Me.procInpTest.Location = New System.Drawing.Point(16, 224)
        Me.procInpTest.Name = "procInpTest"
        Me.procInpTest.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.procInpTest.Size = New System.Drawing.Size(137, 25)
        Me.procInpTest.TabIndex = 22
        Me.procInpTest.Text = "Stored Procedure Input"
        '
        'ODBCTextBox
        '
        Me.ODBCTextBox.AcceptsReturn = True
        Me.ODBCTextBox.AutoSize = False
        Me.ODBCTextBox.BackColor = System.Drawing.SystemColors.Window
        Me.ODBCTextBox.Cursor = System.Windows.Forms.Cursors.IBeam
        Me.ODBCTextBox.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.ODBCTextBox.ForeColor = System.Drawing.SystemColors.WindowText
        Me.ODBCTextBox.Location = New System.Drawing.Point(360, 8)
        Me.ODBCTextBox.MaxLength = 0
        Me.ODBCTextBox.Name = "ODBCTextBox"
        Me.ODBCTextBox.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.ODBCTextBox.Size = New System.Drawing.Size(217, 19)
        Me.ODBCTextBox.TabIndex = 18
        Me.ODBCTextBox.Text = "Adaptive Server Enterprise"
        '
        'ServerPortTextBox
        '
        Me.ServerPortTextBox.AcceptsReturn = True
        Me.ServerPortTextBox.AutoSize = False
        Me.ServerPortTextBox.BackColor = System.Drawing.SystemColors.Window
        Me.ServerPortTextBox.Cursor = System.Windows.Forms.Cursors.IBeam
        Me.ServerPortTextBox.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.ServerPortTextBox.ForeColor = System.Drawing.SystemColors.WindowText
        Me.ServerPortTextBox.Location = New System.Drawing.Point(96, 160)
        Me.ServerPortTextBox.MaxLength = 0
        Me.ServerPortTextBox.Name = "ServerPortTextBox"
        Me.ServerPortTextBox.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.ServerPortTextBox.Size = New System.Drawing.Size(73, 19)
        Me.ServerPortTextBox.TabIndex = 15
        Me.ServerPortTextBox.Text = "5000"
        '
        'CatalogTextBox
        '
        Me.CatalogTextBox.AcceptsReturn = True
        Me.CatalogTextBox.AutoSize = False
        Me.CatalogTextBox.BackColor = System.Drawing.SystemColors.Window
        Me.CatalogTextBox.Cursor = System.Windows.Forms.Cursors.IBeam
        Me.CatalogTextBox.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.CatalogTextBox.ForeColor = System.Drawing.SystemColors.WindowText
        Me.CatalogTextBox.Location = New System.Drawing.Point(96, 112)
        Me.CatalogTextBox.MaxLength = 0
        Me.CatalogTextBox.Name = "CatalogTextBox"
        Me.CatalogTextBox.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.CatalogTextBox.Size = New System.Drawing.Size(73, 19)
        Me.CatalogTextBox.TabIndex = 11
        Me.CatalogTextBox.Text = "pubs2"
        '
        'ServerNameTextBox
        '
        Me.ServerNameTextBox.AcceptsReturn = True
        Me.ServerNameTextBox.AutoSize = False
        Me.ServerNameTextBox.BackColor = System.Drawing.SystemColors.Window
        Me.ServerNameTextBox.Cursor = System.Windows.Forms.Cursors.IBeam
        Me.ServerNameTextBox.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.ServerNameTextBox.ForeColor = System.Drawing.SystemColors.WindowText
        Me.ServerNameTextBox.ImeMode = System.Windows.Forms.ImeMode.Disable
        Me.ServerNameTextBox.Location = New System.Drawing.Point(96, 136)
        Me.ServerNameTextBox.MaxLength = 0
        Me.ServerNameTextBox.Name = "ServerNameTextBox"
        Me.ServerNameTextBox.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.ServerNameTextBox.Size = New System.Drawing.Size(73, 19)
        Me.ServerNameTextBox.TabIndex = 10
        Me.ServerNameTextBox.Text = "sample"
        '
        'cmdTest
        '
        Me.cmdTest.BackColor = System.Drawing.SystemColors.Control
        Me.cmdTest.Cursor = System.Windows.Forms.Cursors.Default
        Me.cmdTest.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.cmdTest.ForeColor = System.Drawing.SystemColors.ControlText
        Me.cmdTest.Location = New System.Drawing.Point(16, 256)
        Me.cmdTest.Name = "cmdTest"
        Me.cmdTest.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.cmdTest.Size = New System.Drawing.Size(137, 25)
        Me.cmdTest.TabIndex = 7
        Me.cmdTest.Text = "Select "
        '
        'passWordTextBox
        '
        Me.passWordTextBox.AcceptsReturn = True
        Me.passWordTextBox.AutoSize = False
        Me.passWordTextBox.BackColor = System.Drawing.SystemColors.Window
        Me.passWordTextBox.Cursor = System.Windows.Forms.Cursors.IBeam
        Me.passWordTextBox.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.passWordTextBox.ForeColor = System.Drawing.SystemColors.WindowText
        Me.passWordTextBox.Location = New System.Drawing.Point(96, 88)
        Me.passWordTextBox.MaxLength = 0
        Me.passWordTextBox.Name = "passWordTextBox"
        Me.passWordTextBox.PasswordChar = Microsoft.VisualBasic.ChrW(42)
        Me.passWordTextBox.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.passWordTextBox.Size = New System.Drawing.Size(73, 19)
        Me.passWordTextBox.TabIndex = 1
        Me.passWordTextBox.Text = ""
        '
        'List1
        '
        Me.List1.BackColor = System.Drawing.SystemColors.Window
        Me.List1.Cursor = System.Windows.Forms.Cursors.Default
        Me.List1.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.List1.ForeColor = System.Drawing.SystemColors.WindowText
        Me.List1.ItemHeight = 14
        Me.List1.Location = New System.Drawing.Point(208, 112)
        Me.List1.Name = "List1"
        Me.List1.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.List1.Size = New System.Drawing.Size(433, 214)
        Me.List1.TabIndex = 5
        '
        'cmdExit
        '
        Me.cmdExit.BackColor = System.Drawing.SystemColors.Control
        Me.cmdExit.Cursor = System.Windows.Forms.Cursors.Default
        Me.cmdExit.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.cmdExit.ForeColor = System.Drawing.SystemColors.ControlText
        Me.cmdExit.Location = New System.Drawing.Point(16, 288)
        Me.cmdExit.Name = "cmdExit"
        Me.cmdExit.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.cmdExit.Size = New System.Drawing.Size(137, 25)
        Me.cmdExit.TabIndex = 3
        Me.cmdExit.Text = "Exit"
        '
        'userNameTextBox
        '
        Me.userNameTextBox.AcceptsReturn = True
        Me.userNameTextBox.AutoSize = False
        Me.userNameTextBox.BackColor = System.Drawing.SystemColors.Window
        Me.userNameTextBox.Cursor = System.Windows.Forms.Cursors.IBeam
        Me.userNameTextBox.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.userNameTextBox.ForeColor = System.Drawing.SystemColors.WindowText
        Me.userNameTextBox.Location = New System.Drawing.Point(96, 64)
        Me.userNameTextBox.MaxLength = 0
        Me.userNameTextBox.Name = "userNameTextBox"
        Me.userNameTextBox.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.userNameTextBox.Size = New System.Drawing.Size(73, 19)
        Me.userNameTextBox.TabIndex = 0
        Me.userNameTextBox.Text = "sa"
        '
        'Label12
        '
        Me.Label12.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label12.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label12.Font = New System.Drawing.Font("Arial", 9.75!, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label12.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label12.Location = New System.Drawing.Point(16, 472)
        Me.Label12.Name = "Label12"
        Me.Label12.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label12.Size = New System.Drawing.Size(625, 65)
        Me.Label12.TabIndex = 26
        Me.Label12.Text = "Stored Procedure Output : Demonstrates how to bind an output parameter for a stor" & _
        "ed procedure call. It uses ""sp_ado_out_c3_c4"", and binds an  output parameter to" & _
        " a stored procedure and gathers information from the Recordset object, such as c" & _
        "olumn names and data."
        '
        'Label11
        '
        Me.Label11.BackColor = System.Drawing.Color.FromArgb(CType(224, Byte), CType(224, Byte), CType(224, Byte))
        Me.Label11.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label11.Font = New System.Drawing.Font("Arial", 9.75!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label11.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label11.Location = New System.Drawing.Point(32, 552)
        Me.Label11.Name = "Label11"
        Me.Label11.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label11.Size = New System.Drawing.Size(465, 17)
        Me.Label11.TabIndex = 24
        Me.Label11.Text = "Copyright (c) 2003-2004 Sybase,Inc"
        '
        'Label10
        '
        Me.Label10.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label10.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label10.Font = New System.Drawing.Font("Arial", 9.75!, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label10.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label10.Location = New System.Drawing.Point(16, 400)
        Me.Label10.Name = "Label10"
        Me.Label10.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label10.Size = New System.Drawing.Size(625, 65)
        Me.Label10.TabIndex = 23
        Me.Label10.Text = "Stored Procedure Input : Demonstrates how to bind an input parameter for a stored" & _
        " procedure call. It uses ""sp_ado_c3_c4"", and binds an input parameter to a store" & _
        "d procedure and gathers information from the Recordset object, such as column na" & _
        "mes and data."
        '
        'Label9
        '
        Me.Label9.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label9.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label9.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label9.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label9.Location = New System.Drawing.Point(216, 8)
        Me.Label9.Name = "Label9"
        Me.Label9.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label9.Size = New System.Drawing.Size(121, 17)
        Me.Label9.TabIndex = 19
        Me.Label9.Text = "ODBC Driver"
        Me.Label9.TextAlign = System.Drawing.ContentAlignment.TopRight
        '
        'Label7
        '
        Me.Label7.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label7.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label7.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label7.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label7.Location = New System.Drawing.Point(16, 160)
        Me.Label7.Name = "Label7"
        Me.Label7.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label7.Size = New System.Drawing.Size(73, 17)
        Me.Label7.TabIndex = 14
        Me.Label7.Text = "PORT:"
        Me.Label7.TextAlign = System.Drawing.ContentAlignment.TopRight
        '
        'Label6
        '
        Me.Label6.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label6.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label6.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label6.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label6.Location = New System.Drawing.Point(16, 112)
        Me.Label6.Name = "Label6"
        Me.Label6.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label6.Size = New System.Drawing.Size(73, 16)
        Me.Label6.TabIndex = 13
        Me.Label6.Text = " CATALOG:"
        '
        'Label5
        '
        Me.Label5.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label5.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label5.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label5.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label5.Location = New System.Drawing.Point(16, 136)
        Me.Label5.Name = "Label5"
        Me.Label5.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label5.Size = New System.Drawing.Size(73, 17)
        Me.Label5.TabIndex = 12
        Me.Label5.Text = "SERVER:"
        Me.Label5.TextAlign = System.Drawing.ContentAlignment.TopRight
        '
        'Label4
        '
        Me.Label4.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label4.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label4.Font = New System.Drawing.Font("Arial", 9.75!, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label4.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label4.Location = New System.Drawing.Point(16, 336)
        Me.Label4.Name = "Label4"
        Me.Label4.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label4.Size = New System.Drawing.Size(625, 57)
        Me.Label4.TabIndex = 9
        Me.Label4.Text = "Select : Demonstrates how to execute a SELECT statement. It uses ""select * from a" & _
        "do_table"", and then gathers information from the Recordset object, such as colum" & _
        "n names and data."
        '
        'SybSamps
        '
        Me.SybSamps.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.SybSamps.Cursor = System.Windows.Forms.Cursors.Default
        Me.SybSamps.Font = New System.Drawing.Font("Arial", 12.0!, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.SybSamps.ForeColor = System.Drawing.SystemColors.ControlText
        Me.SybSamps.Location = New System.Drawing.Point(16, 8)
        Me.SybSamps.Name = "SybSamps"
        Me.SybSamps.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.SybSamps.Size = New System.Drawing.Size(153, 49)
        Me.SybSamps.TabIndex = 8
        Me.SybSamps.Text = "ADODB Sample for Sybase"
        '
        'Label2
        '
        Me.Label2.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label2.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label2.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label2.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label2.Location = New System.Drawing.Point(16, 88)
        Me.Label2.Name = "Label2"
        Me.Label2.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label2.Size = New System.Drawing.Size(73, 17)
        Me.Label2.TabIndex = 6
        Me.Label2.Text = "PASSWORD:"
        Me.Label2.TextAlign = System.Drawing.ContentAlignment.TopRight
        '
        'Label3
        '
        Me.Label3.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label3.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label3.Font = New System.Drawing.Font("Arial", 9.75!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label3.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label3.Location = New System.Drawing.Point(216, 88)
        Me.Label3.Name = "Label3"
        Me.Label3.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label3.Size = New System.Drawing.Size(433, 17)
        Me.Label3.TabIndex = 4
        Me.Label3.Text = "Output: Heading contains Columns names and ADO datatype"
        '
        'Label1
        '
        Me.Label1.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label1.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label1.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label1.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label1.Location = New System.Drawing.Point(16, 64)
        Me.Label1.Name = "Label1"
        Me.Label1.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label1.Size = New System.Drawing.Size(73, 17)
        Me.Label1.TabIndex = 2
        Me.Label1.Text = "USER ID:"
        Me.Label1.TextAlign = System.Drawing.ContentAlignment.TopRight
        '
        'OLEDBTextBox
        '
        Me.OLEDBTextBox.AcceptsReturn = True
        Me.OLEDBTextBox.AutoSize = False
        Me.OLEDBTextBox.BackColor = System.Drawing.SystemColors.Window
        Me.OLEDBTextBox.Cursor = System.Windows.Forms.Cursors.IBeam
        Me.OLEDBTextBox.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.OLEDBTextBox.ForeColor = System.Drawing.SystemColors.WindowText
        Me.OLEDBTextBox.Location = New System.Drawing.Point(360, 40)
        Me.OLEDBTextBox.MaxLength = 0
        Me.OLEDBTextBox.Name = "OLEDBTextBox"
        Me.OLEDBTextBox.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.OLEDBTextBox.Size = New System.Drawing.Size(217, 19)
        Me.OLEDBTextBox.TabIndex = 27
        Me.OLEDBTextBox.Text = "ASEOLEDB"
        '
        'Label8
        '
        Me.Label8.BackColor = System.Drawing.Color.FromArgb(CType(128, Byte), CType(255, Byte), CType(255, Byte))
        Me.Label8.Cursor = System.Windows.Forms.Cursors.Default
        Me.Label8.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Label8.ForeColor = System.Drawing.SystemColors.ControlText
        Me.Label8.Location = New System.Drawing.Point(216, 40)
        Me.Label8.Name = "Label8"
        Me.Label8.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.Label8.Size = New System.Drawing.Size(121, 17)
        Me.Label8.TabIndex = 28
        Me.Label8.Text = "OLEDB Provider"
        Me.Label8.TextAlign = System.Drawing.ContentAlignment.TopRight
        '
        'OLEDBOption
        '
        Me.OLEDBOption.BackColor = System.Drawing.SystemColors.Control
        Me.OLEDBOption.Checked = True
        Me.OLEDBOption.Cursor = System.Windows.Forms.Cursors.Default
        Me.OLEDBOption.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.OLEDBOption.ForeColor = System.Drawing.SystemColors.ControlText
        Me.OLEDBOption.Location = New System.Drawing.Point(360, 72)
        Me.OLEDBOption.Name = "OLEDBOption"
        Me.OLEDBOption.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.OLEDBOption.Size = New System.Drawing.Size(105, 13)
        Me.OLEDBOption.TabIndex = 30
        Me.OLEDBOption.TabStop = True
        Me.OLEDBOption.Text = "OLEDB"
        '
        'ODBCOption
        '
        Me.ODBCOption.BackColor = System.Drawing.SystemColors.Control
        Me.ODBCOption.Cursor = System.Windows.Forms.Cursors.Default
        Me.ODBCOption.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.ODBCOption.ForeColor = System.Drawing.SystemColors.ControlText
        Me.ODBCOption.Location = New System.Drawing.Point(216, 72)
        Me.ODBCOption.Name = "ODBCOption"
        Me.ODBCOption.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.ODBCOption.Size = New System.Drawing.Size(105, 13)
        Me.ODBCOption.TabIndex = 29
        Me.ODBCOption.TabStop = True
        Me.ODBCOption.Text = "ODBC"
        '
        'Form1
        '
        Me.AutoScaleBaseSize = New System.Drawing.Size(5, 13)
        Me.BackColor = System.Drawing.Color.FromArgb(CType(0, Byte), CType(128, Byte), CType(128, Byte))
        Me.ClientSize = New System.Drawing.Size(698, 584)
        Me.Controls.Add(Me.OLEDBOption)
        Me.Controls.Add(Me.ODBCOption)
        Me.Controls.Add(Me.OLEDBTextBox)
        Me.Controls.Add(Me.Label8)
        Me.Controls.Add(Me.procInOutTest)
        Me.Controls.Add(Me.procInpTest)
        Me.Controls.Add(Me.ODBCTextBox)
        Me.Controls.Add(Me.ServerPortTextBox)
        Me.Controls.Add(Me.CatalogTextBox)
        Me.Controls.Add(Me.ServerNameTextBox)
        Me.Controls.Add(Me.cmdTest)
        Me.Controls.Add(Me.passWordTextBox)
        Me.Controls.Add(Me.List1)
        Me.Controls.Add(Me.cmdExit)
        Me.Controls.Add(Me.userNameTextBox)
        Me.Controls.Add(Me.Label12)
        Me.Controls.Add(Me.Label11)
        Me.Controls.Add(Me.Label10)
        Me.Controls.Add(Me.Label9)
        Me.Controls.Add(Me.Label7)
        Me.Controls.Add(Me.Label6)
        Me.Controls.Add(Me.Label5)
        Me.Controls.Add(Me.Label4)
        Me.Controls.Add(Me.SybSamps)
        Me.Controls.Add(Me.Label2)
        Me.Controls.Add(Me.Label3)
        Me.Controls.Add(Me.Label1)
        Me.Cursor = System.Windows.Forms.Cursors.Default
        Me.Font = New System.Drawing.Font("Arial", 8.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.Location = New System.Drawing.Point(222, 144)
        Me.Name = "Form1"
        Me.RightToLeft = System.Windows.Forms.RightToLeft.No
        Me.StartPosition = System.Windows.Forms.FormStartPosition.Manual
        Me.Text = "Form1"
        Me.ResumeLayout(False)

    End Sub
#End Region 
#Region "Upgrade Support "
	Private Shared m_vb6FormDefInstance As Form1
	Private Shared m_InitializingDefInstance As Boolean
	Public Shared Property DefInstance() As Form1
		Get
			If m_vb6FormDefInstance Is Nothing OrElse m_vb6FormDefInstance.IsDisposed Then
				m_InitializingDefInstance = True
				m_vb6FormDefInstance = New Form1()
				m_InitializingDefInstance = False
			End If
			DefInstance = m_vb6FormDefInstance
		End Get
		Set
			m_vb6FormDefInstance = Value
		End Set
	End Property
#End Region 
	'SybSamps for ADO
	
    ' Copyright (c) 2003-2005  Sybase, Inc.
	
	
	'
	Dim sql As String ' sql statement
	Dim connStr As String ' connection string
	Dim sybConn As ADODB.Connection 'ADO Connection object
	Dim sybCmd As ADODB.Command 'ADO Command object
	Dim lstr As String ' String that contains record data
	Dim errLoop As ADODB.Error 'ADO Error object
	Dim strError As String
	Dim fieldStr As String ' field info string
	Dim sybRst As ADODB.Recordset 'ADO Recordset object
	Dim sybFld As ADODB.Field 'ADO Field object
	Dim sybFld2 As ADODB.Field 'ADO Field Object to collect column info
	Dim sybParameter As ADODB.Parameter 'ADO Parameter object
	
	
	
	Private Sub cmdExit_Click(ByVal eventSender As System.Object, ByVal eventArgs As System.EventArgs) Handles cmdExit.Click
		On Error Resume Next
		Me.Close()

		Form1.DefInstance = Nothing
	End Sub
	Private Sub cmdTest_Click(ByVal eventSender As System.Object, ByVal eventArgs As System.EventArgs) Handles cmdTest.Click
		
		Dim firstRow As Boolean ' true if on first Row - to be used to make field string
		Dim tmpStr As String
		
		
		On Error GoTo ErrTrap
		
		sybConn = New ADODB.Connection
		sybRst = New ADODB.Recordset
		sybCmd = New ADODB.Command
        Init2()
		sql = "select c2,c1,c3,c4 from ado_table"
		
		' This informs the Recordset object, sybRst to use Connection object sybConn.
		' When the Recordset object is opened below, then the application uses sybConn
		' to access the ASE database.
		sybRst.let_ActiveConnection(sybConn)
		
		'If you want to limit records returned from ASE you can do it here with the
		' MaxRecords Recordset property.
		'sybRst.MaxRecords = 5
		
		'This is where we open the Recordset object. Note that there are a variety of settings.
		'Open recordset object: sql string (sql), connection object (sybConn), cursor type,
		' lock type, option : in this case we send adCmdText
		sybRst.Open(sql, sybConn, ADODB.CursorTypeEnum.adOpenForwardOnly, ADODB.LockTypeEnum.adLockReadOnly, ADODB.CommandTypeEnum.adCmdText)
		' Get Column Names - this is very crude and will not line up with the
		' output below of the actual data, but it gives you an idea on how to gather this
		' type of information
		TraverseRecordset()
		'Message Boxes are one way to get debug info.
		'In this case we get the RecordCount from this select
		MsgBox("RecordCount is " & sybRst.RecordCount)
		'Debug.Print will display the info in the Immediate Window down below
		'Debug.Print "RecordCount is " & sybRst.RecordCount
		
		'Housecleaning - close all ADO objects used
		'field objects are destroyed when Recordset object is destroyed
		Finish()
		
		Exit Sub
		
		'Basic error handling when error is trapped
ErrTrap: 
        ErrorProcess()
        'Finish()
	End Sub
	
	
	
	
	Private Sub procInpTest_Click(ByVal eventSender As System.Object, ByVal eventArgs As System.EventArgs) Handles procInpTest.Click
		
		On Error GoTo ErrTrap
		sybConn = New ADODB.Connection
		sybRst = New ADODB.Recordset
		sybCmd = New ADODB.Command
		sybParameter = sybCmd.CreateParameter
		
		Init()
		' SQL Statement to send to ASE
		sybCmd.let_ActiveConnection(sybConn)
		sql = "if exists (select 1 from sysobjects where name = 'sp_ado_c3_c4') drop procedure sp_ado_c3_c4"
		sybCmd.CommandText = sql
		sybCmd.Execute()
		sql = "create procedure sp_ado_c3_c4 (@inp integer) as select c3, c4 from ado_table where c1=@inp"
		sybCmd.CommandText = sql
		sybCmd.Execute()
		' This informs the Recordset object, sybRst to use Connection object sybConn.
		' When the Recordset object is opened below, then the application uses sybConn
		' to access the ASE database.
		sql = "sp_ado_c3_c4"
		sybCmd.CommandType = ADODB.CommandTypeEnum.adCmdStoredProc
		sybCmd.CommandText = sql
		' setup for the parameter
		sybParameter.Name = "@inp" ' Only useful here, on the client.  No named parameters are sent in TDS
		sybParameter.Type = ADODB.DataTypeEnum.adInteger ' Set the Type to the ADO data type as defined in the
		' ado specification. 
		
		sybParameter.Direction = ADODB.ParameterDirectionEnum.adParamInput ' designates the direction of the parameter
		
		sybCmd.Parameters.Append(sybParameter) ' associates this parameter with the Command object
		sybCmd.Parameters(0).Value = 1 ' Set the value through the Command object
		

		sybParameter = Nothing ' We no longer need the parameter object so we clean
		' it out now.
		
		' This sample sproc returns a result set, so we use the ADO Recordset to
		' hold the results.  This is why we do the "Set sybRecordset = " on the Execute
		'sybCommand.Execute
		sybRst = sybCmd.Execute()
		' Since we have a result set we process this information
		TraverseRecordset()
		
		
		Finish()
		
		Exit Sub
ErrTrap: 
		ErrorProcess()
	End Sub
	
	
	Private Sub procInOutTest_Click(ByVal eventSender As System.Object, ByVal eventArgs As System.EventArgs) Handles procInOutTest.Click
		Dim sybParameter As ADODB.Parameter 'ADO Parameter object
		On Error GoTo ErrTrap
		sybConn = New ADODB.Connection
		sybRst = New ADODB.Recordset
		sybCmd = New ADODB.Command
		sybParameter = sybCmd.CreateParameter
		'Initialize the table ado_table & insert values
		Init()
		' SQL Statement to send to ASE
		sybCmd.let_ActiveConnection(sybConn)
		sql = "if exists (select 1 from sysobjects where name = 'sp_ado_out_c3_c4') drop procedure sp_ado_out_c3_c4"
		sybCmd.CommandText = sql
		sybCmd.Execute()
		sql = "create procedure sp_ado_out_c3_c4 (@out integer output) as  select @out=300 select c3,c4 from ado_table"
		sybCmd.CommandText = sql
		sybCmd.Execute()
		sql = "sp_ado_out_c3_c4"
		sybCmd.CommandTimeout = 10
		sybCmd.let_ActiveConnection(sybConn)
		sybCmd.CommandType = ADODB.CommandTypeEnum.adCmdStoredProc
		sybCmd.CommandText = sql
		
		
		' setup for the parameter
		sybParameter.Name = "@out"
		sybParameter.Type = ADODB.DataTypeEnum.adInteger
		sybParameter.Direction = ADODB.ParameterDirectionEnum.adParamOutput
		sybCmd.Parameters.Append(sybParameter)
		sybCmd.Parameters(0).Value = 0
		sybRst = sybCmd.Execute()
		TraverseRecordset()
		'Must close the record set before accessing the output parameter
		sybRst.Close()
		
		List1.Items.Add("=======================================")
		List1.Items.Add("Output parameter value : " & sybCmd.Parameters(0).Value)
		List1.Items.Add("=======================================")
		
		Finish()
		
		
		Exit Sub
ErrTrap: 
        ErrorProcess()
        Finish()
	End Sub
	
	'Initialize the tables required for the test
	' create ado_table & insert values
	Private Sub Init()
		'Connection object information
		sybConn.CursorLocation = ADODB.CursorLocationEnum.adUseServer
		sybConn.ConnectionTimeout = 10 'login timeout
        'Sybase Connection string
        If ODBCOption.Checked = True Then
            '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
            'Sybase Connection string
            connStr = "DRIVER=" & ODBCTextBox.Text & ";Database=" & CatalogTextBox.Text & ";Server=" & ServerNameTextBox.Text & ";Port=" & ServerPortTextBox.Text
        Else
            If OLEDBOption.Checked = True Then
                connStr = "Provider=" & OLEDBTextBox.Text & ";Data Source=" & ServerNameTextBox.Text & ":" & ServerPortTextBox.Text & ";Initial Catalog=" & CatalogTextBox.Text
            End If
        End If
        'MsgBox("Connect String is " & connStr)
        sybConn.Open(connStr, userNameTextBox.Text, passWordTextBox.Text)
       
        ' SQL Statement to send to ASE
        sybCmd.let_ActiveConnection(sybConn)
        sql = "if exists (select 1 from sysobjects where name = 'sp_ado_insert') drop procedure sp_ado_insert"


        sybCmd.CommandText = sql
        sybCmd.Execute()
        sql = "if exists (select 1 from sysobjects where name = 'ado_table') drop table ado_table"
        sybCmd.CommandText = sql
        sybCmd.Execute()
        sql = "create table ado_table(c1 int, c2 char(20),c3 numeric(10,2),c4 datetime)"
        sybCmd.CommandText = sql
        sybCmd.Execute()
        sql = "create proc sp_ado_insert (@id integer = 5) as declare @a integer declare @b numeric (10,2)   select @a = 1   select @b = 12345.67 while @a <= @id begin insert into ado_table values (@a, 'xyz', @b, getdate()) select @a = @a + 1   select @b = @b + 789.02  End"
        sybCmd.CommandText = sql
        sybCmd.Execute()
        sql = "sp_ado_insert"
        sybCmd.CommandText = sql
        sybCmd.Execute()
        Exit Sub
	End Sub
	
	'House cleaning
	'Close open connections
	Private Sub Finish()
		If sybRst.State = ADODB.ObjectStateEnum.adStateOpen Then
			sybRst.Close()
        End If
        
        If sybConn.State = ADODB.ObjectStateEnum.adStateOpen Then
            sybConn.Close()
        End If
        sybParameter = Nothing
        sybRst = Nothing
        sybCmd = Nothing
        sybConn = Nothing
        Exit Sub
	End Sub
	
	Private Sub ErrorProcess()
		If Err.Number = 5 Then
			lstr = lstr & Err.Description & ","
			Resume Next
		End If
		'We get description of error, the ADO number and the Source
		MsgBox("There has been an error" & vbCrLf & "  " & Err.Description & "  " & Err.Number & "  " & Err.Source)
		' Another method to collect error information
		' Enumerate Errors collection and display
		' properties of each Error object.
		For	Each errLoop In sybConn.Errors
			strError = "Error #" & errLoop.Number & vbCr & "   " & errLoop.Description & vbCr & "   (Source: " & errLoop.Source & ")" & vbCr & "   (SQL State: " & errLoop.SQLState & ")" & vbCr & "   (NativeError: " & errLoop.NativeError & ")" & vbCr
			
			
			System.Diagnostics.Debug.WriteLine(strError)
		Next errLoop
		Exit Sub
	End Sub
    Private Sub Init2()
        'Connection object information

        sybConn.ConnectionTimeout = 10 'login timeout
        'Sybase Connection string
        If ODBCOption.Checked = True Then
            sybConn.CursorLocation = ADODB.CursorLocationEnum.adUseServer
            '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
            'Sybase Connection string
            connStr = "DRIVER=" & ODBCTextBox.Text & ";Database=" & CatalogTextBox.Text & ";Server=" & ServerNameTextBox.Text & ";Port=" & ServerPortTextBox.Text
        Else
            If OLEDBOption.Checked = True Then
                connStr = "PROVIDER=" & OLEDBTextBox.Text & ";Data Source=" & ServerNameTextBox.Text & ":" & ServerPortTextBox.Text & ";Initial Catalog=" & CatalogTextBox.Text
            End If
        End If
        'MsgBox("Connect String is " & connStr)
        sybConn.Open(connStr, userNameTextBox.Text, passWordTextBox.Text)
        sybCmd.let_ActiveConnection(sybConn)
        sql = "if exists (select 1 from sysobjects where name = 'sp_ado_insert') drop procedure sp_ado_insert"
        'sql = "drop procedure sp_ado_insert"
        'sybConn.Execute(sql)
        sybCmd.CommandType = ADODB.CommandTypeEnum.adCmdText
        sybCmd.CommandText = sql
        sybCmd.Execute()
        sql = "if exists (select 1 from sysobjects where name = 'ado_table') drop table ado_table"
        sybCmd.CommandText = sql
        sybCmd.Execute()
        sql = "create table ado_table(c1 int, c2 char(20),c3 numeric(10,2),c4 datetime)"
        sybCmd.CommandText = sql
        sybCmd.Execute()
        sql = " create proc sp_ado_insert (@id integer = 5) as declare @a integer declare @b numeric (10,2)   select @a = 1   select @b = 12345.67 while @a <= @id begin insert into ado_table values (@a, 'xyz', @b, getdate()) select @a = @a + 1   select @b = @b + 789.02  End"
        sybCmd.CommandText = sql
        sybCmd.Execute()
        sql = "sp_ado_insert"
        sybCmd.CommandText = sql
        sybCmd.Execute()
        Exit Sub
    End Sub

    Private Sub TraverseRecordset()
        fieldStr = ""
        List1.Items.Add("================================================================")

        For Each sybFld2 In sybRst.Fields
            fieldStr = fieldStr & sybFld2.Name & ", " 'column name
            fieldStr = fieldStr & sybFld2.Type & ",    " 'ADO datatype

        Next sybFld2
        If fieldStr.Length() > 1 Then
            fieldStr = VB.Left(fieldStr, Len(fieldStr) - 1)
            List1.Items.Add(fieldStr)
        End If
     
        List1.Items.Add("================================================================")

        ' This loops over the sybRst object and will display the data values in each row
        Do While Not sybRst.EOF
            lstr = "  "
            For Each sybFld In sybRst.Fields
                lstr = lstr & sybFld.Value & ",    "
            Next sybFld
            lstr = VB.Left(lstr, Len(lstr) - 1)
            List1.Items.Add(lstr)
            sybRst.MoveNext()
        Loop
        List1.Items.Add("================================================================")

        Exit Sub
    End Sub

    Private Sub Label8_Click(ByVal sender As System.Object, ByVal e As System.EventArgs)

    End Sub

    Private Sub OLEDBTextBox_TextChanged(ByVal sender As System.Object, ByVal e As System.EventArgs)

    End Sub

    Private Sub Form1_Load(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles MyBase.Load

    End Sub

    Private Sub TextBox1_TextChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles OLEDBTextBox.TextChanged

    End Sub

    Private Sub Label8_Click_1(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles Label8.Click

    End Sub

    Private Sub SybSamps_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles SybSamps.Click

    End Sub
End Class