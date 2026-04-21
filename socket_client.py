"""
Socket API Client
Wraps the Socket.dev REST API v0 for metric collection.
"""

import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SOCKET_API_BASE = "https://api.socket.dev/v0"
DEFAULT_TIMEOUT = 30


class SocketAPIError(Exception):
    """Raised when the Socket API returns an error."""
    pass


class SocketClient:
    def __init__(self, api_token: Optional[str] = None, org_slug: Optional[str] = None):
        self.api_token = api_token or os.environ["SOCKET_API_TOKEN"]
        self.org_slug = org_slug or os.environ["SOCKET_ORG_SLUG"]
        self.session = requests.Session()
        self.session.auth = (self.api_token, "")
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{SOCKET_API_BASE}{path}"
        try:
            resp = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited. Retrying after {retry_after}s")
                time.sleep(retry_after)
                resp = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            raise SocketAPIError(f"API error {resp.status_code} for {url}: {e}") from e
        except requests.RequestException as e:
            raise SocketAPIError(f"Request failed for {url}: {e}") from e

    def get_quota(self) -> dict:
        """Check remaining API quota."""
        return self._get("/quota")

    def get_org_repos(self) -> list:
        """List all repos in the org."""
        data = self._get(f"/orgs/{self.org_slug}/repos")
        return data.get("results", [])

    def get_dependencies(self, page: int = 0, per_page: int = 100) -> dict:
        """Search all dependencies across the org."""
        return self._get(
            "/dependencies/search",
            params={"page": page, "per_page": per_page}
        )

    def get_full_scans(self) -> list:
        """Get full scans for the org."""
        data = self._get(f"/orgs/{self.org_slug}/full-scans")
        return data.get("results", [])

    def get_full_scan_metadata(self, scan_id: str) -> dict:
        """Get metadata for a specific full scan."""
        return self._get(f"/orgs/{self.org_slug}/full-scans/{scan_id}")

    def get_packages_from_scan(self, scan_id: str) -> list:
        """Get all packages and their scores from a full scan."""
        data = self._get(f"/orgs/{self.org_slug}/full-scans/{scan_id}/packages")
        return data.get("results", [])

    def get_alerts(self, per_page: int = 100) -> list:
        """Get recent alerts for the org."""
        data = self._get(
            f"/orgs/{self.org_slug}/alerts",
            params={"per_page": per_page}
        )
        return data.get("results", [])

    def get_org_security_policy(self) -> dict:
        """Get org security policy settings."""
        return self._get(f"/orgs/{self.org_slug}/settings/security-policy")
