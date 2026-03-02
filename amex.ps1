# ==========================================
# One-click Streamlit Launcher (Latest)
# Local venv, shared app, self-healing
# ==========================================

$APP_DIR  = "C:\Users\bcorn\PythonProjects\compare_ifsf_amex"
$APP_FILE = "compare_amex_gui.py"

# Local venv per user
$VENV_DIR = "$env:LOCALAPPDATA\compare_iso8583_amex_venv"

# Environment hardening
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONUTF8              = "1"

# ---- Ensure config files exist ----
if (-not (Test-Path "$APP_DIR\config.yaml")) {
    Write-Host "Copying default_config.yaml to config.yaml..."
    Copy-Item "$APP_DIR\samples\default_config.yaml" "$APP_DIR\config.yaml"
}
if (-not (Test-Path "$APP_DIR\msg_specs.py")) {
    Write-Host "Copying default_msg_specs.py to msg_specs.py..."
    Copy-Item "$APP_DIR\samples\default_msg_specs.py" "$APP_DIR\msg_specs.py"
}

# ---- Check Python ----
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python 3.10+ is required but not found."
    Write-Host "Please install Python and try again."
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "$VENV_DIR\Scripts\Activate.ps1")) {
    Write-Host "Creating new local virtual environment..."
    python -m venv "$VENV_DIR"
    # ---- Activate venv ----
    . "$VENV_DIR\Scripts\Activate.ps1"
    # ---- Install / update dependencies (safe, quiet) ----
    $env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
    python -m pip install --upgrade pip | Out-Null
    python -m pip install -r "$APP_DIR\requirements.txt" --quiet
} else {
    Write-Host "---- Activate existing venv ----"
    . "$VENV_DIR\Scripts\Activate.ps1"
}

# ---- Launch app ----
# ---- Command-line mode ----
if ($args[0] -ieq "gui") {
    Write-Host "Starting Compare ISO8583 Amex GUI..."
    Set-Location $APP_DIR
    streamlit run "$APP_DIR\$APP_FILE" --server.headless=true
    Read-Host "Press Enter to exit"
    exit
}

if ($args[0] -ieq "cli" -and $args[1] -ne "" -and $args[2] -ne "") {
    Write-Host "Running Compare ISO8583 Amex CLI with command-line parameters..."
    Set-Location $APP_DIR
    python "$APP_DIR\compare_amex_cli.py" $args[1] $args[2] -c "$APP_DIR\config.yaml"
    Read-Host "Press Enter to exit"
    exit
}

# ---- Interactive menu fallback ----
Write-Host ""
Write-Host "Select mode:"
Write-Host "  1. GUI (Streamlit)"
Write-Host "  2. CLI (compare_amex_cli.py)"
$MODE = Read-Host "Enter 1 or 2"

if ($MODE -eq "1") {
    Write-Host "Starting Compare ISO8583 Amex GUI..."
    Set-Location $APP_DIR
    streamlit run "$APP_DIR\$APP_FILE" --server.headless=true
    Read-Host "Press Enter to exit"
    exit
}

if ($MODE -eq "2") {
    $PARAM1 = Read-Host "Enter first parameter"
    $PARAM2 = Read-Host "Enter second parameter"
    Write-Host "Running Compare ISO8583 Amex CLI..."
    Set-Location $APP_DIR
    python "$APP_DIR\compare_amex_cli.py" "$PARAM1" "$PARAM2" -c "$APP_DIR\config.yaml"
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "Invalid selection. Exiting."
Read-Host "Press Enter to exit"
exit 1
