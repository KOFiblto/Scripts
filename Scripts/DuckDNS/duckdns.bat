@echo off
set TOKEN=***REMOVED***
set DOMAIN=***REMOVED***
curl "https://www.duckdns.org/update?domains=%DOMAIN%&token=%TOKEN%&ip="
