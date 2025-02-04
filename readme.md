# **Raspberry Pi Video Player**
A lightweight Python-based video player for the **Raspberry Pi Zero 2 W** that plays a video file on loop, automatically updates content from an **AWS S3 bucket**, and logs errors for remote maintenance.

---

## **Table of Contents**
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Prepare Your Raspberry Pi](#1-prepare-your-raspberry-pi)
  - [Set Up AWS S3 Bucket](#2-set-up-aws-s3-bucket)
  - [Install Required Software](#3-install-required-software)
  - [Project Directory Setup](#4-project-directory-setup)
  - [Configure and Automate the System](#5-configure-and-automate-the-system)
- [Usage](#usage)
  - [Checking Logs](#checking-logs)
  - [Manually Forcing an Update](#manually-forcing-an-update)
- [Testing and Deployment](#testing-and-deployment)
- [License](#license)

---

## **Overview**
This project enables a Raspberry Pi to continuously play a video file while checking an AWS **S3 bucket** for updates. If a new video is uploaded, the Pi automatically downloads it, moves the old video to a backup folder, and plays the new file. 

Designed for **remote digital signage**, this system includes logging and system monitoring.

---

## **Features**
✅ Automatic **video playback on loop**  
✅ **Syncs** with an AWS **S3 bucket** for updates  
✅ Moves old videos to **backup storage**  
✅ Logs errors for **remote debugging**  
✅ **Automatically runs on boot** via `systemd`  

---

## **Requirements**
- **Hardware**: Raspberry Pi Zero 2 W (or any compatible Raspberry Pi)
- **Software**:
  - Raspberry Pi OS Lite
  - Python 3
  - VLC Media Player
  - AWS CLI
  - Boto3 (AWS SDK for Python)
  - `systemd` for auto-starting scripts

---

## **Installation**

### **1. Prepare Your Raspberry Pi**
1. **Install Raspberry Pi OS Lite**
   - Download the latest Raspberry Pi OS Lite from the [official website](https://www.raspberrypi.com/software/).
   - Flash it onto an **SD card** using [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
   - Enable SSH during setup with the Raspberry Pi Imager

3. **Boot the Pi and Connect via SSH**
   ```bash
   ssh <username>@<pi-name>.local
   ```

4. **Update the System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

5. **Install Raspberry Pi Connect (OPTIONAL)**
   ```bash
   sudo apt install rpi-connect-lite
   ```

6. **Activate RPi Connect (OPTIONAL)**
   ```bash
   rpi-connect on
   ```

   ```bash
   rpi-connect signin
   ```

   - A sign in link will be generated for you to use.

---

### **2. Set Up AWS S3 Bucket**
1. **Create an S3 Bucket**
   - Go to [AWS S3 Console](https://s3.console.aws.amazon.com/)
   - Click "**Create Bucket**" and configure:
     - **Bucket Name:** Unique name
     - **Region:** Closest to the Raspberry Pi location
     - **Block Public Access:** Enabled
     - **Encryption:** **SSE-S3** for security (optional)

2. **Set Up Folder Structure**
   ```bash
   aws s3api put-object --bucket <bucket_name> --key "<device_name>/video/"
   aws s3api put-object --bucket <bucket_name> --key "<device_name>/backups/"
   ```

3. **Configure IAM Policy for Raspberry Pi**
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

4. **Save AWS Credentials**
   - Generate **Access Keys** and save them for later.

---

### **3. Install Required Software**
```bash
sudo apt install python3 python3-pip vlc awscli -y
pip3 install boto3
```

### **4. Project Directory Setup**
1. **Create Required Directories**
   ```bash
   mkdir -p /home/pi/video
   ```

2. Create Python Files
   ```bash
   sudo nano /home/pi/video/main.py
   ```
   - Copy the script from the repository
   - Hit `CTRL+X` then `y` and then `ENTER` to save the changes
   - Do the same for the setup.py file

3. **Make Python Scripts Executable**
   ```bash
   sudo chmod +x /home/pi/setup.py /home/pi/main.py
   ```

4. **Set Up AWS Credentials**
   ```bash
   aws configure
   ```

---

### **5. Configure and Automate the System**
1. **Run Setup Script**
   ```bash
   python3 /home/pi/setup.py
   ```
   - Generates `config.json` with S3 bucket details.

2. **Test the Main Script**
   ```bash
   python3 /home/pi/main.py
   ```

3. **Create a `systemd` Service**
   ```bash
   sudo nano /etc/systemd/system/video_player.service
   ```
   - Paste the following:
     ```ini
     [Unit]
     Description=Video Player Service
     After=network.target

     [Service]
     ExecStart=/usr/bin/python3 /home/pi/main.py
     Restart=always
     User=pi
     Group=pi

     [Install]
     WantedBy=multi-user.target
     ```

4. **Enable & Start the Service**
   ```bash
   sudo systemctl enable video_player.service
   sudo systemctl start video_player.service
   ```

---

## **Usage**

### **Checking Logs**
```bash
cat /home/pi/video_player.log
```

### **Manually Forcing an Update**
```bash
python3 /home/pi/main.py update
```

### **Restart the Service**
```bash
sudo systemctl restart video_player.service
```

---

## **Testing and Deployment**
1. **Test Locally**
   - Upload a sample video to the **S3 bucket**.
   - Ensure the Pi **downloads** and **plays** it.

2. **Deploy to Clients**
   - Install the Raspberry Pi at the **client’s location**.
   - Verify **internet connectivity** for remote updates.

3. **Remote Maintenance**
   - Use **SSH** or **Raspberry Pi Connect** for debugging.

4. **Exit to CLI**
   - Use a standard keyboard interrupt `CTRL+C` to exit the video loop and manage the OS for its CLI.
   - Restart service by rebooting the Raspberry Pi

---

### 🎉 **Congratulations! Your Raspberry Pi video player is now set up and running.** 🎉
