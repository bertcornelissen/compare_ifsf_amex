
@echo off
REM ==========================================
REM One-click Streamlit Launcher (Latest)
REM Local venv, shared app, self-healing
REM ==========================================

SET APP_DIR=C:\Users\bcorn\PythonProjects\compare_ifsf_amex
SET APP_FILE=compare_amex_gui.py

REM Local venv per user
SET VENV_DIR=%LOCALAPPDATA%\compare_iso8583_amex_venv

REM Environment hardening
SET PYTHONDONTWRITEBYTECODE=1
SET PYTHONUTF8=1

REM ---- Ensure config files exist ----
IF NOT EXIST "%APP_DIR%\config.yaml" (
    echo Copying default.config.yaml to config.yaml...
    copy "%APP_DIR%\default.config.yaml" "%APP_DIR%\config.yaml"
)
IF NOT EXIST "%APP_DIR%\msg_specs.py" (
    echo Copying default_msg_specs.py to msg_specs.py...
    copy "%APP_DIR%\default_msg_specs.py" "%APP_DIR%\msg_specs.py"
)

REM ---- Check Python ----
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python 3.10+ is required but not found.
    echo Please install Python and try again.
    pause
    exit /b
)

IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating new local virtual environment...
    python -m venv "%VENV_DIR%"
    REM ---- Activate venv ----
    call "%VENV_DIR%\Scripts\activate.bat"
    REM ---- Install / update dependencies (safe, quiet) ----
    SET PIP_DISABLE_PIP_VERSION_CHECK=1
    python -m pip install --upgrade pip >nul
    python -m pip install -r "%APP_DIR%\requirements.txt" --quiet
) ELSE (
    ECHO ---- Activate existing venv ----
    call "%VENV_DIR%\Scripts\activate.bat"
)

REM ---- Launch app ----
REM ---- Command-line mode ----
IF /I "%1"=="gui" (
    echo Starting Compare ISO8583 Amex GUI...
    streamlit run "%APP_DIR%\%APP_FILE%" --server.headless=true
    pause
    exit /b
)

IF /I "%1"=="cli" IF NOT "%2"=="" IF NOT "%3"=="" (
    echo Running Compare ISO8583 Amex CLI with command-line parameters...
    python "%APP_DIR%\compare_amex_cli.py" "%2" "%3%"
    pause
    exit /b
)

REM ---- Interactive menu fallback ----
echo.
echo Select mode:
echo   1. GUI (Streamlit)
echo   2. CLI (compare_amex_cli.py)
set /p MODE=Enter 1 or 2:

if "%MODE%"=="1" (
    echo Starting Compare ISO8583 Amex GUI...
    streamlit run "%APP_DIR%\%APP_FILE%" --server.headless=true
    pause
    exit /b
)

if "%MODE%"=="2" (
    set /p PARAM1=Enter first parameter:
    set /p PARAM2=Enter second parameter:
    echo Running Compare ISO8583 Amex CLI...
    python "%APP_DIR%\compare_amex_cli.py" "%PARAM1%" "%PARAM2%"
    pause
    exit /b
)

echo Invalid selection. Exiting.
pause
exit /b


