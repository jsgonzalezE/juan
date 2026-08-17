@echo off
title Burman Inventario - servidor local
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo  No encontre Node.js. Instalalo desde https://nodejs.org ^(version LTS^)
  echo  y vuelve a dar doble clic a este archivo.
  echo.
  pause
  exit /b 1
)
node serve.js
pause
