import webbrowser
import os
import antigravity

# 1. Path to your OMR Frontend
# Using absolute path for reliability
frontend_path = os.path.abspath(r"frontend\index.html")
file_url = f"file:///{frontend_path.replace('\\', '/')}"

# 2. Register Microsoft Edge
# Typical path on Windows 10/11
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

try:
    # Tell Python to use Edge
    webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
    
    print(f"[*] Launching OMR System in Microsoft Edge...")
    print(f"[*] Target: {file_url}")
    
    # 3. Open your OMR application in Edge
    webbrowser.get('edge').open(file_url)
    
    # 4. Success!
    print("[+] Evaluation System is ready.")

except Exception as e:
    print(f"[!] Error launching Edge: {e}")
    # Fallback to default browser if Edge isn't at the expected path
    webbrowser.open(file_url)
