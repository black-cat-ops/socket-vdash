"""
Database layer for Socket VDash.
Handles Postgres connections and metric writes.
"""

import logging
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator

import psycopg2
from psycopg2.extras import execute_batch

logger = logging.getLogger(__name__)


def get_connection_params() -> dict:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT", 5432)),
        "dbname": os.environ.get("POSTGRES_DB", "socket_vdash"),
        "user": os.environ.get("POSTGRES_USER", "socket"),
        "password": os.environ.get("POSTGRES_PASSWORD", "changeme"),
    }


@contextmanager
def get_db() -> Generator:
    conn = psycopg2.connect(**get_connection_params())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def write_org_scores(conn, org_slug: str, scores: dict, total_packages: int):
    """Write org-level aggregate scores snapshot."""
    sql = """
        INSERT INTO org_scores (
            collected_at, org_slug,
            avg_overall, avg_supply_chain, avg_vulnerability,
            avg_quality, avg_maintenance, avg_license,
            total_packages
        ) VALUES (
            NOW(), %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    with conn.cursor() as cur:
        cur.execute(sql, (
            org_slug,
            scores.get("overall"),
            scores.get("supplyChain"),
            scores.get("vulnerability"),
            scores.get("quality"),
            scores.get("maintenance"),
            scores.get("license"),
            total_packages,
        ))
    logger.info(f"Wrote org scores: overall={scores.get('overall'):.3f}, packages={total_packages}")


def write_package_scores(conn, org_slug: str, packages: list):
    """Write per-package score snapshots."""
    sql = """
        INSERT INTO package_scores (
            collected_at, org_slug, package_name, package_version, ecosystem,
            score_overall, score_supply_chain, score_vulnerability,
            score_quality, score_maintenance, score_license
        ) VALUES (
            NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    rows = []
    for pkg in packages:
        score = pkg.get("score", {})
        rows.append((
            org_slug,
            pkg.get("name", "unknown"),
            pkg.get("version"),
            pkg.get("type"),
            score.get("overall"),
            score.get("supplyChain"),
            score.get("vulnerability"),
            score.get("quality"),
            score.get("maintenance"),
            score.get("license"),
        ))
    with conn.cursor() as cur:
        execute_batch(cur, sql, rows, page_size=100)
    logger.info(f"Wrote {len(rows)} package scores")


def write_alert_counts(conn, org_slug: str, alert_counts: dict):
    """Write alert counts by severity."""
    sql = """
        INSERT INTO alert_counts (collected_at, org_slug, severity, alert_type, count)
        VALUES (NOW(), %s, %s, %s, %s)
    """
    rows = [
        (org_slug, severity, alert_type, count)
        for (severity, alert_type), count in alert_counts.items()
    ]
    if rows:
        with conn.cursor() as cur:
            execute_batch(cur, sql, rows)
    logger.info(f"Wrote {len(rows)} alert count rows")


def write_cve_findings(conn, org_slug: str, cves: list):
    """Write CVE findings."""
    sql = """
        INSERT INTO cve_findings (
            collected_at, org_slug, package_name,
            cve_id, cvss_score, severity, is_fixable
        ) VALUES (NOW(), %s, %s, %s, %s, %s, %s)
    """
    rows = [
        (
            org_slug,
            cve["package_name"],
            cve["cve_id"],
            cve.get("cvss_score"),
            cve.get("severity"),
            cve.get("is_fixable", False),
        )
        for cve in cves
    ]
    if rows:
        with conn.cursor() as cur:
            execute_batch(cur, sql, rows)
    logger.info(f"Wrote {len(rows)} CVE findings")


def write_dependency_inventory(conn, org_slug: str, inventory: dict):
    """Write dependency inventory snapshot."""
    sql = """
        INSERT INTO dependency_inventory (
            collected_at, org_slug,
            total_direct, total_transitive,
            total_unmaintained, total_deprecated, total_high_risk
        ) VALUES (NOW(), %s, %s, %s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        cur.execute(sql, (
            org_slug,
            inventory.get("total_direct", 0),
            inventory.get("total_transitive", 0),
            inventory.get("total_unmaintained", 0),
            inventory.get("total_deprecated", 0),
            inventory.get("total_high_risk", 0),
        ))
    logger.info(f"Wrote dependency inventory: {inventory}")
