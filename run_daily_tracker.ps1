$ProjectDir = "F:\price_tracker"
Set-Location -Path $ProjectDir

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Ensure logs directory exists
$LogDir = Join-Path -Path $ProjectDir -ChildPath "logs"
if (-not (Test-Path -Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$LogFile = Join-Path -Path $LogDir -ChildPath "cron.log"

# Log execution start timestamp
$dateString = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "`n[CRON EXECUTION TRIGGERED] $dateString"

# Run python orchestrator and append output to log file
python main.py >> $LogFile 2>&1
