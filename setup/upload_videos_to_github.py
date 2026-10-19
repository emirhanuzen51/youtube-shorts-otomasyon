"""
Uploads local videos to GitHub Release Vault for automated YouTube upload.

This script helps you upload videos from your local folders to GitHub Releases,
so they can be automatically uploaded to YouTube even when your computer is off.

Usage:
    python setup/upload_videos_to_github.py animai_studio
    python setup/upload_videos_to_github.py minik_maceralar
"""
import os
import sys
import glob
import subprocess
from pathlib import Path

# GitHub Release tag for video storage
RELEASE_TAG = "videos-vault-v1"

def upload_to_github_release(file_path: str, profile: str):
    """Uploads a single video file to GitHub Release Vault."""
    filename = os.path.basename(file_path)
    print(f"Uploading {filename} to GitHub Release Vault...")
    
    # Check if release exists, create if not
    try:
        result = subprocess.run(
            ["gh", "release", "view", RELEASE_TAG],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Release {RELEASE_TAG} not found, creating...")
            subprocess.run([
                "gh", "release", "create", RELEASE_TAG,
                "--title", "Video Vault",
                "--notes", "Automated video storage for YouTube upload automation"
            ], check=True)
    except Exception as e:
        print(f"Error checking/creating release: {e}")
        return False
    
    # Upload the file
    try:
        result = subprocess.run([
            "gh", "release", "upload", RELEASE_TAG,
            filename, "--clobber", "--dir", os.path.dirname(file_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully uploaded: {filename}")
            return True
        else:
            print(f"❌ Upload failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def get_uploaded_files():
    """Returns list of files already in GitHub Release Vault."""
    try:
        result = subprocess.run(
            ["gh", "release", "view", RELEASE_TAG, "--json", "assets", "--jq", ".assets[].name"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
    except Exception:
        pass
    return set()

def upload_all_videos(profile: str):
    """Uploads all videos from local folder to GitHub."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Determine folder based on profile
    if profile == "animai_studio":
        folder = os.path.join(root_dir, "Yeni klasör", "Hikaye_ai")
    elif profile == "minik_maceralar":
        folder = os.path.join(root_dir, "Yeni klasör", "Bebek")
    else:
        print(f"Unknown profile: {profile}")
        return
    
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return
    
    # Get all MP4 files
    video_files = glob.glob(os.path.join(folder, "*.mp4"))
    
    if not video_files:
        print(f"❌ No MP4 files found in: {folder}")
        return
    
    print(f"\nFound {len(video_files)} video(s) in {folder}")
    
    # Get already uploaded files
    uploaded = get_uploaded_files()
    print(f"Already uploaded: {len(uploaded)} files")
    
    # Upload new files
    new_uploads = 0
    for video_path in sorted(video_files):
        filename = os.path.basename(video_path)
        
        if filename in uploaded:
            print(f"⏭️  Skipping (already uploaded): {filename}")
            continue
        
        if upload_to_github_release(video_path, profile):
            new_uploads += 1
    
    print(f"\n✅ Upload complete! {new_uploads} new file(s) uploaded to GitHub.")
    print(f"Total files in vault: {len(uploaded) + new_uploads}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_videos_to_github.py <animai_studio | minik_maceralar>")
        sys.exit(1)
    
    profile = sys.argv[1].strip().lower()
    
    # Check if gh CLI is installed
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except Exception:
        print("❌ GitHub CLI (gh) not found. Please install it first:")
        print("   - Download from: https://cli.github.com/")
        print("   - Or run: winget install GitHub.cli")
        sys.exit(1)
    
    # Check if authenticated
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
    except Exception:
        print("❌ Not authenticated with GitHub. Please run: gh auth login")
        sys.exit(1)
    
    upload_all_videos(profile)
