@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  Khoi dong Docker Website Ban Giay
echo ====================================================

set COMPOSE_CMD=
where docker-compose >nul 2>&1
if %ERRORLEVEL% equ 0 goto USE_DOCKER_COMPOSE

where docker >nul 2>&1
if %ERRORLEVEL% equ 0 goto USE_DOCKER_COMPOSE_V2

goto NO_DOCKER

:USE_DOCKER_COMPOSE
set COMPOSE_CMD=docker-compose
goto START_APP

:USE_DOCKER_COMPOSE_V2
set COMPOSE_CMD=docker compose
goto START_APP

:START_APP
echo Su dung: %COMPOSE_CMD%
echo Dang kiem tra va don dep container cu...
%COMPOSE_CMD% down >nul 2>&1

echo Dang build va khoi chay website...
%COMPOSE_CMD% up -d --build --remove-orphans

if %ERRORLEVEL% neq 0 goto ERROR_RUN

echo.
echo ====================================================
echo  Website ban giay da khoi dong thanh cong!
echo  Dang mo trinh duyet: http://localhost:5000 ...
echo ====================================================

ping 127.0.0.1 -n 3 >nul
start http://localhost:5000

echo.
echo Website dang chay tren: http://localhost:5000
echo De tat website, hay chay file: docker-stop.bat
echo ====================================================
pause
exit /b 0

:ERROR_RUN
echo.
echo [LOI] Khong the khoi dong Docker container!
echo Vui long kiem tra Docker Desktop da duoc bat (trang thai Running) chua.
pause
exit /b 1

:NO_DOCKER
echo.
echo [LOI] Khong tim thay Docker hoac Docker Compose tren he thong.
echo Vui long cai dat hoac bat Docker Desktop truoc.
pause
exit /b 1