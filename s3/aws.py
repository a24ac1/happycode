import argparse
import requests
import sys
import signal
import threading
import os
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

session = requests.Session()
MAX_THREADS = 1000
OUTPUT_DIR = "output"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def setup_signals():
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTSTP'):
        signal.signal(signal.SIGTSTP, signal.default_int_handler)

def signal_handler(sig, frame):
    print(f"\n\n[!] Ctrl+C terdeteksi! Menghentikan skrip...")
    sys.exit(0)

def check_bucket(bucket_name):
    bucket_name = bucket_name.strip()
    if not bucket_name: return None
        
    base_url = f"http://{bucket_name}.s3.amazonaws.com"
    try:
        response = session.get(f"{base_url}/", timeout=3)
        
        if response.status_code == 200:
            env_url = f"{base_url}/.env"
            env_check = session.get(env_url, timeout=3)
            
            if env_check.status_code == 200:
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                filename = os.path.join(OUTPUT_DIR, f"env-{random_suffix}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"Bucket: {bucket_name}\nURL: {env_url}\n\n{env_check.text}")
                return f"\033[92m[!] PUBLIC  | {bucket_name} | .env: DITEMUKAN (Saved to {filename})\033[0m"
            
            return f"\033[92m[+] PUBLIC  | {bucket_name} | .env: tidak ada\033[0m"
            
        elif response.status_code == 403:
            return f"[-] PRIVATE | {bucket_name}"
        
        elif response.status_code == 404:
            return f"[x] NOT FOUND | {bucket_name}"
        
        else:
            return f"[?] UNKNOWN ({response.status_code}) | {bucket_name}"
            
    except Exception:
        return f"[!] ERROR   | {bucket_name}"

def main():
    setup_signals()
    parser = argparse.ArgumentParser(description="S3 Bucket Audit - Print All")
    parser.add_argument("-l", "--list", required=True, help="Path ke file list bucket")
    args = parser.parse_args()

    try:
        with open(args.list, 'r') as file:
            buckets = [line.strip() for line in file if line.strip()]
        
        print(f"[*] Scanning {len(buckets)} bucket...")
        print("-" * 70)

        with tqdm(total=len(buckets), unit="bucket") as pbar:
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {executor.submit(check_bucket, b): b for b in buckets}
                for future in as_completed(futures):
                    result = future.result()
                    # tqdm.write memastikan output tidak merusak baris progress bar
                    if result:
                        tqdm.write(result)
                    pbar.update(1)

    except Exception as e:
        print(f"\n[!] Error: {e}")

if __name__ == "__main__":
    main()