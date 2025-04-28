# **Raspberry Pi Media Player**

A lightweight Python-based media player for the **Raspberry Pi Zero 2 W** that plays videos and displays images, supports playlists, automatically updates content from an **AWS S3 bucket**, and logs errors for remote maintenance.

---

## **Table of Contents**
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Prepare Your Raspberry Pi](#1-prepare-your-raspberry-pi)
  - [Set Up AWS S3 Bucket](#2-set-up-aws-s3-bucket)
  - [Install Required Software](#3-install-required-software)
  - [Project Setup](#4-project-setup)
  - [Configure and Automate the System](#5-configure-and-automate-the-system)
- [Usage](#usage)
  - [Creating Playlists](#creating-playlists)
  - [Checking Logs](#checking-logs)
  - [Manually Forcing an Update](#manually-forcing-an-update)
- [Troubleshooting](#troubleshooting)

---

## **Overview**
This project enables a Raspberry Pi to continuously play videos and display images while checking an AWS **S3 bucket** for updates. It supports playlist functionality allowing you to specify the order of media and display durations for images. When new content is uploaded, the Pi automatically downloads it, moves old content to a backup folder, and updates the display.

Designed for digital signage, information displays, menus, and other content that needs to be remotely updated.

---

## **Features**
✅ **Video and image support** - Play videos and display static images  
✅ **Playlist functionality** - Order your content with custom durations for images  
✅ **Download integrity verification** - Failsafe mechanisms for interrupted downloads  
✅ **Syncs** with an AWS **S3 bucket** for remote updates  
✅ **Backup system** for previously displayed content  
✅ **Detailed logging** for remote debugging  
✅ **Automatically runs on boot** via `systemd`  

---

## **Requirements**
- **Hardware**: Raspberry Pi Zero 2 W (or any compatible Raspberry Pi)
- **Software**:
  - Raspberry Pi OS Lite (32-bit recommended for Pi Zero 2 W)
  - Python 3
  - VLC Media Player (for videos)
  - Feh (for image display)
  - AWS CLI
  - Python packages: boto3, pillow
  - `systemd` for auto-starting scripts

---

## **Installation**

### **1. Prepare Your Raspberry Pi**
1. **Install Raspberry Pi OS Lite**
   - Flash the official Raspberry Pi OS Lite 32-bit image onto an **SD card** using [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
   - Enable SSH during setup with the Raspberry Pi Imager

2. **Boot the Pi and Connect via SSH**
   ```bash
   ssh <username>@<pi-name>.local
   ```

3. **Update the System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

---

### **2. Set Up AWS S3 Bucket**
1. **Create an S3 Bucket**
   - Go to [AWS S3 Console](https://s3.console.aws.amazon.com/)
   - Click "**Create Bucket**" and configure:
     - **Bucket Name:** Choose a unique name
     - **Region:** Select closest to the Raspberry Pi location
     - **Block Public Access:** Enabled
     - **Encryption:** **SSE-S3** for security (optional)
    - Create Directories Based on Group Name and Device Name

2. **Create an IAM User and Access Keys**
   - Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
   - Create a new user with programmatic access
   - Attach a policy with permissions for your S3 bucket
   - Save the Access Key ID and Secret Access Key

3. **Create IAM Policy for Raspberry Pi**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "s3:ListBucket",
         "Resource": "arn:aws:s3:::<bucket_name>",
         "Condition": {
           "StringLike": {
             "s3:prefix": "<directory>/*"
           }
         }
       },
       {
         "Effect": "Allow",
         "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
         "Resource": "arn:aws:s3:::<bucket_name>/<directory>/*"
       }
     ]
   }
   ```

---

### **3. Install Required Software**
```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y python3 python3-pip vlc feh awscli

# Install Python packages
sudo apt install python3-boto3 python3-pillow
```

### **4. Project Setup**
1. **Download or Copy Setup.py from Repository**
    - https://github.com/Good-Soil-Media/RPi-AWS-Video-Stick.git

2. **Make Script Executable**
   ```bash
   chmod +x setup.py
   ```

3. **Configure AWS Credentials**
   ```bash
   aws configure
   ```
   Enter your AWS Access Key ID, Secret Access Key, region, and preferred output format

4. **Run the Setup Script**
   ```bash
   python3 setup.py
   ```
   Follow the prompts to enter your configuration details:
   - S3 bucket name
   - Group name (optional)
   - Device name
   - Update check interval (in seconds)

---

### **5. Configure and Automate the System**
1. **Test the Main Script**
   ```bash
   python3 ~/main.py
   ```

2. **Create a `systemd` Service File**
   ```bash
   sudo nano /etc/systemd/system/media_player.service
   ```
   Paste the following (replace `<username>` with your actual username):
   ```ini
   [Unit]
   Description=Media Player Service
   After=network.target

   [Service]
   Environment=DISPLAY=:0
   ExecStart=/usr/bin/python3 /home/<username>/main.py
   Restart=always
   User=<username>
   Group=<username>

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable & Start the Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable media_player.service
   sudo systemctl start media_player.service
   ```

---

## **Usage**

### **Creating Playlists**
The system supports playlist functionality for specifying the order and display duration of your media files.

1. **Playlist Format**
   Create a JSON file named `playlist.json` with the following structure:
   ```json
   [
     {
       "filename": "video1.mp4",
       "order": 1,
       "duration": null
     },
     {
       "filename": "image1.jpg",
       "order": 2,
       "duration": 15
     },
     {
       "filename": "image2.png",
       "order": 3,
       "duration": 10
     },
     {
       "filename": "video2.mp4",
       "order": 4,
       "duration": null
     }
   ]
   ```

   - `filename`: Name of the media file
   - `order`: Position in the playlist (lower numbers play first)
   - `duration`: For images, seconds to display (default: 10); for videos, use `null` to play full duration

2. **Uploading Content**
   Upload your media files and playlist to S3:
   ```
   <bucket_name>/<group_name>/<device_name>/media/video1.mp4
   <bucket_name>/<group_name>/<device_name>/media/image1.jpg
   <bucket_name>/<group_name>/<device_name>/playlist.json
   ```

### **Checking Logs**
```bash
cat ~/video_player.log
```

### **Manually Forcing an Update**
```bash
python3 ~/main.py update
```

### **Checking Service Status**
```bash
sudo systemctl status media_player.service
```

### **Restarting the Service**
```bash
sudo systemctl restart media_player.service
```

---

## **Troubleshooting**

### **Display Issues**
- Ensure `DISPLAY=:0` is set in the systemd service file
- For headless setups, install and configure `xorg` or use a desktop environment

### **Media Playback Issues**
- Videos: Ensure VLC is installed correctly (`sudo apt install vlc`)
- Images: Ensure Feh is installed correctly (`sudo apt install feh`)
- For older Raspberry Pi models, limit video resolution to 1080p or less

### **AWS Connection Issues**
- Verify your AWS credentials are correctly configured
- Check internet connectivity
- Ensure IAM permissions are correctly set up

### **System Not Starting On Boot**
- Check systemd service status: `sudo systemctl status media_player.service`
- Review logs for errors: `sudo journalctl -u media_player.service`

---

### 🎉 **Congratulations! Your Enhanced Raspberry Pi Media Player is now set up and running.** 🎉