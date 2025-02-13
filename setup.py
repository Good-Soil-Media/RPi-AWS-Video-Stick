import json
import os

CONFIG_FILE = "/home/goodsoilmedia/config.json"

def setup():
    """Set up the configuration for the video player."""
    if os.path.exists(CONFIG_FILE):
        print("Configuration already exists. Do you want to overwrite it? (y/n)")
        if input().lower() != 'y':
            return

    bucket_name = input("Enter the AWS S3 bucket name: ").strip()
    group_dir = input("Enter the group name (if applicable): ").strip()
    device_dir = input("Enter the S3 directory to monitor (e.g., 'device001'): ").strip()

    if group_dir != "":
        s3_dir = f"{group_dir}/{device_dir}"
    else:
        s3_dir = device_dir

    config = {
        "bucket_name": bucket_name,
        "s3_dir": s3_dir
    }

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)
    print("Configuration saved.")

if __name__ == "__main__":
    setup()