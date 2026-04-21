"""
Metrics processor.
Fetches data from Socket API and transforms it into DB-ready metrics.
"""

import logging
from collections import defaultdict
from typing import Optional

from .socket_client import SocketClient, SocketAPIError

logger = logging.getLogger(__name__)

# Severity mapping for Socket alert types
SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "middle": "medium",
    "low": "low",
    "none": "low",
}

# Alert types that indicate high-risk packages
HIGH_RISK_ALERT_TYPES = {
    "malware", "criticalCVE", "cve", "installScripts",
    "obfuscatedFile", "obfuscatedRequire", "gptMalware",
}

# Alert types for unmaintained/deprecated packages
MAINTENANCE_ALERT_TYPES = {
    "unmaintained", "deprecated", "unpublished", "missingTarball",
}


def collect_metrics(client: SocketClient) -> Optional[dict]:
    """
    Main collection run. Fetches all metrics from Socket API.
    Returns a dict of processed metrics ready to write to DB.
    """
    logger.info(f"Starting collection for org: {client.org_slug}")
    metrics = {
        "org_slug": client.org_slug,
        "packages": [],
        "org_scores": {},
        "alert_counts": defaultdict(int),
        "cve_findings": [],
        "dependency_inventory": {
            "total_direct": 0,
            "total_transitive": 0,
            "total_unmaintained": 0,
            "total_deprecated": 0,
            "total_high_risk": 0,
        },
    }

    # ── 1. Get latest full scan ─────────────────────────────────────────────
    try:
        scans = client.get_full_scans()
        if not scans:
            logger.warning("No full scans found. Is a repo connected to Socket?")
            return _collect_from_dependencies(client, metrics)

        # Use the most recent scan
        latest_scan = scans[0]
        scan_id = latest_scan.get("id")
        logger.info(f"Using scan: {scan_id}")

        packages = client.get_packages_from_scan(scan_id)
        metrics["packages"] = packages

    except SocketAPIError as e:
        logger.warning(f"Full scan fetch failed: {e}. Falling back to dependency search.")
        return _collect_from_dependencies(client, metrics)

    # ── 2. Process package scores ───────────────────────────────────────────
    score_totals = defaultdict(float)
    score_counts = defaultdict(int)
    direct_count = 0
    transitive_count = 0

    for pkg in packages:
        score = pkg.get("score", {})
        alerts = pkg.get("alerts", [])
        is_direct = pkg.get("direct", False)

        if is_direct:
            direct_count += 1
        else:
            transitive_count += 1

        # Aggregate scores
        for key in ["overall", "supplyChain", "vulnerability", "quality", "maintenance", "license"]:
            val = score.get(key)
            if val is not None:
                score_totals[key] += val
                score_counts[key] += 1

        # Process alerts
        for alert in alerts:
            alert_type = alert.get("type", "unknown")
            severity = SEVERITY_MAP.get(alert.get("severity", "low"), "low")
            metrics["alert_counts"][(severity, alert_type)] += 1

            # Check for CVEs
            if alert_type in ("criticalCVE", "cve", "mediumCVE", "mildCVE"):
                props = alert.get("props", {})
                cve_id = props.get("cveId")
                if cve_id:
                    metrics["cve_findings"].append({
                        "package_name": pkg.get("name", "unknown"),
                        "cve_id": cve_id,
                        "cvss_score": props.get("cvss", {}).get("score"),
                        "severity": props.get("severity", severity),
                        "is_fixable": bool(props.get("firstPatchedVersionIdentifier")),
                    })

            # Classify risk
            if alert_type in HIGH_RISK_ALERT_TYPES:
                metrics["dependency_inventory"]["total_high_risk"] += 1
            if alert_type in MAINTENANCE_ALERT_TYPES:
                if alert_type == "deprecated":
                    metrics["dependency_inventory"]["total_deprecated"] += 1
                else:
                    metrics["dependency_inventory"]["total_unmaintained"] += 1

    # Compute averages
    metrics["org_scores"] = {
        key: (score_totals[key] / score_counts[key]) if score_counts[key] > 0 else None
        for key in ["overall", "supplyChain", "vulnerability", "quality", "maintenance", "license"]
    }

    metrics["dependency_inventory"]["total_direct"] = direct_count
    metrics["dependency_inventory"]["total_transitive"] = transitive_count

    logger.info(
        f"Collected {len(packages)} packages, "
        f"{len(metrics['cve_findings'])} CVEs, "
        f"{sum(metrics['alert_counts'].values())} alerts"
    )
    return metrics


def _collect_from_dependencies(client: SocketClient, metrics: dict) -> dict:
    """
    Fallback: collect from dependency search endpoint when no scans exist.
    Useful for orgs that haven't connected a repo yet.
    """
    logger.info("Collecting from dependency search endpoint (fallback mode)")
    try:
        data = client.get_dependencies()
        results = data.get("results", [])
        logger.info(f"Found {len(results)} dependencies via search")

        # Minimal processing — scores not available in this endpoint
        metrics["dependency_inventory"]["total_direct"] = len(results)
        metrics["org_scores"] = {
            k: None for k in ["overall", "supplyChain", "vulnerability", "quality", "maintenance", "license"]
        }
    except SocketAPIError as e:
        logger.error(f"Dependency search also failed: {e}")

    return metrics
