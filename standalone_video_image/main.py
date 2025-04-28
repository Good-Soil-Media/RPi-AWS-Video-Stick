import os
import subprocess
import time
import boto3
import json
import logging
import hashlib
import signal
from datetime import datetime
from PIL import Image  # We'll use Pillow for image handling

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
LOCAL_MEDIA_DIR = f"/home/{USERNAME}/media/"
PLAYLIST_FILE = f"/home/{USERNAME}/playlist.json"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Ensure media directory exists
os.makedirs(LOCAL_MEDIA_DIR, exist_ok=True)

# AWS S3 client
def get_s3_client():
    """Return an S3 client instance."""
    return boto3.client("s3")

# Media handling
def is_video_file(filename):
    """Check if the file is a video."""
    return filename.lower().endswith((".mp4", ".mkv", ".avi", ".mov"))

def is_image_file(filename):
    """Check if the file is an image."""
    return filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp"))

def find_media_files():
    """Find all media files in the local directory."""
    media_files = []
    for file in os.listdir(LOCAL_MEDIA_DIR):
        if is_video_file(file) or is_image_file(file):
            media_files.append(os.path.join(LOCAL_MEDIA_DIR, file))
    return media_files

def get_media_type(file_path):
    """Determine if the file is a video or image."""
    if is_video_file(file_path):
        return "video"
    elif is_image_file(file_path):
        return "image"
    return None

