@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Polaris - Configurador Unico Windows
where powershell.exe >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Windows PowerShell 5.1 nao localizado.
  pause
  exit /b 2
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Polaris_Setup.ps1"
set "RESULTADO=%ERRORLEVEL%"
echo.
if not "%RESULTADO%"=="0" echo O configurador terminou com codigo %RESULTADO%. Consulte o relatorio e logs.
pause
exit /b %RESULTADO%