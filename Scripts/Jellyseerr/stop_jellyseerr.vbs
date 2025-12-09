Option Explicit

' ===== CONFIG =====
Dim scriptFolder : scriptFolder = "D:\Scripts\Mathias\Jellyseerr"
Dim pidFile      : pidFile = scriptFolder & "\pnpm_start.pid"
Dim maxNodeToKill: maxNodeToKill = 3
Dim spawnWaitMs  : spawnWaitMs = 2500   ' wait (ms) before snapshot
Dim verbose      : verbose = False
' ===================

Dim fso: Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FileExists(pidFile) Then
  If verbose Then WScript.Echo "PID file not found: " & pidFile & vbCrLf & "Run start.vbs first."
  WScript.Quit 1
End If

Dim pidText, rootPID
Dim inFile: Set inFile = fso.OpenTextFile(pidFile, 1)
pidText = Trim(inFile.ReadAll)
inFile.Close

If pidText = "" Then
  If verbose Then WScript.Echo "PID file is empty."
  WScript.Quit 1
End If

On Error Resume Next
rootPID = CLng(pidText)
If Err.Number <> 0 Then
  If verbose Then WScript.Echo "Invalid PID in pid file: " & pidText
  WScript.Quit 1
End If
On Error GoTo 0

Dim wmi: Set wmi = GetObject("winmgmts:\\.\root\cimv2")

' <<< Verify that the root process is still alive and is pnpm >>>
Dim procCheck, p
Set procCheck = wmi.ExecQuery("Select * from Win32_Process Where ProcessId=" & rootPID)
Dim foundAlive: foundAlive = False
For Each p In procCheck
    If InStr(LCase(p.CommandLine), "pnpm start") > 0 Then
        foundAlive = True
        Exit For
    End If
Next

If Not foundAlive Then
    If verbose Then WScript.Echo "No active pnpm process found for PID " & rootPID & ". Exiting."
    On Error Resume Next
    fso.DeleteFile pidFile
    On Error GoTo 0
    WScript.Quit 1
End If
' <<< End check >>>

WScript.Sleep spawnWaitMs

' Helper: get creation date of root
Dim rootCreation: rootCreation = GetCreationDateForPID(rootPID)

' Build process map
Dim procMap: Set procMap = CreateObject("Scripting.Dictionary")
Dim colProcs, p2
Set colProcs = wmi.ExecQuery("Select ProcessId, ParentProcessId, Name, CreationDate from Win32_Process")
For Each p2 In colProcs
  Dim key: key = CStr(p2.ProcessId)
  procMap.Add key, Array(CLng(p2.ParentProcessId), LCase(p2.Name), CStr(p2.CreationDate))
Next

' Find descendants of rootPID
Dim descendants: Set descendants = CreateObject("Scripting.Dictionary")
descendants.Add CStr(rootPID), True

Dim added: added = True
Do While added
  added = False
  Dim pidKey
  For Each pidKey In procMap.Keys
    If Not descendants.Exists(pidKey) Then
      Dim vals: vals = procMap(pidKey)
      Dim parentId: parentId = CStr(vals(0))
      If descendants.Exists(parentId) Then
        descendants.Add pidKey, True
        added = True
      End If
    End If
  Next
Loop

' Collect node.exe children
Dim nodeList() : ReDim nodeList(-1)
Dim k
For Each k In descendants.Keys
  If CInt(k) <> rootPID Then
    Dim entry: entry = procMap(k)
    Dim pname: pname = entry(1)
    Dim pcreation: pcreation = entry(2)
    If pname = "node.exe" Then
      If rootCreation = "" Or pcreation >= rootCreation Then
        ReDim Preserve nodeList(UBound(nodeList) + 1)
        nodeList(UBound(nodeList)) = CInt(k)
      End If
    End If
  End If
Next

If UBound(nodeList) = -1 Then
  If verbose Then WScript.Echo "No node.exe descendants found for PID " & rootPID & "."
Else
  If verbose Then WScript.Echo "Found " & (UBound(nodeList)+1) & " node.exe descendant(s). Terminating up to " & maxNodeToKill & "."
  Dim killCount: killCount = 0
  Dim i, pidToKill, procObj, ret
  For i = 0 To UBound(nodeList)
    If killCount >= maxNodeToKill Then Exit For
    pidToKill = nodeList(i)
    On Error Resume Next
    Set procObj = wmi.Get("Win32_Process.Handle='" & pidToKill & "'")
    If Err.Number <> 0 Then
      If verbose Then WScript.Echo "Could not access process object for PID " & pidToKill & " (err " & Err.Number & ")"
      Err.Clear
    Else
      ret = procObj.Terminate()
      If ret = 0 Or ret = 2 Then
        If verbose Then WScript.Echo "Terminated node.exe (PID " & pidToKill & ")"
        killCount = killCount + 1
      Else
        If verbose Then WScript.Echo "Failed to terminate PID " & pidToKill & " (Return code " & ret & ")"
      End If
    End If
    On Error GoTo 0
  Next
  If verbose Then WScript.Echo "Done. Terminated " & killCount & " process(es)."
End If

' Remove pid file
On Error Resume Next
fso.DeleteFile pidFile
On Error GoTo 0

' Helper function
Function GetCreationDateForPID(pid)
  GetCreationDateForPID = ""
  If pid <= 0 Then Exit Function
  Dim q, res
  q = "Select CreationDate from Win32_Process where ProcessId = " & pid
  Set res = wmi.ExecQuery(q)
  Dim r
  For Each r In res
    GetCreationDateForPID = CStr(r.CreationDate)
    Exit For
  Next
End Function
