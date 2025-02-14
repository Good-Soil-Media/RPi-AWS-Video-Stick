import json
import os
import getpass
import subprocess
import time

# Get the current user's username
username = getpass.getuser()

# File paths
CONFIG_FILE = f"/home/{username}/config.json"
SERVICE_FILE = "/etc/systemd/system/video_player.service"

# Systemd service template
SERVICE_TEMPLATE = """[Unit]
Description=Video Player Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/{username}/main.py
Restart=always
User={username}
Group={username}

[Install]
WantedBy=multi-user.target
"""

# Required system packages and Python libraries
SYSTEM_PACKAGES = ["python3", "python3-pip", "vlc", "awscli"]
PYTHON_LIBRARIES = ["boto3"]

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully!")
    except subprocess.CalledProcessError:
        print(f"❌ Error during: {description}. Try running manually: {command}")

def install_dependencies():
    """Install all required system and Python dependencies."""
    # Update package lists first
    run_command("sudo apt update && sudo apt upgrade -y", "Updating system packages")

    # Install system packages
    for package in SYSTEM_PACKAGES:
        run_command(f"sudo apt install -y {package}", f"Installing {package}")

    # Install Python libraries
    for lib in PYTHON_LIBRARIES:
        run_command(f"pip3 install {lib}", f"Installing {lib}")

def setup_config():
    """Set up configuration for video player."""
    if os.path.exists(CONFIG_FILE):
        print("Configuration already exists. Do you want to overwrite it? (y/n)")
        if input().lower() != 'y':
            return

    bucket_name = input("Enter the AWS S3 bucket name: ").strip()
    group_dir = input("Enter the group name (if applicable): ").strip()
    device_dir = input("Enter the S3 directory to monitor (e.g., 'device001'): ").strip()

    s3_dir = f"{group_dir}/{device_dir}" if group_dir else device_dir

    # Ensure config directory exists
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    # Save configuration including the username
    config = {
        "username": username,
        "bucket_name": bucket_name,
        "s3_dir": s3_dir
    }

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

    print(f"✅ Configuration saved at {CONFIG_FILE}")

def setup_service():
    """Set up systemd service for automatic startup."""
    print("\n🔄 Creating systemd service...")

    # Ensure the systemd directory exists
    if not os.path.exists("/etc/systemd/system/"):
        print("❌ Error: /etc/systemd/system/ does not exist. Are you running as root?")
        return

    # Create and save systemd service file
    try:
        with open(SERVICE_FILE, "w") as file:
            file.write(SERVICE_TEMPLATE.format(username=username))

        # Set permissions and reload systemd
        run_command(f"sudo chmod 644 {SERVICE_FILE}", "Setting service file permissions")
        run_command("sudo systemctl daemon-reload", "Reloading systemd")
        run_command("sudo systemctl enable video_player.service", "Enabling service")
        run_command("sudo systemctl start video_player.service", "Starting service")

        print(f"✅ Systemd service file created and enabled at {SERVICE_FILE}")

    except PermissionError:
        print(f"❌ Permission denied when writing to {SERVICE_FILE}. Run this script with sudo.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def configure_aws():
    """Prompt user to configure AWS CLI credentials."""
    print("\n🔄 Configuring AWS credentials...")
    run_command("aws configure", "Running AWS configuration setup")

def setup():
    """Main setup function that installs dependencies, configures the system, and sets up services."""
    print("\n🚀 Starting setup process...")
    
    install_dependencies()
    setup_config()
    setup_service()
    configure_aws()

    print("\n🎉 Setup complete! Your video player is now installed and running.")

if __name__ == "__main__":
    setup()
