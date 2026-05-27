import requests
import gzip
import shutil
import os
import sys
import time

# Add parent directory to sys.path to allow importing config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def download_conceptnet(max_retries=10, retry_delay=5):
    url = config.CONCEPTNET_DOWNLOAD_URL
    target_gz = config.CONCEPTNET_CSV_PATH + ".gz"
    target_csv = config.CONCEPTNET_CSV_PATH

    if os.path.exists(target_csv):
        print(f"ConceptNet CSV already exists at {target_csv}")
        return

    os.makedirs(os.path.dirname(target_csv), exist_ok=True)

    print(f"Downloading ConceptNet from {url}...")

    retries = 0
    while retries < max_retries:
        try:
            downloaded = 0
            if os.path.exists(target_gz):
                downloaded = os.path.getsize(target_gz)

            headers = {}
            if downloaded > 0:
                headers['Range'] = f'bytes={downloaded}-'
                print(f"Resuming download from {downloaded/1024/1024:.2f}MB...")

            mode = 'ab' if downloaded > 0 else 'wb'

            with requests.get(url, stream=True, headers=headers, timeout=30) as r:
                # If Range request is not supported, restart from zero
                if r.status_code == 416: # Range not satisfiable
                     print("Range not satisfiable, restarting...")
                     os.remove(target_gz)
                     downloaded = 0
                     mode = 'wb'
                     r = requests.get(url, stream=True, timeout=30)

                # Handle non-206 (Partial Content) if we sent a Range header
                if headers and r.status_code != 206:
                     print("Server did not support Range, restarting...")
                     downloaded = 0
                     mode = 'wb'

                r.raise_for_status()

                total_size = int(r.headers.get('content-length', 0)) + downloaded

                with open(target_gz, mode) as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                done = int(50 * downloaded / total_size)
                                sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}MB / {total_size/1024/1024:.2f}MB")
                                sys.stdout.flush()

            print("\nDownload complete.")
            break # Success

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            retries += 1
            print(f"\nConnection error: {e}. Retry {retries}/{max_retries} in {retry_delay}s...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            raise
    else:
        print("\nMax retries reached. Download failed.")
        return

    print(f"Decompressing to {target_csv}...")
    try:
        with gzip.open(target_gz, 'rb') as f_in:
            with open(target_csv, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print("Decompression complete.")
        os.remove(target_gz)
    except Exception as e:
        print(f"Decompression failed: {e}")
        # Keep gz for possible manual recovery

if __name__ == "__main__":
    download_conceptnet()
