"""Separate Mock Consumer Client for MSK-Therapy-OS Interoperability (BRIDGE-01 / BRIDGE-02).

Proves standalone consumer integration on Windows/WSL:
  1. Online Mode: Authenticated read-only Bearer queries against Lab OS API.
  2. Offline Fallback: Validated hashed package extraction when Lab OS is offline.
  3. Tamper Negatives: Fails closed on altered packages or revoked rights.
  4. Privacy Boundaries: Never sends patient data or clinical session state to Lab OS.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
import httpx

from msk_research_lab.bridge.packages import validate_offline_package, TamperedPackageError, PackageRightsError


class ConsumerBridgeError(Exception):
    """Base exception for Therapy consumer bridge errors."""
    pass


class AuthenticationError(ConsumerBridgeError):
    """Raised when Bearer authentication fails (401/403)."""
    pass


class KnowledgeNotFoundError(ConsumerBridgeError):
    """Raised when knowledge point is unreviewed or unpublished (404)."""
    pass


class TherapyResearchClient:
    """Mock client representing MSK-Therapy-OS consuming Lab OS research knowledge."""

    def __init__(
        self,
        *,
        api_base_url: str = "http://127.0.0.1:8091/api/v1",
        bearer_token: str = "dev-insecure-research-token",
        offline_package_dir: Optional[Path] = None,
        force_offline: bool = False,
        client: Optional[httpx.Client] = None,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.offline_package_dir = Path(offline_package_dir) if offline_package_dir else None
        self.force_offline = force_offline
        self._http_client = client or httpx.Client(timeout=3.0)

    def close(self):
        self._http_client.close()

    def get_point_knowledge(self, point_code: str) -> Dict[str, Any]:
        """Retrieve reviewed point knowledge, citations, and contradictions.

        Prefers active online Lab OS service; transparently falls back to local
        cryptographically validated offline package if Lab OS is offline.
        """
        clean_code = point_code.strip()

        # 1. Online attempt if not forced offline
        if not self.force_offline:
            try:
                headers = {"Authorization": f"Bearer {self.bearer_token}"}
                resp = self._http_client.get(
                    f"{self.api_base_url}/knowledge/points/{clean_code}",
                    headers=headers
                )
                if resp.status_code == 200:
                    data = resp.json()
                    data["delivery_channel"] = "ONLINE_LAB_API"
                    return data
                elif resp.status_code in {401, 403}:
                    raise AuthenticationError(f"Therapy client authentication failed: {resp.status_code}")
                elif resp.status_code == 404:
                    detail = resp.json().get("detail", {})
                    raise KnowledgeNotFoundError(f"Point '{clean_code}' unreviewed/unpublished: {detail}")
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError):
                # Lab server offline; proceed to fallback
                pass

        # 2. Offline fallback to local approved package
        if not self.offline_package_dir or not self.offline_package_dir.exists():
            raise ConsumerBridgeError(
                f"Lab OS is offline and no local offline package directory is configured."
            )

        # Cryptographically validate package before reading
        validation = validate_offline_package(self.offline_package_dir)

        # Lookup point inside verified package
        point_file = self.offline_package_dir / "points" / f"{clean_code.lower()}.json"
        if not point_file.exists():
            raise KnowledgeNotFoundError(
                f"Point '{clean_code}' is not included in offline package '{validation['package_id']}'."
            )

        point_data = json.loads(point_file.read_text(encoding="utf-8"))
        point_data["delivery_channel"] = "OFFLINE_HASHED_PACKAGE"
        point_data["package_id"] = validation["package_id"]
        point_data["snapshot_id"] = validation["snapshot_id"]
        return point_data
