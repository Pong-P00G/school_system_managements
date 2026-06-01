@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  School System - Local Database Setup
echo ============================================
echo.

REM --- Collect DB credentials ---
set /p DB_USER="PostgreSQL username (default: postgres): "
if "!DB_USER!"=="" set DB_USER=postgres

set /p DB_PASSWORD="PostgreSQL password: "

set /p DB_HOST="Host (default: localhost): "
if "!DB_HOST!"=="" set DB_HOST=localhost

set /p DB_PORT="Port (default: 5432): "
if "!DB_PORT!"=="" set DB_PORT=5432

set /p DB_NAME="Database name (default: school_system_db_v2): "
if "!DB_NAME!"=="" set DB_NAME=school_system_db_v2

echo.
echo [1/4] Creating database "%DB_NAME%"...
set PGPASSWORD=!DB_PASSWORD!
psql -U !DB_USER! -h !DB_HOST! -p !DB_PORT! -c "CREATE DATABASE %DB_NAME%;" 2>nul
if errorlevel 1 (
    echo      Database may already exist, continuing...
)

echo [2/4] Writing backend\.env ...
set BACKEND_DIR=%~dp0..\backend
(
    echo DATABASE_URL=postgresql+asyncpg://!DB_USER!:!DB_PASSWORD!@!DB_HOST!:!DB_PORT!/!DB_NAME!
    echo DATABASE_URL_SYNC=postgresql://!DB_USER!:!DB_PASSWORD!@!DB_HOST!:!DB_PORT!/!DB_NAME!
    echo APP_NAME=School Management System API
    echo APP_VERSION=1.0.0
    echo DEBUG=true
    echo SECRET_KEY=change-this-to-a-secure-random-string
    echo ALGORITHM=HS256
    echo ACCESS_TOKEN_EXPIRE_MINUTES=60
    echo CORS_ORIGINS=http://localhost:5173,http://localhost:3000
    echo PROMETHEUS_ENABLED=true
) > "%BACKEND_DIR%\.env"

echo [3/4] Updating alembic.ini sqlalchemy.url ...
powershell -Command "(Get-Content '%BACKEND_DIR%\alembic.ini') -replace '^sqlalchemy\.url\s*=.*', 'sqlalchemy.url = postgresql://!DB_USER!:!DB_PASSWORD!@!DB_HOST!:!DB_PORT!/!DB_NAME!' | Set-Content '%BACKEND_DIR%\alembic.ini'"

echo [4/4] Running Alembic migrations...
cd /d "%BACKEND_DIR%"
call python -m alembic upgrade head
if errorlevel 1 (
    echo.
    echo ERROR: Migration failed. Check your PostgreSQL connection and try again.
    exit /b 1
)

echo.
echo ============================================
echo  Done! Database "%DB_NAME%" is ready.
echo  Run: cd backend ^&^& uvicorn app.main:app --reload
echo ============================================
endlocal
