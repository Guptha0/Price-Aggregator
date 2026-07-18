import os
import sys
import argparse
import subprocess
import platform
import tempfile
from pathlib import Path

# ANSI color codes for clean terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def get_project_paths():
    """Resolves absolute paths for the project root, venv Python, main script, and log dir."""
    project_root = Path(__file__).parent.resolve()
    
    # Determine the venv python executable path based on OS
    if platform.system() == "Windows":
        python_exe = project_root / "venv" / "Scripts" / "python.exe"
    else:
        python_exe = project_root / "venv" / "bin" / "python"
        
    main_py = project_root / "main.py"
    log_dir = project_root / "logs"
    cron_log = log_dir / "cron.log"
    ps_script = project_root / "run_daily_tracker.ps1"
    
    return project_root, python_exe, main_py, log_dir, cron_log, ps_script

def install_windows_task(ps_script, project_root):
    """Registers a hidden Windows Task Scheduler job."""
    task_name = "UniversalPriceTracker"
    
    if not ps_script.exists():
        print(f"{RED}[ERROR] run_daily_tracker.ps1 wrapper not found at {ps_script}.{RESET}")
        sys.exit(1)
        
    # We execute powershell with -WindowStyle Hidden to ensure no black console window flashes
    ps_command = (
        f"$Action = New-ScheduledTaskAction -Execute 'powershell.exe' "
        f"-Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -File \"{ps_script}\"'; "
        f"$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM; "
        f"Register-ScheduledTask -TaskName '{task_name}' -Action $Action -Trigger $Trigger "
        f"-Description 'Runs the daily price aggregator background scraper' -Force"
    )
    
    try:
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, check=True)
        print(f"{GREEN}[SUCCESS] Windows Task '{task_name}' installed to run daily at 9:00 AM.{RESET}")
        print(f"Executing: powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File {ps_script}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}[ERROR] Failed to install Windows Task Scheduler job. Ensure you are running as Administrator.{RESET}")
        print(e.stderr)

def remove_windows_task():
    """Removes the Windows Task Scheduler job."""
    task_name = "UniversalPriceTracker"
    ps_command = f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false"
    
    try:
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, check=True)
        print(f"{GREEN}[SUCCESS] Windows Task '{task_name}' successfully removed.{RESET}")
    except subprocess.CalledProcessError:
        print(f"{YELLOW}[INFO] Task '{task_name}' was not found or already removed.{RESET}")

def install_unix_cron(python_exe, main_py, cron_log):
    """Installs a crontab entry on Linux/macOS."""
    cron_job = f"0 9 * * * {python_exe} {main_py} >> {cron_log} 2>&1"
    marker = "UniversalPriceTracker"
    
    # Get current crontab
    try:
        current_crontab = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        print(f"{RED}[ERROR] 'crontab' command not found. Is cron installed?{RESET}")
        sys.exit(1)
    except subprocess.CalledProcessError:
        # Expected if no crontab exists for user yet
        current_crontab = ""
        
    if marker in current_crontab:
        print(f"{YELLOW}[INFO] Cron job already exists for {marker}. Use --remove first if you want to update it.{RESET}")
        return
        
    # Append new job
    new_crontab = current_crontab + f"\n# {marker} Background Job\n{cron_job}\n"
    
    # Write to temp file and load
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(new_crontab)
        tmp_path = tmp.name
        
    try:
        subprocess.run(["crontab", tmp_path], check=True)
        print(f"{GREEN}[SUCCESS] Unix Cron job installed to run daily at 9:00 AM.{RESET}")
        print(f"Registered Job: {cron_job}")
    except subprocess.CalledProcessError:
        print(f"{RED}[ERROR] Failed to install cron job.{RESET}")
    finally:
        os.remove(tmp_path)

def remove_unix_cron():
    """Removes the crontab entry on Linux/macOS."""
    marker = "UniversalPriceTracker"
    
    try:
        current_crontab = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        print(f"{YELLOW}[INFO] No crontab found for current user.{RESET}")
        return
    except FileNotFoundError:
        print(f"{RED}[ERROR] 'crontab' command not found.{RESET}")
        return
        
    if marker not in current_crontab:
        print(f"{YELLOW}[INFO] No cron job found for {marker}.{RESET}")
        return
        
    # Filter out lines related to our job
    lines = current_crontab.splitlines()
    new_lines = []
    
    for line in lines:
        if f"# {marker}" in line:
            continue
        if "main.py >>" in line and "cron.log" in line:
            continue
        new_lines.append(line)
        
    new_crontab = "\n".join(new_lines) + "\n" if new_lines else ""
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(new_crontab)
        tmp_path = tmp.name
        
    try:
        # If crontab is completely empty, remove it natively
        if not new_crontab.strip():
            subprocess.run(["crontab", "-r"], check=True)
        else:
            subprocess.run(["crontab", tmp_path], check=True)
        print(f"{GREEN}[SUCCESS] Unix Cron job for '{marker}' successfully removed.{RESET}")
    except subprocess.CalledProcessError:
        print(f"{RED}[ERROR] Failed to update crontab.{RESET}")
    finally:
        os.remove(tmp_path)

def main():
    parser = argparse.ArgumentParser(description="Universal Price Aggregator Scheduler Setup")
    parser.add_argument("--install", action="store_true", help="Install the background scheduler task")
    parser.add_argument("--remove", action="store_true", help="Remove the background scheduler task")
    args = parser.parse_args()
    
    if not args.install and not args.remove:
        parser.print_help()
        sys.exit(0)

    project_root, python_exe, main_py, log_dir, cron_log, ps_script = get_project_paths()
    os_name = platform.system()
    
    if args.install:
        print(f"[{os_name}] Verifying environment...")
        
        # 1. Check for Virtual Environment
        if not python_exe.exists():
            print(f"{RED}[ERROR] Virtual environment not found at: {python_exe}{RESET}")
            print(f"Please create it first:\n  python -m venv venv\n  source venv/bin/activate (or .\\venv\\Scripts\\Activate.ps1)\n  pip install -r requirements.txt")
            sys.exit(1)
            
        # 2. Ensure log directory exists
        log_dir.mkdir(exist_ok=True)
        
        # 3. Route to OS specific installer
        if os_name == "Windows":
            install_windows_task(ps_script, project_root)
        else:
            install_unix_cron(python_exe, main_py, cron_log)
            
    elif args.remove:
        print(f"[{os_name}] Removing background tasks...")
        if os_name == "Windows":
            remove_windows_task()
        else:
            remove_unix_cron()

if __name__ == "__main__":
    main()
