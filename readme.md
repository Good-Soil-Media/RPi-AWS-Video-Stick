# **Raspberry Pi Video Player**

A lightweight Python-based video player for the **Raspberry Pi Zero 2 W** that plays a video file on loop, automatically updates content from an **AWS S3 bucket**, and logs errors for remote maintenance. **Now fully automated using `setup.py`!**

---

## **Table of Contents**
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Testing and Deployment](#testing-and-deployment)

---

## **Overview**
This project enables a Raspberry Pi to continuously play a video file while checking an AWS **S3 bucket** for updates. If a new video is uploaded, the Pi automatically downloads it, moves the old video to a backup folder, and plays the new file.

Designed for **digital signage, menus, and remote content updates** for businesses.

---

## **Features**
✅ Automatic **video playback on loop**  
✅ **Syncs** with an AWS **S3 bucket** for updates  
✅ Moves old videos to **backup storage**  
✅ Logs errors for **remote debugging**  
✅ **Automatically runs on boot** via `systemd`  
✅ **Fully automated installation** using `setup.py`  

---

## **Requirements**
### **Hardware**
- Raspberry Pi Zero 2 W (or any compatible Raspberry Pi)
- MicroSD card (8GB+ recommended)
- Internet connection (WiFi or Ethernet)

### **Software**
- Raspberry Pi OS Lite
- Python 3
- VLC Media Player
- AWS CLI
- Boto3 (AWS SDK for Python)
- `systemd` (for auto-starting the script)

---

## **Installation**

### **1. Prepare Your Raspberry Pi**
1. **Install Raspberry Pi OS Lite**  
   - Download from the [official website](https://www.raspberrypi.com/software/).  
   - Flash it onto an **SD card** using [Raspberry Pi Imager](https://www.raspberrypi.com/software/).  
   - Enable SSH during setup.

2. **Boot the Pi and Connect via SSH**  
   ```bash
   ssh <username>@<pi-name>.local
   ```

3. **Update the System (Optional but Recommended)**  
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

### **2. Download and Install the Software**
#### **Download the Latest Release**
First, navigate to your home directory and download the latest release:
```bash
cd ~
wget <repository_release_link> -O repo.tar.gz
```

Extract the contents directly into the home directory:
```bash
tar -xvzf repo.tar.gz --strip-components=1
```

Or, if using Git:
```bash
git clone --depth=1 <repository_git_link> ~
```

🎉 **Everything is now handled by the `setup.py` script!** 🎉

Run the following command:
```bash
sudo python3 setup.py
```

🔄 **This script will:**
- Install all necessary software packages (`python3`, `vlc`, `awscli`, `boto3`, etc.).
- Configure AWS S3 settings.
- Create a `systemd` service so the video player runs on boot.
- Prompt you to enter your AWS credentials (`aws configure`).
- Automatically start the service after installation.

⚠️ **Note:** `setup.py` does **not** build `main.py`. You must ensure `main.py` is included in the release you cloned or manually copy it to the correct directory.

Once completed, **your Raspberry Pi video player is ready to go!** 🚀

---

## **Usage**

### **Checking Logs**
To see playback activity and error logs:
```bash
cat /home/<username>/video_player.log
```

### **Manually Forcing an Update**
If you need to check for new videos immediately:
```bash
python3 /home/<username>/main.py update
```

### **Restart the Service**
If the video player isn't running:
```bash
sudo systemctl restart video_player.service
```

### **Stopping the Service**
To stop the player manually:
```bash
sudo systemctl stop video_player.service
```

---

## **Testing and Deployment**

### **Test Locally**
- Upload a sample video to the **S3 bucket**.
- Ensure the Pi **downloads** and **plays** it.

### **Deploy to Clients**
- Install the Raspberry Pi at the **client’s location**.
- Verify **internet connectivity** for remote updates.

### **Remote Maintenance**
- Use **SSH** or **Raspberry Pi Connect** for debugging.

---

### 🎉 **Congratulations! Your Raspberry Pi video player is now set up and running.** 🎉

