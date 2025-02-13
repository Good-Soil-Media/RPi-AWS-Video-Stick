import os
import subprocess
import time
import boto3
import json
import logging
from datetime import datetime

CONFIG_FILE = os.path.expanduser("~/.config/video_player/config.json")

# Load configuration
def load_config():
    """Load configuration from config.json."""
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise

config = load_config()
USERNAME = config["username"]
LOG_FILE = f"/home/{USERNAME}/video_player.log"
LOCAL_VIDEO_DIR = f"/home/{USERNAME}/video/"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# AWS S3 client
def get_s3_client():
    """Return an S3 client instance."""
    return boto3.client("s3")

# Video handling
def find_video():
    """Find the first video file in the local directory."""
    for file in os.listdir(LOCAL_VIDEO_DIR):
        if file.lower().endswith((".mp4", ".mkv", ".avi", ".mov")):
            return os.path.join(LOCAL_VIDEO_DIR, file)
    return None

def play_video(file_path):
    """Play a video file using VLC in fullscreen and loop mode."""
    logging.info(f"Starting playback for {file_path}")
    return subprocess.Popen(["cvlc", "--fullscreen", "--loop", "--no-osd", "--no-audio", file_path])

def stop_video(player_process):
    """Stop the VLC player process."""
    if player_process:
        player_process.terminate()
        player_process.wait()

# AWS S3 interaction
def check_s3(s3, bucket_name, base_dir):
    """Check the S3 video directory for new video files."""
    video_dir = f"{base_dir}/video/"
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=video_dir)
        if not response or "Contents" not in response:
            logging.warning(f"No files found in directory: {video_dir}. Response: {response}")
            return None

        # Filter out directories and empty files
        files = [
            file for file in response["Contents"]
            if file["Size"] > 0 and not file["Key"].endswith("/")
        ]
        if not files:
            logging.info("No valid video files found.")
            return None

        # Return the latest file by LastModified
        return sorted(files, key=lambda x: x["LastModified"], reverse=True)[0]["Key"]
    except Exception as e:
        logging.error(f"Error checking S3: {e}")
        return None

def download_file(s3, bucket_name, s3_key):
    """Download the file from S3."""
    try:
        local_path = os.path.join(LOCAL_VIDEO_DIR, os.path.basename(s3_key))
        s3.download_file(bucket_name, s3_key, local_path)
        logging.info(f"Downloaded file: {local_path}")
        return local_path
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return None

def move_to_backup(s3, bucket_name, base_dir, s3_key):
    """Move the file to the backups directory in S3 with a timestamp."""
    backups_dir = f"{base_dir}/backups/"
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_key = f"{backups_dir}{timestamp}_{os.path.basename(s3_key)}"
        s3.copy_object(Bucket=bucket_name, CopySource=f"{bucket_name}/{s3_key}", Key=backup_key)
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        logging.info(f"Moved file to backup: {backup_key}")
    except Exception as e:
        logging.error(f"Error moving file to backup: {e}")

# Main loop
def main():
    """Main loop for playback and S3 monitoring."""
    bucket_name = config["bucket_name"]
    base_dir = config["s3_dir"]
    s3 = get_s3_client()

    current_video = find_video()
    player = None
    if current_video:
        player = play_video(current_video)

    try:
        while True:
            time.sleep(300)  # Check every 60 seconds
            logging.info("Checking for new video files...")

            new_file = check_s3(s3, bucket_name, base_dir)
            if new_file:
                logging.info(f"New file found: {new_file}")
                # Download the new file while keeping the old video playing
                new_local_file = download_file(s3, bucket_name, new_file)
                if new_local_file:
                    # Move the new file to backup after successful download
                    move_to_backup(s3, bucket_name, base_dir, new_file)

                    # Transition playback to the new video
                    stop_video(player)  # Stop the old video playback
                    player = play_video(new_local_file)  # Start playing the new video

                    # Delete the old video after playback has transitioned
                    if current_video and os.path.exists(current_video):
                        os.remove(current_video)
                        logging.info(f"Deleted old video: {current_video}")

                    # Update current_video to the new file
                    current_video = new_local_file
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected. Stopping video playback and exiting.")
        stop_video(player)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        logging.info("Exiting program.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        from setup import setup
        setup()
    elif len(sys.argv) > 1 and sys.argv[1] == "update":
        main()
    else:
        try:
            main()
        except Exception as e:
            logging.error(f"Fatal error: {e}")