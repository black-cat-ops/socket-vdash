import os, time, requests
from dotenv import load_dotenv
load_dotenv()

API_BASE = "https://api.socket.dev/v0"
TOKEN = os.environ.get("SOCKET_API_TOKEN")
ORG_SLUG = os.environ.get("SOCKET_ORG_SLUG")

session = requests.Session()
session.auth = (TOKEN, "")
session.headers.update({"Accept": "application/json"})

scan_id = "c9c3c40a-324d-475d-ac21-22a901f0deb6"

for i in range(10):
    r = session.get(f"{API_BASE}/orgs/{ORG_SLUG}/full-scans", timeout=15)
    scans = {s["id"]: s for s in r.json().get("results", [])}
    state = scans.get(scan_id, {}).get("scan_state", "not found")
    print(f"[{i+1}] scan_state: {state}")
    if state not in ("resolve", "pending"):
        print("State changed — ready to stream!")
        break
    time.sleep(15)
