import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def check_component(name, url, method="GET", payload=None):
    print(f"Checking {name}...")
    try:
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, json=payload, timeout=5)
        
        if resp.status_code == 200:
            print(f"  [OK] {name} is active.")
            return True, resp
        else:
            print(f"  [FAIL] {name} returned status {resp.status_code}")
            return False, resp
    except Exception as e:
        print(f"  [ERROR] {name} unreachable: {e}")
        return False, None

def run_audit():
    print("\n=== SYSTEM AUDIT START ===\n")
    
    # 1. Health Check
    health_ok, _ = check_component("Backend API Health", f"{BASE_URL}/api/health")
    
    # 2. Static Serving
    static_ok, resp = check_component("Frontend Serving (Static)", f"{BASE_URL}/")
    if static_ok and "<!DOCTYPE html>" in resp.text:
        print("  [OK] Frontend is being served correctly.")
    else:
        print("  [FAIL] Frontend serving returned invalid content.")
        static_ok = False

    # 3. Hardware Simulation Endpoint
    # This just starts it, so we check if it accepts the command
    hw_ok, _ = check_component("Hardware Simulation Start", f"{BASE_URL}/api/machine/simulate", "POST", {"enable": True})
    
    # 4. Cleanup Hardware Simulation
    check_component("Hardware Simulation Stop", f"{BASE_URL}/api/machine/simulate", "POST", {"enable": False})

    print("\n=== AUDIT RESULTS ===")
    overall = "PASS" if all([health_ok, static_ok, hw_ok]) else "FAIL"
    print(f"OVERALL SYSTEM STATUS: {overall}")
    print("\n=== SYSTEM AUDIT END ===\n")

if __name__ == "__main__":
    # Wait a moment for server to be ready if it just restarted
    time.sleep(2)
    run_audit()
