@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  Dung Docker Website Ban Giay
echo ====================================================

set COMPOSE_CMD=
where docker-compose >nul 2>&1
if %ERRORLEVEL% equ 0 goto USE_DOCKER_COMPOSE

where docker >nul 2>&1
if %ERRORLEVEL% equ 0 goto USE_DOCKER_COMPOSE_V2

goto NO_DOCKER

:USE_DOCKER_COMPOSE
set COMPOSE_CMD=docker-compose
goto STOP_APP

:USE_DOCKER_COMPOSE_V2
set COMPOSE_CMD=docker compose
goto STOP_APP

:STOP_APP
echo Dang dung container...
%COMPOSE_CMD% down

echo.
echo Da dung container thanh cong. Du lieu folder van duoc giu nguyen.
pause
exit /b 0

:NO_DOCKER
echo.
echo [LOI] Khong tim thay lenh docker tren he thong.
pause
exit /b 1