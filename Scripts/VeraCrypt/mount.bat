

:: --------------------------------------------------------------
::   This Script allows the user to mount specific Safes faster
:: --------------------------------------------------------------


@echo off
setlocal EnableDelayedExpansion

:: Set VeraCrypt Filepath if not installed to default location
set "VC_PATH=C:\Program Files\VeraCrypt\VeraCrypt.exe"

:: ------------------ Configuration ---------------
:: Set "Count" to match the number of safes
set "Count=3"

:: Format: 
:: "SafePath[Index]=Path\to\Safe"
:: "SafePIM[Index]=PID"

set "SafePath[1]=D:\other.hc"
set "SafePIM[1]=0"

set "SafePath[2]=C:\private.hc"
set "SafePIM[2]=20"

set "SafePath[3]=C:\passwords.hc"
set "SafePIM[3]=0"
:: ------------------------------------------------



:MENU
cls
echo Select Safe to Mount:
echo.
:: Loops from 1 to Count to generate the menu at Runtime
for /L %%i in (1,1,%Count%) do (
    echo %%i. !SafePath[%%i]!
)
echo.
set /p CHOICE="Enter Number (1-%Count%): "

:: Basic Validation
if "%CHOICE%" lss "1" goto MENU
if "%CHOICE%" gtr "%Count%" goto MENU

:: Extract selected data
set "VOLUME=!SafePath[%CHOICE%]!"
set "PIM=!SafePIM[%CHOICE%]!"

:: Mount Logic
for %%L in (Z Y X W V U T S R Q P O N M L K J I H G F E) do (
    if not exist %%L:\ (
        echo Mounting "!VOLUME!" to Drive %%L...
        "%VC_PATH%" /v "!VOLUME!" /l %%L /pim !PIM! /q
        exit /b
    )
)

echo Error: No free drive letters found.
pause