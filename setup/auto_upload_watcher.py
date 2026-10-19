"""
Automated video folder watcher for GitHub upload.

This script runs in the background and automatically uploads new videos
to GitHub Release Vault when they are added to the local folders.

Usage:
    python setup/auto_upload_watcher.py

Press Ctrl+C to stop.
"""
import os
import sys
import time
import glob
import subprocess
from pathlib import Path
from datetime import datetime

RELEASE_TAG = "videos-vault-v1"

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

def upload_single_file(file_path: str, uploaded_set: set):
    """Uploads a single file to GitHub Release Vault."""
    filename = os.path.basename(file_path)
    
    if filename in uploaded_set:
        return False
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Yeni video tespit edildi: {filename}")
    print(f"GitHub'a yükleniyor...")
    
    try:
        result = subprocess.run([
            "gh", "release", "upload", RELEASE_TAG,
            filename, "--clobber", "--dir", os.path.dirname(file_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Başarıyla yüklendi: {filename}")
            return True
        else:
            print(f"❌ Yükleme başarısız: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

def watch_folder(folder: str, profile_name: str):
    """Watches a folder for new videos and uploads them to GitHub."""
    print(f"\n{'='*60}")
    print(f"📁 Klasör izleniyor: {folder}")
    print(f"🎬 Kanal: {profile_name}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(folder):
        print(f"❌ Klasör bulunamadı: {folder}")
        return
    
    uploaded = get_uploaded_files()
    print(f"GitHub'da zaten {len(uploaded)} video var")
    
    # Initial check for any new files
    video_files = glob.glob(os.path.join(folder, "*.mp4"))
    new_files = [f for f in video_files if os.path.basename(f) not in uploaded]
    
    if new_files:
        print(f"\n🔍 Başlangıç kontrolü: {len(new_files)} yeni video bulundu")
        for video_path in sorted(new_files):
            if upload_single_file(video_path, uploaded):
                uploaded.add(os.path.basename(video_path))
                time.sleep(2)  # Small delay between uploads
    else:
        print("✅ Tüm videolar zaten GitHub'da")
    
    print(f"\n⏰ İzleme başladı... (Yeni video ekleyin, otomatik yüklenir)")
    print(f"   Durdurmak için Ctrl+C\n")
    
    # Watch loop
    while True:
        try:
            time.sleep(10)  # Check every 10 seconds
            
            current_files = set(os.path.basename(f) for f in glob.glob(os.path.join(folder, "*.mp4")))
            new_files = current_files - uploaded
            
            if new_files:
                print(f"\n🎉 {len(new_files)} yeni video tespit edildi!")
                for filename in sorted(new_files):
                    file_path = os.path.join(folder, filename)
                    if upload_single_file(file_path, uploaded):
                        uploaded.add(filename)
                        time.sleep(2)
                        
        except KeyboardInterrupt:
            print("\n\n⏹️  İzleme durduruldu.")
            break
        except Exception as e:
            print(f"❌ Hata: {e}")
            time.sleep(5)

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    folders = {
        "animai_studio": os.path.join(root_dir, "Yeni klasör", "Hikaye_ai"),
        "minik_maceralar": os.path.join(root_dir, "Yeni klasör", "Bebek")
    }
    
    print("🚀 Otomatik Video İzleyici Başlatılıyor...")
    print(f"GitHub CLI sürümü: ", end="")
    subprocess.run(["gh", "--version"], capture_output=True)
    
    # Check authentication
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
    except Exception:
        print("❌ GitHub'a giriş yapmamışsınız. Önce 'gh auth login' çalıştırın.")
        return
    
    # Watch both folders
    try:
        # For simplicity, we'll watch both folders in sequence
        # In a real production setup, you might want to run separate processes
        while True:
            print("\n" + "="*60)
            print("🔄 Tüm klasörler kontrol ediliyor...")
            print("="*60)
            
            for profile, folder in folders.items():
                if os.path.exists(folder):
                    uploaded = get_uploaded_files()
                    video_files = glob.glob(os.path.join(folder, "*.mp4"))
                    new_files = [f for f in video_files if os.path.basename(f) not in uploaded]
                    
                    if new_files:
                        print(f"\n📂 {profile}: {len(new_files)} yeni video")
                        for video_path in sorted(new_files):
                            if upload_single_file(video_path, uploaded):
                                time.sleep(2)
                    else:
                        print(f"✅ {profile}: Yeni video yok")
                else:
                    print(f"⚠️  {profile}: Klasör bulunamadı")
            
            print(f"\n⏰ Sonraki kontrol: 30 saniye sonra... (Ctrl+C ile durdur)")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n✅ İzleyici durduruldu.")

if __name__ == "__main__":
    main()
