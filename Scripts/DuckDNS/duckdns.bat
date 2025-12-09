@echo off
set TOKEN=4c5f7767-b39a-4f37-8b4a-56a057fcc1cc
set DOMAIN=bemajoko
curl "https://www.duckdns.org/update?domains=%DOMAIN%&token=%TOKEN%&ip="
