import os
import json
import subprocess
import logging
import requests
import time
from pathlib import Path

# Constants
HOME_DIR = os.environ.get("HOME", "/home/pi")
CONFIG_FILE = os.path.join(HOME_DIR, "config.json")
LOG_FILE = os.path.join(HOME_DIR, "video_player.log")
LOCAL_VIDEO_DIR = os.path.join(HOME_DIR, "video")
GITHUB_API = "https://api.github.com/repos/{}/tags"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_config():
    """Load configuration from config.json."""
    if not os.path.exists(CONFIG_FILE):
        logging.error("Configuration file not found. Run setup first.")
        raise Exception("Configuration file missing.")
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def get_latest_github_version(repo):
    """Retrieve the latest tag from the GitHub repository, formatted as vX.Y.Z."""
    url = GITHUB_API.format(repo)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        tags = response.json()
        if tags:
            return tags[0]['name']  # Ensure tags are formatted as vX.Y.Z
    except Exception as e:
        logging.error(f"Failed to fetch GitHub tags: {e}")
        return None

def check_for_updates():
    """Compare local version against the latest GitHub release."""
    config = load_config()
    github_repo = config["github_url"]
    local_version = config.get("firmware_version", "v0.0.0")
    latest_version = get_latest_github_version(github_repo)
    
    if latest_version and latest_version != local_version:
        logging.info(f"New firmware available: {latest_version} (current: {local_version})")
        return latest_version
    
    logging.info("No new firmware updates found.")
    return None

def restore_from_version(version):
    """Restore main.py and setup.py to a specified version from GitHub."""
    config = load_config()
    github_repo = config["github_url"]
    repo_url = f"https://github.com/{github_repo}/archive/refs/tags/v{version}.zip"
    temp_dir = "/tmp/video_player_restore"
    
    if os.path.exists(temp_dir):
        subprocess.run(["rm", "-rf", temp_dir])
    os.makedirs(temp_dir, exist_ok=True)
    
    zip_file = os.path.join(temp_dir, "restore.zip")
    subprocess.run(["wget", "-O", zip_file, repo_url])
    subprocess.run(["unzip", zip_file, "-d", temp_dir])
    extracted_dir = os.path.join(temp_dir, f"RPi-AWS-Video-Stick-v{version}")
    
    for file in ["main.py", "setup.py"]:
        src = os.path.join(extracted_dir, file)
        dest = os.path.join(HOME_DIR, file)
        if os.path.exists(src):
            subprocess.run(["cp", src, dest])
            logging.info(f"Restored {file} to version v{version}.")
    
    subprocess.run(["rm", "-rf", temp_dir])
    logging.info("Firmware restoration complete.")

def stop_video_process():
    """Stop the VLC video process if running."""
    subprocess.run(["pkill", "-f", "cvlc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logging.info("Stopped video playback process.")

def restart_video_process():
    """Restart the video process."""
    subprocess.run(["systemctl", "restart", "video_player.service"])
    logging.info("Restarted video playback process.")

def display_logs():
    """Display the contents of the log file."""
    try:
        with open(LOG_FILE, "r") as file:
            print(file.read())
    except Exception as e:
        logging.error(f"Error displaying logs: {e}")

def backup_last_firmware():
    """Create a backup of the current firmware files."""
    backup_dir = os.path.join(HOME_DIR, "firmware_backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    files_to_backup = ["main.py", "setup.py"]
    for file in files_to_backup:
        src = os.path.join(HOME_DIR, file)
        dest = os.path.join(backup_dir, f"{file}.{int(time.time())}")
        subprocess.run(["cp", src, dest])
        logging.info(f"Backed up {file} to {dest}")

def restore_last_firmware():
    """Restore the most recent backup for main.py and setup.py."""
    backup_dir = os.path.join(HOME_DIR, "firmware_backup")
    if not os.path.exists(backup_dir):
        logging.error("No backup directory found.")
        return
    for file in ["main.py", "setup.py"]:
        backups = sorted(Path(backup_dir).glob(f"{file}.*"), key=os.path.getmtime, reverse=True)
        if backups:
            src = str(backups[0])
            dest = os.path.join(HOME_DIR, file)
            subprocess.run(["cp", src, dest])
            logging.info(f"Restored {file} from backup {src}")
        else:
            logging.error(f"No backups found for {file} to restore.")


def update_firmware(new_version):
    """Download and apply the new firmware version."""
    config = load_config()
    github_repo = config["github_url"]
    repo_url = f"https://github.com/{github_repo}/archive/refs/tags/{new_version}.zip"
    temp_dir = "/tmp/video_player_update"
    
    if os.path.exists(temp_dir):
        subprocess.run(["rm", "-rf", temp_dir])
    os.makedirs(temp_dir, exist_ok=True)
    
    zip_file = os.path.join(temp_dir, "update.zip")
    subprocess.run(["wget", "-O", zip_file, repo_url])
    subprocess.run(["unzip", zip_file, "-d", temp_dir])
    extracted_dir = os.path.join(temp_dir, f"RPi-AWS-Video-Stick-{new_version}")
    
    for file in ["main.py", "setup.py"]:
        src = os.path.join(extracted_dir, file)
        dest = os.path.join(HOME_DIR, file)
        if os.path.exists(src):
            subprocess.run(["cp", src, dest])
            logging.info(f"Updated {file} to version {new_version}.")
    
    subprocess.run(["rm", "-rf", temp_dir])
    
    config["firmware_version"] = new_version
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)
    
    logging.info("Firmware update complete.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "check_updates":
            latest_version = check_for_updates()
            if latest_version:
                print(f"New update available: {latest_version}")
            else:
                print("No updates found.")
        elif cmd == "update_firmware":
            latest_version = check_for_updates()
            if latest_version:
                stop_video_process()
                update_firmware(latest_version)
                restart_video_process()
        elif cmd == "restore_firmware":
            restore_last_firmware()
        elif cmd == "restore_from_version" and len(sys.argv) == 3:
            restore_from_version(sys.argv[2])
        elif cmd == "backup_firmware":
            backup_last_firmware()
        elif cmd == "display_logs":
            display_logs()
        else:
            print("Unknown command. Options: check_updates, update_firmware, restore_firmware, restore_from_version <version>, backup_firmware, display_logs")
