import os
import glob
import subprocess
import time

TAG = "videos-vault-v1"
REPO_DIR = r"C:\Users\emirhan\Desktop\youtube"
hikaye_dir = os.path.join(REPO_DIR, "Yeni klasör", "Hikaye_ai")
bebek_dir = os.path.join(REPO_DIR, "Yeni klasör", "Bebek")

def sync():
    res = subprocess.run(["gh", "release", "view", TAG, "--json", "assets", "--jq", ".assets[].name"], cwd=REPO_DIR, capture_output=True, text=True)
    existing = set(res.stdout.split())
    
    all_videos = sorted(glob.glob(os.path.join(hikaye_dir, "*.mp4"))) + sorted(glob.glob(os.path.join(bebek_dir, "*.mp4")))
    to_upload = [v for v in all_videos if os.path.basename(v) not in existing]
    
    print(f"Toplam dosya: {len(all_videos)} | Zaten bulutta: {len(existing)} | Yüklenecek: {len(to_upload)}")
    
    for idx, v in enumerate(to_upload, 1):
        base = os.path.basename(v)
        size_mb = os.path.getsize(v) / (1024 * 1024)
        print(f"[{idx}/{len(to_upload)}] Buluta Yükleniyor: {base} ({size_mb:.1f} MB)...")
        for attempt in range(1, 4):
            cmd = ["gh", "release", "upload", TAG, v, "--clobber"]
            ret = subprocess.run(cmd, cwd=REPO_DIR)
            if ret.returncode == 0:
                print(f"  -> Başarılı: {base}")
                break
            else:
                print(f"  -> Deneme {attempt} başarısız oldu, 5 saniye sonra tekrar deneniyor...")
                time.sleep(5)
                
    print("\nTAMAMLANDI: Tüm videolar GitHub Bulut Kasası'na aktarıldı!")

if __name__ == "__main__":
    sync()
