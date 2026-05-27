import requests
import gzip
import shutil
import os
import sys

# Add parent directory to sys.path to allow importing config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def download_conceptnet():
    url = config.CONCEPTNET_DOWNLOAD_URL
    target_gz = config.CONCEPTNET_CSV_PATH + ".gz"
    target_csv = config.CONCEPTNET_CSV_PATH

    if os.path.exists(target_csv):
        print(f"ConceptNet CSV already exists at {target_csv}")
        return

    os.makedirs(os.path.dirname(target_csv), exist_ok=True)

    print(f"Downloading ConceptNet from {url}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(target_gz, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    done = int(50 * downloaded / total_size)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}MB")
                    sys.stdout.flush()
    print("\nDownload complete.")

    print(f"Decompressing to {target_csv}...")
    with gzip.open(target_gz, 'rb') as f_in:
        with open(target_csv, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Decompression complete.")
    os.remove(target_gz)

if __name__ == "__main__":
    download_conceptnet()
