import os, json, requests
from dotenv import load_dotenv
load_dotenv()

API_BASE = "https://api.socket.dev/v0"
TOKEN = os.environ.get("SOCKET_API_TOKEN")
ORG_SLUG = os.environ.get("SOCKET_ORG_SLUG")

session = requests.Session()
session.auth = (TOKEN, "")
session.headers.update({"Accept": "application/json"})

r = session.get(f"{API_BASE}/orgs/{ORG_SLUG}/full-scans", timeout=15)
scans = r.json().get("results", [])

print(f"Found {len(scans)} scans:\n")
for s in scans[:5]:
    print(f"  id:         {s['id']}")
    print(f"  repo:       {s.get('repo')}")
    print(f"  branch:     {s.get('branch')}")
    print(f"  scan_state: {s.get('scan_state')}")
    print(f"  created_at: {s.get('created_at')}")
    print(f"  all keys:   {list(s.keys())}")
    print()
