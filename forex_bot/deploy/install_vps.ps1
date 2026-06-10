# ==============================================================================
# FOREX BOT — Windows VPS Auto-Installer (PowerShell)
# Run as Administrator in PowerShell:
#   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\deploy\install_vps.ps1
# ==============================================================================

$ErrorActionPreference = "Stop"
$BOT_DIR = "C:\ForexBot"
$PYTHON_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$PYTHON_INSTALLER = "$env:TEMP\python_installer.exe"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  INSTITUTIONAL FOREX BOT — VPS INSTALLER" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# ── 1. Check/Install Python ──────────────────────────────────────────────────
Write-Host "`n[1/7] Checking Python installation..." -ForegroundColor Yellow

$pythonOk = $false
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "Python 3\.(1[0-9]|[89])") {
        Write-Host "  Python found: $pyVersion" -ForegroundColor Green
        $pythonOk = $true
    }
} catch {}

if (-not $pythonOk) {
    Write-Host "  Downloading Python 3.11..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $PYTHON_URL -OutFile $PYTHON_INSTALLER -UseBasicParsing
    Write-Host "  Installing Python (silent)..."
    Start-Process -FilePath $PYTHON_INSTALLER -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User")
    Write-Host "  Python installed." -ForegroundColor Green
}

# ── 2. Create Bot Directory ──────────────────────────────────────────────────
Write-Host "`n[2/7] Creating bot directory at $BOT_DIR..." -ForegroundColor Yellow
if (-not (Test-Path $BOT_DIR)) {
    New-Item -ItemType Directory -Path $BOT_DIR | Out-Null
}

# Copy bot files (assumes script is run from the forex_bot directory)
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$SOURCE_DIR  = Split-Path -Parent $SCRIPT_DIR   # one level up from deploy/
Write-Host "  Copying files from $SOURCE_DIR to $BOT_DIR..."
Copy-Item -Path "$SOURCE_DIR\*" -Destination $BOT_DIR -Recurse -Force
Write-Host "  Files copied." -ForegroundColor Green

# ── 3. Create Virtual Environment ────────────────────────────────────────────
Write-Host "`n[3/7] Creating Python virtual environment..." -ForegroundColor Yellow
Set-Location $BOT_DIR
python -m venv venv
Write-Host "  Virtual environment created." -ForegroundColor Green

# ── 4. Install Dependencies ──────────────────────────────────────────────────
Write-Host "`n[4/7] Installing Python dependencies..." -ForegroundColor Yellow
& "$BOT_DIR\venv\Scripts\pip.exe" install --upgrade pip
& "$BOT_DIR\venv\Scripts\pip.exe" install -r "$BOT_DIR\requirements.txt"
Write-Host "  Dependencies installed." -ForegroundColor Green

# ── 5. Configure .env ────────────────────────────────────────────────────────
Write-Host "`n[5/7] Setting up .env configuration..." -ForegroundColor Yellow
$envFile = "$BOT_DIR\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item "$BOT_DIR\.env.example" $envFile
    Write-Host "  .env created from template." -ForegroundColor Yellow
    Write-Host "  *** IMPORTANT: Edit $envFile with your credentials! ***" -ForegroundColor Red
} else {
    Write-Host "  .env already exists — not overwritten." -ForegroundColor Green
}

# ── 6. Create Windows Service (Task Scheduler) ───────────────────────────────
Write-Host "`n[6/7] Registering Windows Task Scheduler job..." -ForegroundColor Yellow

$taskName   = "ForexBot"
$taskAction = New-ScheduledTaskAction `
    -Execute "$BOT_DIR\venv\Scripts\python.exe" `
    -Argument "$BOT_DIR\main.py" `
    -WorkingDirectory $BOT_DIR

$taskTrigger = New-ScheduledTaskTrigger -AtStartup

$taskSettings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Days 0) `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Remove if exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $taskAction `
    -Trigger $taskTrigger `
    -Settings $taskSettings `
    -Principal $taskPrincipal `
    -Description "Institutional Forex Trading Bot (24/7)"

Write-Host "  Task '$taskName' registered — auto-starts on boot." -ForegroundColor Green

# ── 7. Create Convenience Scripts ────────────────────────────────────────────
Write-Host "`n[7/7] Creating convenience scripts..." -ForegroundColor Yellow

@"
@echo off
cd /d C:\ForexBot
call venv\Scripts\activate.bat
python main.py
pause
"@ | Out-File -FilePath "$BOT_DIR\START_BOT.bat" -Encoding ASCII

@"
@echo off
schtasks /end /tn "ForexBot"
echo Bot stopped.
pause
"@ | Out-File -FilePath "$BOT_DIR\STOP_BOT.bat" -Encoding ASCII

@"
@echo off
schtasks /run /tn "ForexBot"
echo Bot started via Task Scheduler.
pause
"@ | Out-File -FilePath "$BOT_DIR\RESTART_BOT.bat" -Encoding ASCII

Write-Host "  Scripts created: START_BOT.bat, STOP_BOT.bat, RESTART_BOT.bat" -ForegroundColor Green

# ── DONE ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  INSTALLATION COMPLETE" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Edit: C:\ForexBot\.env  (add your MT5 + Telegram credentials)"
Write-Host "  2. Ensure MetaTrader 5 is installed and logged into your broker"
Write-Host "  3. Start bot: Double-click START_BOT.bat  -OR-  reboot (auto-start)"
Write-Host ""
Write-Host "Logs will be saved to: C:\ForexBot\logs\" -ForegroundColor Yellow
Write-Host ""
