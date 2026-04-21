"""
Socket API Client - validated 2026-04-21
Key: package data streams as NDJSON from full scan endpoint.
"""

import json
import logging
import os
import time
from typing import Generator, Optional

import requests

logger = logging.getLogger(__name__)
SOCKET_API_BASE = "https://api.socket.dev/v0"
DEFAULT_TIMEOUT = 60

class SocketAPIError(Exception):
    pass

class SocketClient:
    def __init__(self, api_token=None, org_slug=None):
        self.api_token = api_token or os.environ["SOCKET_API_TOKEN"]
        self.org_slug = org_slug or os.environ["SOCKET_ORG_SLUG"]
        self.session = requests.Session()
        self.session.auth = (self.api_token, "")
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, path, params=None, stream=False):
        url = f"{SOCKET_API_BASE}{path}"
        resp = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT, stream=stream)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited. Retrying after {retry_after}s")
            time.sleep(retry_after)
            resp = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT, stream=stream)
        if not stream:
            resp.raise_for_status()
        return resp

    def get_quota(self):
        return self._get("/quota").json()

    def get_org_repos(self):
        return self._get(f"/orgs/{self.org_slug}/repos").json().get("results", [])

    def get_full_scans(self, repo=None, branch=None, limit=10):
        params = {"limit": limit}
        if repo: params["repo"] = repo
        if branch: params["branch"] = branch
        return self._get(f"/orgs/{self.org_slug}/full-scans", params=params).json().get("results", [])

    def stream_full_scan(self, scan_id) -> Generator[dict, None, None]:
        """Stream SBOM artifacts as NDJSON — this is how you get package scores/alerts."""
        url = f"{SOCKET_API_BASE}/orgs/{self.org_slugfull-scans/{scan_id}"
        resp = self.session.get(url, timeout=DEFAULT_TIMEOUT, stream=True)
        resp.raise_for_status()
        count = 0
        for line in resp.iter_lines():
            if line:
                try:
                    yield json.loads(line)
                    count += 1
                except json.JSONDecodeError as e:
                    logger.warning(f"NDJSON parse error: {e}")
        logger.info(f"Streamed {count} artifacts from scan {scan_id}")

    def get_org_security_policy(self):
        return self._get(f"/orgs/{self.org_slug}/settings/security-policy").json()
