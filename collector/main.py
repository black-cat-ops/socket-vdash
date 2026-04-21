"""
Socket VDash Collector — Main Entrypoint
Runs on a schedule, collecting Socket API metrics and writing to Postgres.
"""

import logging
import os
import sys
import time

import schedule
from dotenv import load_dotenv

from .db import (
    get_db,
    write_alert_counts,
    write_cve_findings,
    write_dependency_inventory,
    write_org_scores,
    write_package_scores,
)
from .metrics import collect_metrics
from .socket_client import SocketClient, SocketAPIError

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_collection():
    """Single collection run — fetch metrics and write to DB."""
    logger.info("═" * 50)
    logger.info("Starting Socket VDash collection run")

    try:
        client = SocketClient()
        metrics = collect_metrics(client)

        if not metrics:
            logger.error("No metrics returned. Skipping DB write.")
            return

        with get_db() as conn:
            # Write org-level scores if we have them
            if any(v is not None for v in metrics["org_scores"].values()):
                write_org_scores(
                    conn,
                    metrics["org_slug"],
                    metrics["org_scores"],
                    len(metrics["packages"]),
                )

            # Write per-package scores
            if metrics["packages"]:
                write_package_scores(conn, metrics["org_slug"], metrics["packages"])

            # Write alert counts
            if metrics["alert_counts"]:
                write_alert_counts(conn, metrics["org_slug"], metrics["alert_counts"])

            # Write CVE findings
            if metrics["cve_findings"]:
                write_cve_findings(conn, metrics["org_slug"], metrics["cve_findings"])

            # Write dependency inventory
            write_dependency_inventory(
                conn, metrics["org_slug"], metrics["dependency_inventory"]
            )

        logger.info("Collection run complete ✓")

    except SocketAPIError as e:
        logger.error(f"Socket API error during collection: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during collection: {e}")


def main():
    """Main entrypoint — runs once immediately, then on a schedule."""
    interval = int(os.environ.get("COLLECT_INTERVAL_MINUTES", 60))

    logger.info("Socket VDash Collector starting up")
    logger.info(f"Org: {os.environ.get('SOCKET_ORG_SLUG', 'NOT SET')}")
    logger.info(f"Collection interval: {interval} minutes")

    # Validate required env vars
    required = ["SOCKET_API_TOKEN", "SOCKET_ORG_SLUG"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        sys.exit(1)

    # Run immediately on startup
    run_collection()

    # Then schedule recurring runs
    schedule.every(interval).minutes.do(run_collection)
    logger.info(f"Scheduled collection every {interval} minutes. Running...")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
