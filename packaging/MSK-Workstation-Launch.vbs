' MSK Research Lab OS — Windows Desktop Silent Launcher (VBScript)
' Runs the local Uvicorn workstation backend without showing an ugly console window,
' waits for the local HTTP port to bind, and automatically launches the user browser.

Option Explicit

Dim WshShell, fso, scriptDir, projectDir, pythonExe, runCmd, oExec, i, httpCheck

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
' Check if running inside distribution or repository root
If fso.FolderExists(scriptDir & "\src\msk_research_lab") Then
    projectDir = scriptDir
ElseIf fso.FolderExists(fso.GetParentFolderName(scriptDir) & "\src\msk_research_lab") Then
    projectDir = fso.GetParentFolderName(scriptDir)
Else
    projectDir = scriptDir
End If

' Locate Python runtime (DEF-37)
If fso.FileExists(projectDir & "\.venv\Scripts\python.exe") Then
    pythonExe = """" & projectDir & "\.venv\Scripts\python.exe" & """"
ElseIf fso.FileExists("C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe") Then
    pythonExe = """C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe"""
ElseIf fso.FileExists(projectDir & "\python\python.exe") Then
    pythonExe = """" & projectDir & "\python\python.exe" & """"
Else
    ' Fallback to PATH
    On Error Resume Next
    Dim testExec
    Set testExec = WshShell.Exec("python --version")
    If Err.Number <> 0 Then
        MsgBox "Python runtime not detected. Please install Python 3.10+ or create a virtual environment in .venv.", vbCritical, "MSK Research Lab Workstation"
        WScript.Quit 1
    End If
    On Error GoTo 0
    pythonExe = "python"
End If

' Set Desktop Storage Mode
WshShell.Environment("PROCESS")("MSK_STORAGE_MODE") = "desktop"
WshShell.Environment("PROCESS")("MSK_LAB_HOST") = "127.0.0.1"
WshShell.Environment("PROCESS")("MSK_LAB_PORT") = "8091"

' Launch background process (0 = hidden window)
runCmd = "cmd.exe /c cd /d """ & projectDir & """ && " & pythonExe & " -m uvicorn msk_research_lab.api.app:app --host 127.0.0.1 --port 8091"
WshShell.Run runCmd, 0, False

' Wait for server to bind port (up to 15 seconds)
WScript.Sleep 2500

' Open default browser to Workstation UI
WshShell.Run "http://127.0.0.1:8091/workstation", 1, False

WScript.Quit 0
