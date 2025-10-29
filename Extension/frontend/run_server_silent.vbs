Option Explicit

Dim WshShell, scriptDir, batFile, cmd

Set WshShell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Point to the BAT file
batFile = scriptDir & "\start_server.bat"

If Not CreateObject("Scripting.FileSystemObject").FileExists(batFile) Then
    MsgBox "Error: start_server.bat not found in " & scriptDir, vbCritical, "Tube Snatcher"
    WScript.Quit 1
End If

' Run BAT file hidden
cmd = "cmd /c """ & batFile & """"
WshShell.Run cmd, 0, False

Set WshShell = Nothing
