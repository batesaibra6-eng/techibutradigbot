# ==============================================================================
# FOREX BOT — Update Script
# Run to update bot files and restart the service
# ==============================================================================

$BOT_DIR = "C:\ForexBot"

Write-Host "Stopping bot..." -ForegroundColor Yellow
schtasks /end /tn "ForexBot" 2>$null
Start-Sleep -Seconds 3

Write-Host "Updating dependencies..." -ForegroundColor Yellow
& "$BOT_DIR\venv\Scripts\pip.exe" install -r "$BOT_DIR\requirements.txt" --upgrade

Write-Host "Restarting bot..." -ForegroundColor Yellow
schtasks /run /tn "ForexBot"

Write-Host "Bot updated and restarted." -ForegroundColor Green
