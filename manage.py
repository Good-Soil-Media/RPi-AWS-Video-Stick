from pathlib import Path
import json
import subprocess
import os, json, logging
import time
import logging

# Replace <username> with your actual username or use os.environ["HOME"]
HOME_DIR = os.environ.get("HOME", "/home/pi")
CONFIG_FILE = os.path.join(HOME_DIR, "config.json")
LOG_FILE = os.path.join(HOME_DIR, "video_player.log")
LOCAL_VIDEO_DIR = os.path.join(HOME_DIR, "video")

# Setup logging (this will be shared by main.py when imported)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_config():
    """Load configuration from config.json. If not present, run setup() to create one."""
    if not os.path.exists(CONFIG_FILE):
        print("Configuration file not found. Running setup...")
        try:
            from setup import setup
            setup()  # This will run the interactive setup process
        except Exception as e:
            logging.error(f"Error running setup: {e}")
            raise Exception("Setup failed. Exiting.")
        # Check again if the file was created
        if not os.path.exists(CONFIG_FILE):
            logging.error("Configuration file still not found after running setup.")
            raise Exception("Configuration file not created. Exiting.")

    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            logging.info("Configuration loaded successfully.")
            return config
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise


def check_for_updates():
    """
    Check if there is a new version of the firmware on GitHub.
    This function could compare a local version number vs. a remote one.
    For now, it just logs the check.
    """
    logging.info("Checking for firmware updates...")
    # TODO: Implement actual update checking logic (e.g., via an API call or version file).
    return False

def update_firmware(url=None):
    """
    Update the firmware from GitHub.
    This function clones the repository to a temporary directory, copies new files, and cleans up.
    """
    config = load_config()
    github_url = config["github_url"]
    repo_url = f"https://github.com/{github_url}"
    logging.info(f"Updating firmware from {repo_url}")
    temp_dir = "/tmp/video_player_update"
    if os.path.exists(temp_dir):
        subprocess.run(["rm", "-rf", temp_dir])
    subprocess.run(["git", "clone", repo_url, temp_dir])
    # Assume the repo has updated main.py, manage.py, and setup.py.
    files_to_update = ["main.py", "manage.py", "setup.py"]
    for file in files_to_update:
        src = os.path.join(temp_dir, file)
        dest = os.path.join(HOME_DIR, file)
        subprocess.run(["cp", src, dest])
        logging.info(f"Updated {file}")
    subprocess.run(["rm", "-rf", temp_dir])
    logging.info("Firmware update complete.")

def backup_last_firmware():
    """
    Create a backup of the current firmware files.
    Backups are stored in a subdirectory called firmware_backup.
    """
    backup_dir = os.path.join(HOME_DIR, "firmware_backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    files_to_backup = ["main.py", "manage.py", "setup.py"]
    for file in files_to_backup:
        src = os.path.join(HOME_DIR, file)
        dest = os.path.join(backup_dir, f"{file}.{int(time.time())}")
        subprocess.run(["cp", src, dest])
        logging.info(f"Backed up {file} to {dest}")

def restore_last_firmware():
    """
    Restore the most recent backup for main.py.
    (You can extend this to restore all files if needed.)
    """
    backup_dir = os.path.join(HOME_DIR, "firmware_backup")
    if not os.path.exists(backup_dir):
        logging.error("No backup directory found.")
        return
    backups = {}
    for file in os.listdir(backup_dir):
        if file.startswith("main.py"):
            backups[file] = os.path.getmtime(os.path.join(backup_dir, file))
    if backups:
        latest_backup = max(backups, key=backups.get)
        src = os.path.join(backup_dir, latest_backup)
        dest = os.path.join(HOME_DIR, "main.py")
        subprocess.run(["cp", src, dest])
        logging.info(f"Restored {dest} from backup {src}")
    else:
        logging.error("No backups found to restore.")

def display_logs():
    """Display the contents of the log file."""
    try:
        with open(LOG_FILE, "r") as file:
            print(file.read())
    except Exception as e:
        logging.error(f"Error displaying logs: {e}")

if __name__ == "__main__":
    import sys
    # Simple command-line interface for management functions.
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "update_firmware":
            update_firmware()
        elif cmd == "backup_firmware":
            backup_last_firmware()
        elif cmd == "restore_firmware":
            restore_last_firmware()
        elif cmd == "display_logs":
            display_logs()
        elif cmd == "check_updates":
            if check_for_updates():
                print("Firmware update available.")
            else:
                print("No firmware updates found.")
        else:
            print("Unknown command. Options: update_firmware, backup_firmware, restore_firmware, display_logs, check_updates")
    else:
        # If no command is provided, run the main video playback logic.
        try:
            import main
            main.main()
        except Exception as e:
            logging.error(f"Fatal error in management: {e}")
