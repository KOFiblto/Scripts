@echo off
setlocal enabledelayedexpansion

set "ENV_FILE=D:\Scripts\.env"

if not exist "%ENV_FILE%" (
    echo Error: File "%ENV_FILE%" not found.
    pause
    goto :eof
)

FOR /F "usebackq tokens=1,2 delims==" %%A IN (`findstr /I "DUCKDNS" "%ENV_FILE%"`) DO (
    set "KEY=%%A"
    set "VAL=%%B"
    
    IF /I "!KEY!"=="DUCKDNS_TOKEN" (
        set "TOKEN=!VAL!"
    )
    IF /I "!KEY!"=="DUCKDNS_DOMAIN" (
        set "DUCKDNS_DOMAIN=!VAL!"
    )
)

:: Validation
if not defined TOKEN (
    echo Error: DUCKDNS_TOKEN not found in %ENV_FILE%
    pause
    goto :eof
)
if not defined DUCKDNS_DOMAIN (
    echo Error: DUCKDNS_DOMAIN not found in %ENV_FILE%
    pause
    goto :eof
)

echo DuckDNS Update for %DUCKDNS_DOMAIN%...

:: Execute Update
curl "https://www.duckdns.org/update?domains=%DUCKDNS_DOMAIN%&token=%TOKEN%&ip="

endlocal