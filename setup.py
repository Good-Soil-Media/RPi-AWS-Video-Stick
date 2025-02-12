import json
import os

# Adjust this path if needed (e.g., use /home/pi or /home/<username>)
CONFIG_FILE = "/home/pi/config.json"

def setup():
    """Set up the configuration for the video player."""
    if os.path.exists(CONFIG_FILE):
        print("Configuration already exists. Do you want to overwrite it? (y/n)")
        if input().lower() != 'y':
            return

    bucket_name = input("Enter the AWS S3 bucket name: ").strip()
    group_dir = input("Enter the group name (if applicable): ").strip()
    device_dir = input("Enter the S3 directory to monitor (e.g., 'device001'): ").strip()
    github_url = input("Enter the GitHub URL for the project: ").strip()
    firmware_version = input("Enter the initial firmware version: ").strip()

    if github_url == "":
        github_url = "SilentKnight-24/RPi-AWS-Video-Stick"
    
    if group_dir != "":
        s3_dir = f"{group_dir}/{device_dir}"
    else:
        s3_dir = device_dir
    
    config = {
        "bucket_name": bucket_name,
        "s3_dir": s3_dir,
        "github_url": github_url,
        "firmware_version": firmware_version
    }

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)
    print("Configuration saved.")

if __name__ == "__main__":
    setup()
