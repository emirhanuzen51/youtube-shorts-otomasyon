"""
Automated Watcher & Vault Synchronizer.
Runs in the background. Whenever you drop or create new MP4 videos in:
  - 'Yeni klasör/Hikaye_ai'
  - 'Yeni klasör/Bebek'
It automatically syncs them to the GitHub Cloud Release Vault ('videos-vault-v1').
This ensures that even when your PC is turned off, GitHub Actions in the cloud
can access and publish all your videos without interruption!
"""
import os
import glob
import time
import subprocess

REPO_DIR = r"C:\Users\emirhan\Desktop\youtube"
TAG = "videos-vault-v1"
HIKAYE_DIR = os.path.join(REPO_DIR, "Yeni klasör", "Hikaye_ai")
BEBEK_DIR = os.path.join(REPO_DIR, "Yeni klasör", "Bebek")

def get_remote_assets():
    try:
        res = subprocess.run(
            ["gh", "release", "view", TAG, "--json", "assets", "--jq", ".assets[].name"],
            cwd=REPO_DIR, capture_output=True, text=True
        )
        if res.returncode == 0:
            return set(res.stdout.split())
    except Exception as e:
        print(f"[Watcher] Hata: {e}")
    return set()

def sync_once():
    remote = get_remote_assets()
    all_local = sorted(glob.glob(os.path.join(HIKAYE_DIR, "*.mp4"))) + sorted(glob.glob(os.path.join(BEBEK_DIR, "*.mp4")))
    
    for v in all_local:
        base = os.path.basename(v)
        if base not in remote:
            size_mb = os.path.getsize(v) / (1024 * 1024)
            print(f"[Watcher] Yeni video bulundu: {base} ({size_mb:.1f} MB). GitHub Bulut Kasası'na yükleniyor...")
            cmd = ["gh", "release", "upload", TAG, v, "--clobber"]
            ret = subprocess.run(cmd, cwd=REPO_DIR)
            if ret.returncode == 0:
                print(f"[Watcher] BAŞARILI: {base} buluta aktarıldı!")
                remote.add(base)
            else:
                print(f"[Watcher] Yükleme başarısız oldu, bir sonraki döngüde tekrar denenecek.")

if __name__ == "__main__":
    print("[Watcher] Video klasörleri izleniyor...")
    while True:
        try:
            sync_once()
        except Exception as e:
            print(f"[Watcher] Döngü hatası: {e}")
        time.sleep(120)  # Her 2 dakikada bir klasörü kontrol eder
