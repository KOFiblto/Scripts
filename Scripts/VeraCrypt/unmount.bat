

:: ---------------------------------------------
::   This Script unmounts all VeraCrypt Drives
:: ---------------------------------------------


@echo off

:: Set VeraCrypt Filepath if not installed to default location
set "VC_PATH=C:\Program Files\VeraCrypt\VeraCrypt.exe"

:: /f = Force (optional, add before /q if you want to force close open files) >>>  %VC_PATH%" /d /f /q  <<<
:: Due to VeryCrypt being a GUI Programm, its not easily possible to detect if files are still open and 
:: then ask the user if it should be force-closed. I just rerun it after closing all the Files.
"%VC_PATH%" /d /q

echo Volume dismounted.
timeout /t 2 >nul