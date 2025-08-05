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
	Public WithEvents asePortNumText As System.Windows.Forms.TextBox
	Public WithEvents aseHostNameText As System.Windows.Forms.TextBox
	Public WithEvents kbUserPrinText As System.Windows.Forms.TextBox
	Public WithEvents kbServerPrinText As System.Windows.Forms.TextBox
	Public WithEvents kbAuthClientText As System.Windows.Forms.TextBox
	Public WithEvents sybOledbOption As System.Windows.Forms.RadioButton
	Public WithEvents sybOdbcOption As System.Windows.Forms.RadioButton
	Public WithEvents cmdTest As System.Windows.Forms.Button
	Public WithEvents List1 As System.Windows.Forms.ListBox
	Public WithEvents cmdExit As System.Windows.Forms.Button
	Public WithEvents Label2 As System.Windows.Forms.Label
	Public WithEvents Label1 As System.Windows.Forms.Label
	Public WithEvents Label14 As System.Windows.Forms.Label
	Public WithEvents Label13 As System.Windows.Forms.Label
	Public WithEvents Label12 As System.Windows.Forms.Label
	Public WithEvents Label11 As System.Windows.Forms.Label
	Public WithEvents Label6 As System.Windows.Forms.Label
	Public WithEvents Label4 As System.Windows.Forms.Label
	Public WithEvents Kerberos As System.Windows.Forms.Label
	Public WithEvents Label3 As System.Windows.Forms.Label
	'NOTE: The following procedure is required by the Windows Form Designer
	'It can be modified using the Windows Form Designer.
	'Do not modify it using the code editor.
	<System.Diagnostics.DebuggerStepThrough()> Private Sub InitializeComponent()
		Dim resources As System.Resources.ResourceManager = New System.Resources.ResourceManager(GetType(Form1))
		Me.components = New System.ComponentModel.Container()
		Me.ToolTip1 = New System.Windows.Forms.ToolTip(components)
		Me.ToolTip1.Active = True
		Me.asePortNumText = New System.Windows.Forms.TextBox
		Me.aseHostNameText = New System.Windows.Forms.TextBox
		Me.kbUserPrinText = New System.Windows.Forms.TextBox
		Me.kbServerPrinText = New System.Windows.Forms.TextBox
		Me.kbAuthClientText = New System.Windows.Forms.TextBox
		Me.sybOledbOption = New System.Windows.Forms.RadioButton
		Me.sybOdbcOption = New System.Windows.Forms.RadioButton
		Me.cmdTest = New System.Windows.Forms.Button
		Me.List1 = New System.Windows.Forms.ListBox
		Me.cmdExit = New System.Windows.Forms.Button
		Me.Label2 = New System.Windows.Forms.Label
		Me.Label1 = New System.Windows.Forms.Label
		Me.Label14 = New System.Windows.Forms.Label
		Me.Label13 = New System.Windows.Forms.Label
		Me.Label12 = New System.Windows.Forms.Label
		Me.Label11 = New System.Windows.Forms.Label
		Me.Label6 = New System.Windows.Forms.Label
		Me.Label4 = New System.Windows.Forms.Label
		Me.Kerberos = New System.Windows.Forms.Label
		Me.Label3 = New System.Windows.Forms.Label
		Me.StartPosition = System.Windows.Forms.FormStartPosition.Manual
		Me.BackColor = System.Drawing.Color.FromARGB(0, 128, 128)
		Me.Text = "Form1"
		Me.ClientSize = New System.Drawing.Size(938, 595)
		Me.Location = New System.Drawing.Point(174, 161)
		Me.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.AutoScaleBaseSize = New System.Drawing.Size(5, 13)
		Me.FormBorderStyle = System.Windows.Forms.FormBorderStyle.Sizable
		Me.ControlBox = True
		Me.Enabled = True
		Me.KeyPreview = False
		Me.MaximizeBox = True
		Me.MinimizeBox = True
		Me.Cursor = System.Windows.Forms.Cursors.Default
		Me.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.ShowInTaskbar = True
		Me.HelpButton = False
		Me.WindowState = System.Windows.Forms.FormWindowState.Normal
		Me.Name = "Form1"
		Me.asePortNumText.AutoSize = False
		Me.asePortNumText.Size = New System.Drawing.Size(97, 25)
		Me.asePortNumText.Location = New System.Drawing.Point(136, 96)
		Me.asePortNumText.TabIndex = 19
		Me.asePortNumText.Text = "asePort"
		Me.asePortNumText.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.asePortNumText.AcceptsReturn = True
		Me.asePortNumText.TextAlign = System.Windows.Forms.HorizontalAlignment.Left
		Me.asePortNumText.BackColor = System.Drawing.SystemColors.Window
		Me.asePortNumText.CausesValidation = True
		Me.asePortNumText.Enabled = True
		Me.asePortNumText.ForeColor = System.Drawing.SystemColors.WindowText
		Me.asePortNumText.HideSelection = True
		Me.asePortNumText.ReadOnly = False
		Me.asePortNumText.Maxlength = 0
		Me.asePortNumText.Cursor = System.Windows.Forms.Cursors.IBeam
		Me.asePortNumText.MultiLine = False
		Me.asePortNumText.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.asePortNumText.ScrollBars = System.Windows.Forms.ScrollBars.None
		Me.asePortNumText.TabStop = True
		Me.asePortNumText.Visible = True
		Me.asePortNumText.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D
		Me.asePortNumText.Name = "asePortNumText"
		Me.aseHostNameText.AutoSize = False
		Me.aseHostNameText.Size = New System.Drawing.Size(97, 25)
		Me.aseHostNameText.Location = New System.Drawing.Point(136, 56)
		Me.aseHostNameText.TabIndex = 18
		Me.aseHostNameText.Text = "aseHost"
		Me.aseHostNameText.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.aseHostNameText.AcceptsReturn = True
		Me.aseHostNameText.TextAlign = System.Windows.Forms.HorizontalAlignment.Left
		Me.aseHostNameText.BackColor = System.Drawing.SystemColors.Window
		Me.aseHostNameText.CausesValidation = True
		Me.aseHostNameText.Enabled = True
		Me.aseHostNameText.ForeColor = System.Drawing.SystemColors.WindowText
		Me.aseHostNameText.HideSelection = True
		Me.aseHostNameText.ReadOnly = False
		Me.aseHostNameText.Maxlength = 0
		Me.aseHostNameText.Cursor = System.Windows.Forms.Cursors.IBeam
		Me.aseHostNameText.MultiLine = False
		Me.aseHostNameText.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.aseHostNameText.ScrollBars = System.Windows.Forms.ScrollBars.None
		Me.aseHostNameText.TabStop = True
		Me.aseHostNameText.Visible = True
		Me.aseHostNameText.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D
		Me.aseHostNameText.Name = "aseHostNameText"
		Me.kbUserPrinText.AutoSize = False
		Me.kbUserPrinText.Size = New System.Drawing.Size(233, 33)
		Me.kbUserPrinText.Location = New System.Drawing.Point(200, 384)
		Me.kbUserPrinText.TabIndex = 15
		Me.kbUserPrinText.Text = "UserId"
		Me.kbUserPrinText.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.kbUserPrinText.AcceptsReturn = True
		Me.kbUserPrinText.TextAlign = System.Windows.Forms.HorizontalAlignment.Left
		Me.kbUserPrinText.BackColor = System.Drawing.SystemColors.Window
		Me.kbUserPrinText.CausesValidation = True
		Me.kbUserPrinText.Enabled = True
		Me.kbUserPrinText.ForeColor = System.Drawing.SystemColors.WindowText
		Me.kbUserPrinText.HideSelection = True
		Me.kbUserPrinText.ReadOnly = False
		Me.kbUserPrinText.Maxlength = 0
		Me.kbUserPrinText.Cursor = System.Windows.Forms.Cursors.IBeam
		Me.kbUserPrinText.MultiLine = False
		Me.kbUserPrinText.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.kbUserPrinText.ScrollBars = System.Windows.Forms.ScrollBars.None
		Me.kbUserPrinText.TabStop = True
		Me.kbUserPrinText.Visible = True
		Me.kbUserPrinText.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D
		Me.kbUserPrinText.Name = "kbUserPrinText"
		Me.kbServerPrinText.AutoSize = False
		Me.kbServerPrinText.Size = New System.Drawing.Size(233, 33)
		Me.kbServerPrinText.Location = New System.Drawing.Point(200, 344)
		Me.kbServerPrinText.TabIndex = 14
		Me.kbServerPrinText.Text = "aseServer@KerberosPrincipal"
		Me.kbServerPrinText.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.kbServerPrinText.AcceptsReturn = True
		Me.kbServerPrinText.TextAlign = System.Windows.Forms.HorizontalAlignment.Left
		Me.kbServerPrinText.BackColor = System.Drawing.SystemColors.Window
		Me.kbServerPrinText.CausesValidation = True
		Me.kbServerPrinText.Enabled = True
		Me.kbServerPrinText.ForeColor = System.Drawing.SystemColors.WindowText
		Me.kbServerPrinText.HideSelection = True
		Me.kbServerPrinText.ReadOnly = False
		Me.kbServerPrinText.Maxlength = 0
		Me.kbServerPrinText.Cursor = System.Windows.Forms.Cursors.IBeam
		Me.kbServerPrinText.MultiLine = False
		Me.kbServerPrinText.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.kbServerPrinText.ScrollBars = System.Windows.Forms.ScrollBars.None
		Me.kbServerPrinText.TabStop = True
		Me.kbServerPrinText.Visible = True
		Me.kbServerPrinText.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D
		Me.kbServerPrinText.Name = "kbServerPrinText"
		Me.kbAuthClientText.AutoSize = False
		Me.kbAuthClientText.Size = New System.Drawing.Size(153, 33)
		Me.kbAuthClientText.Location = New System.Drawing.Point(200, 280)
		Me.kbAuthClientText.TabIndex = 13
		Me.kbAuthClientText.Text = "mitkerberos"
		Me.kbAuthClientText.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.kbAuthClientText.AcceptsReturn = True
		Me.kbAuthClientText.TextAlign = System.Windows.Forms.HorizontalAlignment.Left
		Me.kbAuthClientText.BackColor = System.Drawing.SystemColors.Window
		Me.kbAuthClientText.CausesValidation = True
		Me.kbAuthClientText.Enabled = True
		Me.kbAuthClientText.ForeColor = System.Drawing.SystemColors.WindowText
		Me.kbAuthClientText.HideSelection = True
		Me.kbAuthClientText.ReadOnly = False
		Me.kbAuthClientText.Maxlength = 0
		Me.kbAuthClientText.Cursor = System.Windows.Forms.Cursors.IBeam
		Me.kbAuthClientText.MultiLine = False
		Me.kbAuthClientText.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.kbAuthClientText.ScrollBars = System.Windows.Forms.ScrollBars.None
		Me.kbAuthClientText.TabStop = True
		Me.kbAuthClientText.Visible = True
		Me.kbAuthClientText.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D
		Me.kbAuthClientText.Name = "kbAuthClientText"
		Me.sybOledbOption.TextAlign = System.Drawing.ContentAlignment.MiddleLeft
		Me.sybOledbOption.Text = "ASE OLE DB Provider"
		Me.sybOledbOption.Size = New System.Drawing.Size(177, 33)
		Me.sybOledbOption.Location = New System.Drawing.Point(24, 208)
		Me.sybOledbOption.TabIndex = 8
		Me.sybOledbOption.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.sybOledbOption.CheckAlign = System.Drawing.ContentAlignment.MiddleLeft
		Me.sybOledbOption.BackColor = System.Drawing.SystemColors.Control
		Me.sybOledbOption.CausesValidation = True
		Me.sybOledbOption.Enabled = True
		Me.sybOledbOption.ForeColor = System.Drawing.SystemColors.ControlText
		Me.sybOledbOption.Cursor = System.Windows.Forms.Cursors.Default
		Me.sybOledbOption.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.sybOledbOption.Appearance = System.Windows.Forms.Appearance.Normal
		Me.sybOledbOption.TabStop = True
		Me.sybOledbOption.Checked = False
		Me.sybOledbOption.Visible = True
		Me.sybOledbOption.Name = "sybOledbOption"
		Me.sybOdbcOption.TextAlign = System.Drawing.ContentAlignment.MiddleLeft
		Me.sybOdbcOption.Text = "ASE ODBC Driver "
		Me.sybOdbcOption.Size = New System.Drawing.Size(177, 33)
		Me.sybOdbcOption.Location = New System.Drawing.Point(24, 168)
		Me.sybOdbcOption.TabIndex = 7
		Me.sybOdbcOption.Checked = True
		Me.sybOdbcOption.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.sybOdbcOption.CheckAlign = System.Drawing.ContentAlignment.MiddleLeft
		Me.sybOdbcOption.BackColor = System.Drawing.SystemColors.Control
		Me.sybOdbcOption.CausesValidation = True
		Me.sybOdbcOption.Enabled = True
		Me.sybOdbcOption.ForeColor = System.Drawing.SystemColors.ControlText
		Me.sybOdbcOption.Cursor = System.Windows.Forms.Cursors.Default
		Me.sybOdbcOption.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.sybOdbcOption.Appearance = System.Windows.Forms.Appearance.Normal
		Me.sybOdbcOption.TabStop = True
		Me.sybOdbcOption.Visible = True
		Me.sybOdbcOption.Name = "sybOdbcOption"
		Me.cmdTest.TextAlign = System.Drawing.ContentAlignment.MiddleCenter
		Me.cmdTest.Text = "select count(*) from sysobjects"
		Me.cmdTest.Size = New System.Drawing.Size(153, 41)
		Me.cmdTest.Location = New System.Drawing.Point(176, 8)
		Me.cmdTest.TabIndex = 3
		Me.cmdTest.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.cmdTest.BackColor = System.Drawing.SystemColors.Control
		Me.cmdTest.CausesValidation = True
		Me.cmdTest.Enabled = True
		Me.cmdTest.ForeColor = System.Drawing.SystemColors.ControlText
		Me.cmdTest.Cursor = System.Windows.Forms.Cursors.Default
		Me.cmdTest.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.cmdTest.TabStop = True
		Me.cmdTest.Name = "cmdTest"
		Me.List1.Size = New System.Drawing.Size(417, 85)
		Me.List1.Location = New System.Drawing.Point(360, 32)
		Me.List1.TabIndex = 2
		Me.List1.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.List1.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D
		Me.List1.BackColor = System.Drawing.SystemColors.Window
		Me.List1.CausesValidation = True
		Me.List1.Enabled = True
		Me.List1.ForeColor = System.Drawing.SystemColors.WindowText
		Me.List1.IntegralHeight = True
		Me.List1.Cursor = System.Windows.Forms.Cursors.Default
		Me.List1.SelectionMode = System.Windows.Forms.SelectionMode.One
		Me.List1.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.List1.Sorted = False
		Me.List1.TabStop = True
		Me.List1.Visible = True
		Me.List1.MultiColumn = False
		Me.List1.Name = "List1"
		Me.cmdExit.TextAlign = System.Drawing.ContentAlignment.MiddleCenter
		Me.cmdExit.Text = "Exit"
		Me.cmdExit.Font = New System.Drawing.Font("Arial", 13.5!, System.Drawing.FontStyle.Bold Or System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.cmdExit.Size = New System.Drawing.Size(241, 65)
		Me.cmdExit.Location = New System.Drawing.Point(568, 448)
		Me.cmdExit.TabIndex = 0
		Me.cmdExit.BackColor = System.Drawing.SystemColors.Control
		Me.cmdExit.CausesValidation = True
		Me.cmdExit.Enabled = True
		Me.cmdExit.ForeColor = System.Drawing.SystemColors.ControlText
		Me.cmdExit.Cursor = System.Windows.Forms.Cursors.Default
		Me.cmdExit.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.cmdExit.TabStop = True
		Me.cmdExit.Name = "cmdExit"
		Me.Label2.Text = "ASE Port Number"
		Me.Label2.Size = New System.Drawing.Size(89, 25)
		Me.Label2.Location = New System.Drawing.Point(24, 96)
		Me.Label2.TabIndex = 17
		Me.Label2.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label2.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label2.BackColor = System.Drawing.SystemColors.Control
		Me.Label2.Enabled = True
		Me.Label2.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label2.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label2.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label2.UseMnemonic = True
		Me.Label2.Visible = True
		Me.Label2.AutoSize = False
		Me.Label2.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label2.Name = "Label2"
		Me.Label1.Text = "ASE Hostname"
		Me.Label1.Size = New System.Drawing.Size(89, 25)
		Me.Label1.Location = New System.Drawing.Point(24, 56)
		Me.Label1.TabIndex = 16
		Me.Label1.Font = New System.Drawing.Font("Arial", 8!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label1.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label1.BackColor = System.Drawing.SystemColors.Control
		Me.Label1.Enabled = True
		Me.Label1.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label1.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label1.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label1.UseMnemonic = True
		Me.Label1.Visible = True
		Me.Label1.AutoSize = False
		Me.Label1.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label1.Name = "Label1"
		Me.Label14.Text = "UserPrincipal = Ticket getter, they who get Kerberos credentials"
		Me.Label14.Font = New System.Drawing.Font("Arial", 8.25!, System.Drawing.FontStyle.Bold Or System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label14.Size = New System.Drawing.Size(161, 49)
		Me.Label14.Location = New System.Drawing.Point(24, 384)
		Me.Label14.TabIndex = 12
		Me.Label14.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label14.BackColor = System.Drawing.SystemColors.Control
		Me.Label14.Enabled = True
		Me.Label14.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label14.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label14.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label14.UseMnemonic = True
		Me.Label14.Visible = True
		Me.Label14.AutoSize = False
		Me.Label14.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label14.Name = "Label14"
		Me.Label13.Text = "ServerPrincipal = ASE server @ Kerberos Realm"
		Me.Label13.Font = New System.Drawing.Font("Arial", 8.25!, System.Drawing.FontStyle.Bold Or System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label13.Size = New System.Drawing.Size(153, 33)
		Me.Label13.Location = New System.Drawing.Point(24, 344)
		Me.Label13.TabIndex = 11
		Me.Label13.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label13.BackColor = System.Drawing.SystemColors.Control
		Me.Label13.Enabled = True
		Me.Label13.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label13.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label13.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label13.UseMnemonic = True
		Me.Label13.Visible = True
		Me.Label13.AutoSize = False
		Me.Label13.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label13.Name = "Label13"
		Me.Label12.Text = "AuthenticationClient = mitkerberos, cybersafekerberos or activedirectory"
		Me.Label12.Font = New System.Drawing.Font("Arial", 8.25!, System.Drawing.FontStyle.Bold Or System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label12.Size = New System.Drawing.Size(153, 57)
		Me.Label12.Location = New System.Drawing.Point(24, 280)
		Me.Label12.TabIndex = 10
		Me.Label12.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label12.BackColor = System.Drawing.SystemColors.Control
		Me.Label12.Enabled = True
		Me.Label12.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label12.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label12.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label12.UseMnemonic = True
		Me.Label12.Visible = True
		Me.Label12.AutoSize = False
		Me.Label12.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label12.Name = "Label12"
		Me.Label11.Text = "Kerberos Connection Properties"
		Me.Label11.Font = New System.Drawing.Font("Arial", 8.25!, System.Drawing.FontStyle.Bold Or System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label11.Size = New System.Drawing.Size(209, 25)
		Me.Label11.Location = New System.Drawing.Point(24, 248)
		Me.Label11.TabIndex = 9
		Me.Label11.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label11.BackColor = System.Drawing.SystemColors.Control
		Me.Label11.Enabled = True
		Me.Label11.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label11.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label11.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label11.UseMnemonic = True
		Me.Label11.Visible = True
		Me.Label11.AutoSize = False
		Me.Label11.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label11.Name = "Label11"
		Me.Label6.Text = "Sybase"
		Me.Label6.Font = New System.Drawing.Font("Arial", 12!, System.Drawing.FontStyle.Bold Or System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label6.Size = New System.Drawing.Size(81, 25)
		Me.Label6.Location = New System.Drawing.Point(24, 136)
		Me.Label6.TabIndex = 6
		Me.Label6.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label6.BackColor = System.Drawing.SystemColors.Control
		Me.Label6.Enabled = True
		Me.Label6.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label6.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label6.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label6.UseMnemonic = True
		Me.Label6.Visible = True
		Me.Label6.AutoSize = False
		Me.Label6.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label6.Name = "Label6"
		Me.Label4.BackColor = System.Drawing.Color.FromARGB(128, 255, 255)
		Me.Label4.Text = "Kerberos: Demonstrate connection properties used for connecting to the ASE with Kerberos.  Select either ODBC or OLEDB.  You can even build a connection string with your own Kerberos properties."
		Me.Label4.Font = New System.Drawing.Font("Arial", 12!, System.Drawing.FontStyle.Bold Or System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label4.Size = New System.Drawing.Size(433, 105)
		Me.Label4.Location = New System.Drawing.Point(24, 472)
		Me.Label4.TabIndex = 5
		Me.Label4.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label4.Enabled = True
		Me.Label4.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label4.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label4.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label4.UseMnemonic = True
		Me.Label4.Visible = True
		Me.Label4.AutoSize = False
		Me.Label4.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label4.Name = "Label4"
		Me.Kerberos.BackColor = System.Drawing.Color.FromARGB(128, 255, 255)
		Me.Kerberos.Text = "Kerberos Demo"
		Me.Kerberos.Font = New System.Drawing.Font("Arial", 13.5!, System.Drawing.FontStyle.Bold Or System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Kerberos.Size = New System.Drawing.Size(161, 33)
		Me.Kerberos.Location = New System.Drawing.Point(8, 8)
		Me.Kerberos.TabIndex = 4
		Me.Kerberos.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Kerberos.Enabled = True
		Me.Kerberos.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Kerberos.Cursor = System.Windows.Forms.Cursors.Default
		Me.Kerberos.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Kerberos.UseMnemonic = True
		Me.Kerberos.Visible = True
		Me.Kerberos.AutoSize = False
		Me.Kerberos.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Kerberos.Name = "Kerberos"
		Me.Label3.BackColor = System.Drawing.Color.FromARGB(128, 255, 255)
		Me.Label3.Text = "Output from select count(*)"
		Me.Label3.Font = New System.Drawing.Font("Arial", 9.75!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
		Me.Label3.Size = New System.Drawing.Size(465, 17)
		Me.Label3.Location = New System.Drawing.Point(360, 8)
		Me.Label3.TabIndex = 1
		Me.Label3.TextAlign = System.Drawing.ContentAlignment.TopLeft
		Me.Label3.Enabled = True
		Me.Label3.ForeColor = System.Drawing.SystemColors.ControlText
		Me.Label3.Cursor = System.Windows.Forms.Cursors.Default
		Me.Label3.RightToLeft = System.Windows.Forms.RightToLeft.No
		Me.Label3.UseMnemonic = True
		Me.Label3.Visible = True
		Me.Label3.AutoSize = False
		Me.Label3.BorderStyle = System.Windows.Forms.BorderStyle.None
		Me.Label3.Name = "Label3"
		Me.Controls.Add(asePortNumText)
		Me.Controls.Add(aseHostNameText)
		Me.Controls.Add(kbUserPrinText)
		Me.Controls.Add(kbServerPrinText)
		Me.Controls.Add(kbAuthClientText)
		Me.Controls.Add(sybOledbOption)
		Me.Controls.Add(sybOdbcOption)
		Me.Controls.Add(cmdTest)
		Me.Controls.Add(List1)
		Me.Controls.Add(cmdExit)
		Me.Controls.Add(Label2)
		Me.Controls.Add(Label1)
		Me.Controls.Add(Label14)
		Me.Controls.Add(Label13)
		Me.Controls.Add(Label12)
		Me.Controls.Add(Label11)
		Me.Controls.Add(Label6)
		Me.Controls.Add(Label4)
		Me.Controls.Add(Kerberos)
		Me.Controls.Add(Label3)
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
	''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
	'Kerberos for ADO
	'
	'Copyright (c) 2003-2005 Sybase,Inc
	'
	'
	'From accompanying readme file:
	'6-8-05
	'------
	'
	'The Kerberos sample demonstrates the connection string format for the various Windows related
	'data access products, the ODBC drivers and OLE DB Providers that access Sybase ASE.
	'
	'Following are the current levels that support Kerberos (Sybase OCS SDK 12.5.1 EBF 12531 ESD08):
	'
	'-------------------------
	'ASE ODBC Driver by Sybase (12.5.1.465, current build, sybdrvodb.dll)
	'ASE OLE DB Provider by Sybase (12.5.1.466, current build, sybdrvoledb.dll)
	''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
	
	Private Declare Function GetUserName Lib "advapi32.dll"  Alias "GetUserNameA"(ByVal lpBuffer As String, ByRef nSize As Integer) As Integer
	Private UserID As String ' User's Login ID
	
	Private Function CurrentUser() As String
		Dim strBuff As New VB6.FixedLengthString(255)
		Dim x As Integer
		CurrentUser = ""
		x = GetUserName(strBuff.Value, Len(strBuff.Value) - 1)
		If x > 0 Then
			x = InStr(strBuff.Value, vbNullChar)
			If x > 0 Then
				CurrentUser = VB.Left(strBuff.Value, x - 1)
			End If
		End If
	End Function
	
	Private Sub cmdExit_Click(ByVal eventSender As System.Object, ByVal eventArgs As System.EventArgs) Handles cmdExit.Click
		On Error Resume Next
		Me.Close()

		Form1.DefInstance = Nothing
	End Sub
	Private Sub cmdTest_Click(ByVal eventSender As System.Object, ByVal eventArgs As System.EventArgs) Handles cmdTest.Click
		
		Dim sql As String ' sql statement
		Dim connStr As String ' connection string
		Dim lstr As String ' String that contains record data
		Dim fieldStr As String ' field info string
		Dim firstRow As Boolean ' true if on first Row - to be used to make field string
		Dim tmpStr As String
		
		
		Dim sybConn As ADODB.Connection 'ADO Connection object
		Dim sybRst As ADODB.Recordset 'ADO Recordset object
		Dim sybFld As ADODB.Field 'ADO Field object
		Dim sybFld2 As ADODB.Field 'ADO Field Object to collect column info
		Dim errLoop As ADODB.Error 'ADO Error object
		Dim strError As String
		
		'ASE connection info
		Dim aseHost As String
		Dim asePort As String
		
		On Error GoTo ErrTrap
		
		sybConn = New ADODB.Connection
		sybRst = New ADODB.Recordset
		
		'Connection object information
		'sybConn.CursorLocation = adUseClient
		sybConn.ConnectionTimeout = 10 'login timeout
		'sybConn.CommandTimeout = 10    'query timeout
		
		'Get Connection info
		aseHost = aseHostNameText.Text
		asePort = asePortNumText.Text
		
		If sybOdbcOption.Checked = True Then
			' ASE ODBC Driver by Sybase : Adaptive Server Enterprise: 12.5.1.465 ESD08
			MsgBox("ASE ODBC Driver by Sybase")
			connStr = "Driver={Adaptive Server Enterprise};" & "Server=" & aseHost & ";Port=" & asePort & ";" & "AuthenticationClient=" & kbAuthClientText.Text & ";ServerPrincipal=" & kbServerPrinText.Text & ";UserPrincipal=" & kbUserPrinText.Text & ";"
			
		ElseIf sybOledbOption.Checked = True Then 
			' ASE OLE DB Provider by Sybase : ASEOLEDB : 12.5.1.466 ESD08
			' UserPrincipal is optional since in MIT Kerb, you get the ticket with the credentials.  Driver will
			' use those crendentials.
			MsgBox("ASE OLE DB Provider by Sybase")
			connStr = "Provider=ASEOLEDB;" & "Data Source=" & aseHost & ":" & asePort & ";" & "AuthenticationClient=" & kbAuthClientText.Text & ";ServerPrincipal=" & kbServerPrinText.Text & ";UserPrincipal=" & kbUserPrinText.Text & ";"
		End If
		
		''''''
		MsgBox("Connection String: " & connStr)
		System.Diagnostics.Debug.WriteLine(connStr)
		
		sybConn.Open(connStr)
		
		' SQL Statement to send to ASE
		sql = "select count(*) from sysobjects"
		
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
		'sybRst.Open sql, sybConn, adOpenKeyset, adLockOptimistic, adCmdText
		sybRst.Open(sql, sybConn, ADODB.CursorTypeEnum.adOpenStatic, ADODB.LockTypeEnum.adLockOptimistic, ADODB.CommandTypeEnum.adCmdText)
		'sybRst.Open sql, sybConn, adOpenDynamic, adLockOptimistic, adCmdText
		'sybRst.Open sql, sybConn, adOpenForwardOnly, adLockOptimistic, adCmdText
		
		' Get Column Names - this is very crude and will not line up with the
		' output below of the actual data, but it gives you an idea on how to gather this
		' type of information
		fieldStr = ""
		List1.Items.Add("==============================================")
		
		For	Each sybFld2 In sybRst.Fields
			fieldStr = fieldStr & sybFld2.Name & ", " 'column name
			fieldStr = fieldStr & sybFld2.Type & ",    " 'ADO datatype
			'fieldStr = fieldStr & sybFld2.Attributes & ","     'This returns the enumerated
			'value of the Attributes
		Next sybFld2
		fieldStr = VB.Left(fieldStr, Len(fieldStr) - 1)
		List1.Items.Add(fieldStr)
		List1.Items.Add("==============================================")
		
		' This loops over the sybRst object and will display the data values in each row
		Do While Not sybRst.EOF
			lstr = ""
			For	Each sybFld In sybRst.Fields
				lstr = lstr & sybFld.Value & ","
			Next sybFld
			lstr = VB.Left(lstr, Len(lstr) - 1)
			List1.Items.Add(lstr)
			sybRst.MoveNext()
		Loop 
		List1.Items.Add("==============================================")
		
		
		'Message Boxes are one way to get debug info.
		'In this case we get the RecordCount from this select
		MsgBox("RecordCount is " & sybRst.RecordCount)
		'Debug.Print will display the info in the Immediate Window down below
		'Debug.Print "RecordCount is " & sybRst.RecordCount
		
		'Housecleaning - close all ADO objects used
		'field objects are destroyed when Recordset object is destroyed
		sybRst.Close()
		sybConn.Close()
        sybRst = Nothing
        sybConn = Nothing

		Exit Sub
		
		'Basic error handling when error is trapped
ErrTrap: 
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
			'If errLoop.HelpFile = "" Then
			'   strError = strError & _
			''      "   No Help file available" & _
			''      vbCr & vbCr
			'Else
			'   strError = strError & _
			''      "   (HelpFile: " & errLoop.HelpFile & ")" & vbCr & _
			''      "   (HelpContext: " & errLoop.HelpContext & ")" & _
			''      vbCr & vbCr
			'End If
			
			
			System.Diagnostics.Debug.WriteLine(strError)
		Next errLoop
		
	End Sub
	
	Private Function GetDomain(ByRef dnPath As Object) As Object
		Dim arrVar As Object
		Dim i As Object
		
		
		arrVar = Split(VB.Right(dnPath, Len(dnPath) - InStr(dnPath, "DC=") + 1), "DC=")
		
		For i = 0 To UBound(arrVar)
            GetDomain = GetDomain & VB.Right(arrVar(i), Len(arrVar(i)))
		Next 
		
		GetDomain = Replace(GetDomain, ",", ".")
		
	End Function
	
	Private Sub Form1_Load(ByVal eventSender As System.Object, ByVal eventArgs As System.EventArgs) Handles MyBase.Load
		''''''''''
		' Obtain Current User's Login ID, and Kerberos5 User Principal Name
		''''''''''
		Dim sysInfo As Object ' ADSI System Object
		Dim objUser As Object ' ADSI User Object
		
		Dim KRB5_UID As String ' krb5 user principal name
		
		On Error Resume Next
		' get current user info from Active Directory Provider
		sysInfo = CreateObject("ADSystemInfo")
		' lookup user in Active Directory (only works on Windows NT, 2000, XP, 2003 and above)
        objUser = GetObject("LDAP://" & GetDomain(sysInfo.UserName) & "/" & Replace(sysInfo.UserName, "/", "\/"))
		
        UserID = objUser.sAMAccountName
        KRB5_UID = objUser.UserPrincipalName
		If Err.Number <> 0 Then
			UserID = CurrentUser
			KRB5_UID = ""
		End If
		
		System.Diagnostics.Debug.WriteLine("Login ID: " & UserID)
		System.Diagnostics.Debug.WriteLine("KRB5 Principal: " & KRB5_UID)
		
		' unload the ADSI user object and SysInfo objects

		objUser = Nothing

		sysInfo = Nothing
		On Error GoTo 0
		
		If KRB5_UID <> "" Then
			kbUserPrinText.Text = KRB5_UID
		End If
	End Sub
End Class