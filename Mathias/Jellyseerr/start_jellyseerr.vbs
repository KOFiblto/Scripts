Option Explicit

' === CONFIG ===
Dim projectFolder : projectFolder = "D:\NZB\jellyseerr"
Dim scriptFolder  : scriptFolder  = "D:\Scripts\Jellyseerr"
Dim pidFile       : pidFile       = scriptFolder & "\pnpm_start.pid"
Dim verbose       : verbose       = False
' ===============

Dim fso: Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FolderExists(scriptFolder) Then fso.CreateFolder(scriptFolder)

Dim wmi, startup, retCode, newPID
Set wmi = GetObject("winmgmts:\\.\root\cimv2")

' <<< Check if already running >>>
If fso.FileExists(pidFile) Then
    Dim oldPID, inFile, pidText
    Set inFile = fso.OpenTextFile(pidFile, 1)
    pidText = Trim(inFile.ReadAll)
    inFile.Close

    If pidText <> "" Then
        On Error Resume Next
        oldPID = CLng(pidText)
        On Error GoTo 0

        If oldPID > 0 Then
            Dim procCheck, p
            Set procCheck = wmi.ExecQuery("Select * from Win32_Process Where ProcessId=" & oldPID)
            For Each p In procCheck
                ' Verify it's really our pnpm process (child of cmd.exe in our folder)
                If InStr(LCase(p.CommandLine), "pnpm start") > 0 Then
                    If verbose Then WScript.Echo "pnpm is already running with PID " & oldPID & ". Exiting."
                    WScript.Quit 0
                End If
            Next
        End If
    End If
    ' PID not valid → cleanup stale file
    On Error Resume Next
    fso.DeleteFile pidFile
    On Error GoTo 0
End If
' <<< End check >>>

' Build a Win32_ProcessStartup object and hide the window
Set startup = wmi.Get("Win32_ProcessStartup").SpawnInstance_
startup.ShowWindow = 0

' Create process hidden and get the PID
newPID = 0
retCode = wmi.Get("Win32_Process").Create("cmd.exe /c pnpm start", projectFolder, startup, newPID)

If retCode = 0 Then
    Dim outFile: Set outFile = fso.CreateTextFile(pidFile, True)
    outFile.WriteLine CStr(newPID)
    outFile.Close
    If verbose Then WScript.Echo "pnpm started (hidden). PID: " & newPID
Else
    If verbose Then WScript.Echo "Failed to start pnpm. WMI Create returned: " & CStr(retCode)
End If