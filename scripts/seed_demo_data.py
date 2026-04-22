"""
Seeds Postgres with realistic demo data for dashboard presentation.
Run: python3 scripts/seed_demo_data.py
"""

import os, sys, random
from datetime import datetime, timezone, timedelta
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    port=int(os.environ.get("POSTGRES_PORT", 5432)),
    dbname=os.environ.get("POSTGRES_DB", "socket_vdash"),
    user=os.environ.get("POSTGRES_USER", "socket"),
    password=os.environ.get("POSTGRES_PASSWORD", "socket123"),
)

cur = conn.cursor()
now = datetime.now(timezone.utc)
org = "carma"

print("Seeding org_scores (30 days of trending data)...")
for i in range(30):
    ts = now - timedelta(days=29-i)
    # Scores gradually improving over time
    base = 0.55 + (i * 0.008)
    cur.execute("""
        INSERT INTO org_scores (collected_at, org_slug, avg_overall, avg_supply_chain,
        avg_vulnerability, avg_quality, avg_maintenance, avg_license, total_packages)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (ts, org,
        round(min(base + random.uniform(-0.02, 0.02), 1.0), 3),
        round(min(base - 0.05 + random.uniform(-0.03, 0.03), 1.0), 3),
        round(min(base + 0.10 + random.uniform(-0.02, 0.02), 1.0), 3),
        round(min(base + 0.05 + random.uniform(-0.02, 0.02), 1.0), 3),
        round(min(base - 0.08 + random.uniform(-0.03, 0.03), 1.0), 3),
        round(min(base + 0.15 + random.uniform(-0.01, 0.01), 1.0), 3),
        random.randint(85, 120)
    ))

print("Seeding package_scores...")
packages = [
    ("requests", "2.31.0", "pypi", 0.85, 0.80, 0.90, 0.88, 0.82, 0.95),
    ("numpy", "1.26.0", "pypi", 0.92, 0.91, 0.95, 0.93, 0.90, 0.98),
    ("django", "4.2.0", "pypi", 0.78, 0.72, 0.85, 0.80, 0.75, 0.90),
    ("lodash", "4.17.21", "npm", 0.65, 0.60, 0.70, 0.68, 0.55, 0.88),
    ("axios", "1.6.0", "npm", 0.80, 0.78, 0.85, 0.82, 0.79, 0.92),
    ("cryptography", "41.0.0", "pypi", 0.88, 0.85, 0.92, 0.87, 0.86, 0.95),
    ("left-pad", "1.3.0", "npm", 0.30, 0.25, 0.60, 0.35, 0.20, 0.70),
    ("event-stream", "3.3.4", "npm", 0.15, 0.10, 0.20, 0.18, 0.12, 0.40),
    ("minimist", "1.2.5", "npm", 0.45, 0.40, 0.55, 0.48, 0.35, 0.80),
    ("sqlalchemy", "2.0.0", "pypi", 0.87, 0.84, 0.90, 0.88, 0.85, 0.94),
    ("flask", "3.0.0", "pypi", 0.82, 0.79, 0.88, 0.83, 0.80, 0.92),
    ("express", "4.18.2", "npm", 0.75, 0.70, 0.82, 0.77, 0.72, 0.90),
]
for pkg in packages:
    cur.execute("""
        INSERT INTO package_scores (collected_at, org_slug, package_name, package_version,
        ecosystem, score_overall, score_supply_chain, score_vulnerability,
        score_quality, score_maintenance, score_license)
        VALUES (NOW(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (org, *pkg))

print("Seeding alert_counts (30 days)...")
for i in range(30):
    ts = now - timedelta(days=29-i)
    for severity, base_count in [("critical", 2), ("high", 8), ("medium", 15), ("low", 25)]:
        count = max(0, base_count + random.randint(-2, 2) - int(i * 0.05))
        cur.execute("""
            INSERT INTO alert_counts (collected_at, org_slug, severity, alert_type, count)
            VALUES (%s,%s,%s,%s,%s)
        """, (ts, org, severity, "mixed", count))

print("Seeding cve_findings...")
cves = [
    ("lodash", "CVE-2021-23337", 7.2, "high", False),
    ("minimist", "CVE-2021-44906", 9.8, "critical", True),
    ("event-stream", "CVE-2018-21270", 9.8, "critical", False),
    ("django", "CVE-2023-41164", 7.5, "high", True),
    ("axios", "CVE-2023-45857", 6.5, "medium", True),
]
for cve in cves:
    cur.execute("""
        INSERT INTO cve_findings (collected_at, org_slug, package_name,
        cve_id, cvss_score, severity, is_fixable)
        VALUES (NOW(),%s,%s,%s,%s,%s,%s)
    """, (org, *cve))

print("Seeding dependency_inventory...")
for i in range(30):
    ts = now - timedelta(days=29-i)
    cur.execute("""
        INSERT INTO dependency_inventory (collected_at, org_slug, total_direct,
        total_transitive, total_unmaintained, total_deprecated, total_high_risk)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (ts, org,
        random.randint(28, 35),
        random.randint(75, 95),
        random.randint(3, 7),
        random.randint(1, 4),
        random.randint(2, 6)
    ))

conn.commit()
cur.close()
conn.close()
print("\nDone! Refresh Grafana at http://localhost:3000")