def play_video(file_path):
    """Play a video file using VLC in fullscreen and loop mode."""
    logging.info(f"Starting video playback for {file_path}")
    return subprocess.Popen(
        ["cvlc", "--fullscreen", "--loop", "--no-osd", "--no-audio", file_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def display_image(file_path, duration=None):
    """Display an image file using VLC in fullscreen mode."""
    logging.info(f"Displaying image {file_path}")
    
    # If duration is set (for playlist mode), use the slideshow duration
    # Otherwise for single images, just display indefinitely
    if duration:
        return subprocess.Popen(
            ["cvlc", "--fullscreen", "--image-duration", str(duration), "--loop", "--no-osd", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ), duration
    else:
        # For a single image with no duration, display indefinitely
        return subprocess.Popen(
            ["cvlc", "--fullscreen", "--loop", "--no-osd", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ), None

def stop_playback(process):
    """Stop any media playback process."""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

# File integrity check
def calculate_file_hash(file_path):
    """Calculate the MD5 hash of a file."""
    if not os.path.exists(file_path):
        return None
    
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logging.error(f"Error calculating file hash: {e}")
        return None

def verify_file_integrity(file_path, expected_size=None):
    """Verify file integrity by checking if it exists and optionally checking its size."""
    if not os.path.exists(file_path):
        return False
    
    if expected_size and os.path.getsize(file_path) != expected_size:
        return False
    
    return True

# AWS S3 interaction
def check_s3_for_playlist(s3, bucket_name, base_dir):
    """Check S3 for a playlist and multiple media files."""
    media_dir = f"{base_dir}/media/"
    try:
        # Check if there's a playlist.json file
        playlist_key = f"{base_dir}/playlist.json"
        try:
            s3.head_object(Bucket=bucket_name, Key=playlist_key)
            playlist_exists = True
        except Exception:
            playlist_exists = False
            
        # List all media files
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=media_dir)
        if not response or "Contents" not in response:
            logging.warning(f"No files found in directory: {media_dir}")
            return None, playlist_exists, playlist_key

        # Filter out directories and empty files
        files = [
            file for file in response["Contents"]
            if file["Size"] > 0 and not file["Key"].endswith("/") and
            (is_video_file(file["Key"]) or is_image_file(file["Key"]))
        ]
        
        if not files:
            logging.info("No valid media files found.")
            return None, playlist_exists, playlist_key

        # Sort files by LastModified (newest first)
        latest_files = sorted(files, key=lambda x: x["LastModified"], reverse=True)
        
        return latest_files, playlist_exists, playlist_key
    except Exception as e:
        logging.error(f"Error checking S3: {e}")
        return None, False, None

def download_file(s3, bucket_name, s3_key, retry_count=3):
    """Download a file from S3 with retry mechanism and integrity checking."""
    base_filename = os.path.basename(s3_key)
    local_path = os.path.join(LOCAL_MEDIA_DIR, base_filename)
    
    # If the file already exists, append a number to avoid conflicts
    counter = 1
    while os.path.exists(local_path):
        file_name, ext = os.path.splitext(base_filename)
        local_path = os.path.join(LOCAL_MEDIA_DIR, f"{file_name}_{counter}{ext}")
        counter += 1
    
    # Get the expected file size
    try:
        response = s3.head_object(Bucket=bucket_name, Key=s3_key)
        expected_size = response["ContentLength"]
    except Exception as e:
        logging.error(f"Error getting file size: {e}")
        return None
    
    for attempt in range(retry_count):
        try:
            # Set up a signal handler for timeouts
            def timeout_handler(signum, frame):
                raise TimeoutError("Download took too long")
            
            # Set a timeout for the download (30 seconds)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            # Download the file
            s3.download_file(bucket_name, s3_key, local_path)
            
            # Cancel the alarm
            signal.alarm(0)
            
            # Verify file integrity
            if verify_file_integrity(local_path, expected_size):
                logging.info(f"Downloaded file: {local_path}")
                return local_path
            else:
                logging.warning(f"File integrity check failed, retrying ({attempt+1}/{retry_count})")
                if os.path.exists(local_path):
                    os.remove(local_path)
        except Exception as e:
            logging.error(f"Error downloading file (attempt {attempt+1}/{retry_count}): {e}")
            if os.path.exists(local_path):
                os.remove(local_path)
            # If S3 can't find the file, it might have been removed during download
            if "404" in str(e):
                logging.warning("File no longer exists in S3, possibly removed during download")
                break
        
        # Wait before retrying
        time.sleep(2)
    
    return None

def download_playlist(s3, bucket_name, playlist_key):
    """Download the playlist file from S3."""
    local_path = PLAYLIST_FILE
    try:
        s3.download_file(bucket_name, playlist_key, local_path)
        logging.info(f"Downloaded playlist: {local_path}")
        return local_path
    except Exception as e:
        logging.error(f"Error downloading playlist: {e}")
        return None

def download_all_media(s3, bucket_name, file_list):
    """Download all media files in the list."""
    downloaded_files = []
    for file_info in file_list:
        local_path = download_file(s3, bucket_name, file_info["Key"])
        if local_path:
            downloaded_files.append({
                "path": local_path,
                "type": get_media_type(local_path),
                "s3_key": file_info["Key"]
            })
    return downloaded_files

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

# Playlist management
def load_playlist():
    """Load the playlist from the local JSON file."""
    if not os.path.exists(PLAYLIST_FILE):
        return None
    
    try:
        with open(PLAYLIST_FILE, "r") as file:
            playlist = json.load(file)
        return playlist
    except Exception as e:
        logging.error(f"Error loading playlist: {e}")
        return None

def create_default_playlist(media_files):
    """Create a default playlist from available media files."""
    playlist = []
    for i, media_file in enumerate(media_files):
        playlist.append({
            "path": media_file["path"],
            "type": media_file["type"],
            "order": i,
            "duration": 10 if media_file["type"] == "image" else None  # Default 10 seconds for images
        })
    
    # Sort by order
    playlist.sort(key=lambda x: x["order"])
    return playlist

def clean_old_media(current_media_files):
    """Remove old media files that are not in the current playlist."""
    current_paths = [item["path"] for item in current_media_files]
    for file in os.listdir(LOCAL_MEDIA_DIR):
        file_path = os.path.join(LOCAL_MEDIA_DIR, file)
        if file_path not in current_paths and (is_video_file(file) or is_image_file(file)):
            try:
                os.remove(file_path)
                logging.info(f"Deleted old media file: {file_path}")
            except Exception as e:
                logging.error(f"Error deleting old file {file_path}: {e}")

# Main loop
def main():
    """Main loop for playback and S3 monitoring."""
    bucket_name = config["bucket_name"]
    base_dir = config["s3_dir"]
    check_interval = config.get("check_interval", 300)  # Default to 5 minutes
    s3 = get_s3_client()
    
    # Check for existing local media files first
    existing_media = []
    for file_path in find_media_files():
        existing_media.append({
            "path": file_path,
            "type": get_media_type(file_path),
            "s3_key": None  # Local file, no S3 key
        })
    
    current_playlist = None
    current_media_files = existing_media
    current_index = 0
    current_process = None
    
    # Create a default playlist from existing files if available
    if current_media_files:
        current_playlist = create_default_playlist(current_media_files)
        logging.info(f"Created default playlist from {len(current_media_files)} existing local files")
    
    try:
        while True:
            # If no active playback but we have a playlist, start playing
            if current_process is None and current_playlist and len(current_playlist) > 0:
                current_item = current_playlist[current_index]
                if current_item["type"] == "video":
                    current_process = play_video(current_item["path"])
                elif current_item["type"] == "image":
                    # If it's a single image in the playlist, display indefinitely
                    if len(current_playlist) == 1:
                        current_process, _ = display_image(current_item["path"])
                    else:
                        # For images in a multi-item playlist, use the specified duration
                        duration = current_item.get("duration", 10)
                        current_process, _ = display_image(current_item["path"], duration)
                        
                        # Wait for the specified duration
                        time.sleep(duration)
                        
                        # Stop the image display and move to the next item
                        stop_playback(current_process)
                        current_process = None
                        current_index = (current_index + 1) % len(current_playlist)
            
            # Check S3 for updates periodically
            if time.time() % check_interval < 1:  # Only check at intervals
                logging.info("Checking for new media files...")
                try:
                    latest_files, playlist_exists, playlist_key = check_s3_for_playlist(s3, bucket_name, base_dir)
                    
                    update_needed = False
                    
                    # If playlist exists in S3, download it
                    if playlist_exists:
                        playlist_path = download_playlist(s3, bucket_name, playlist_key)
                        if playlist_path:
                            # Move the playlist to backup after successful download
                            move_to_backup(s3, bucket_name, base_dir, playlist_key)
                            update_needed = True
                    
                    # If there are media files in S3, download them
                    if latest_files:
                        new_media_files = download_all_media(s3, bucket_name, latest_files)
                        if new_media_files:
                            # Move all downloaded files to backup
                            for media_file in new_media_files:
                                if media_file["s3_key"]:  # Skip local files with no S3 key
                                    move_to_backup(s3, bucket_name, base_dir, media_file["s3_key"])
                            
                            # Update the current media files
                            current_media_files = new_media_files
                            update_needed = True
                    
                    # If an update is needed, refresh the playlist
                    if update_needed:
                        # Stop the current playback
                        stop_playback(current_process)
                        current_process = None
                        
                        # Load the playlist or create a default one
                        loaded_playlist = load_playlist()
                        if loaded_playlist:
                            # Convert loaded playlist to use local paths
                            file_map = {os.path.basename(item["path"]): item["path"] for item in current_media_files}
                            for item in loaded_playlist:
                                base_name = os.path.basename(item["filename"])
                                if base_name in file_map:
                                    item["path"] = file_map[base_name]
                                    item["type"] = get_media_type(item["path"])
                            
                            # Filter out items that don't have a valid path
                            current_playlist = [item for item in loaded_playlist if "path" in item and os.path.exists(item["path"])]
                        else:
                            current_playlist = create_default_playlist(current_media_files)
                        
                        # Clean up old media files
                        clean_old_media(current_media_files)
                        
                        # Reset the index
                        current_index = 0
                except Exception as e:
                    logging.error(f"Error checking for updates: {e}")
            
            # If we have a video playing, just sleep briefly and continue
            if current_process is not None and current_playlist and current_playlist[current_index]["type"] == "video":
                # Check if the video is still playing
                if current_process.poll() is not None:
                    # Video ended prematurely (shouldn't happen with loop), move to next
                    current_process = None
                    current_index = (current_index + 1) % len(current_playlist)
            
            # If there's no playlist or it's empty, but we have media files, recreate the playlist
            if (not current_playlist or len(current_playlist) == 0) and current_media_files:
                current_playlist = create_default_playlist(current_media_files)
                current_index = 0
            
            # Sleep briefly to prevent CPU hogging
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected. Stopping playback and exiting.")
        stop_playback(current_process)
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