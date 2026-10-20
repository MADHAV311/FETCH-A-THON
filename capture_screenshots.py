import urllib.request
import json
import time
import subprocess
import os

BASE_URL = "http://localhost:8080"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = r"D:\PS1\screenshots"

def set_situation_mode(mode):
    url = f"{BASE_URL}/api/situation/mode"
    data = json.dumps({"mode": mode}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"Error setting mode {mode}: {e}")
        return None

def set_view_mode(mode):
    url = f"{BASE_URL}/api/control"
    data = json.dumps({"action": "viewMode", "viewMode": mode}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"Error setting viewMode {mode}: {e}")
        return None

def capture_screenshot(filename, url=BASE_URL, virtual_time=4000):
    filepath = os.path.join(OUTPUT_DIR, filename)
    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        "--window-size=1920,1080",
        f"--virtual-time-budget={virtual_time}",
        f"--screenshot={filepath}",
        url
    ]
    print(f"Capturing: {filename} from {url}...")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"  [OK] Saved {filename} ({size:,} bytes)")
    else:
        print(f"  [FAIL] Could not find {filepath}")

def main():
    print("Capturing analytics and benchmark tabs...")

    # Clear any residual accident
    url = f"{BASE_URL}/api/accident/clear"
    req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except:
        pass

    set_view_mode("SINGLE")
    set_situation_mode("NORMAL")

    # 1. Fixed vs Adaptive Analytics Comparison View
    capture_screenshot("07_fixed_vs_adaptive_analytics.png", url=f"{BASE_URL}/#comparison", virtual_time=3000)

    # 2. Experiments & Automated Benchmark View
    capture_screenshot("08_experiments_benchmarking_suite.png", url=f"{BASE_URL}/#experiments", virtual_time=3000)

    # 3. Clean Main Dashboard
    capture_screenshot("01_trafficflow_main_dashboard.png", url=f"{BASE_URL}/", virtual_time=3000)

    print("Tab captures completed!")

if __name__ == "__main__":
    main()
