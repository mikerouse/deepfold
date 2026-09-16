from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import settings
from app.models import Outlet


@dataclass
class WordPressResult:
    dry_run: bool
    ok: bool
    remote_post_id: str | None
    status: str
    detail: str


class WordPressAdapter:
    """WordPress REST adapter.

    Production path (when WP_LIVE=true): Application Password against
    POST /wp-json/wp/v2/posts with status=draft unless publish is explicitly allowed.

    v0 default is a dry-run stub so the desk can be developed without live CMS credentials.
    """

    def create_post(
        self,
        outlet: Outlet,
        *,
        title: str,
        content: str,
        publish: bool,
    ) -> WordPressResult:
        status = "publish" if publish else "draft"
        if not settings.wp_live:
            return WordPressResult(
                dry_run=True,
                ok=True,
                remote_post_id=f"dry-{outlet.slug}",
                status=status,
                detail=(
                    f"Dry-run {status} for {outlet.name} at "
                    f"{outlet.cms_base_url or 'https://example.invalid'}/wp-json/wp/v2/posts"
                ),
            )

        if not outlet.cms_base_url or not settings.wp_username or not settings.wp_application_password:
            return WordPressResult(
                dry_run=False,
                ok=False,
                remote_post_id=None,
                status="failed",
                detail="Missing cms_base_url or WP application password credentials.",
            )

        url = outlet.cms_base_url.rstrip("/") + "/wp-json/wp/v2/posts"
        try:
            response = httpx.post(
                url,
                json={"title": title, "content": content, "status": status},
                auth=(settings.wp_username, settings.wp_application_password),
                timeout=20.0,
            )
            response.raise_for_status()
            data = response.json()
            return WordPressResult(
                dry_run=False,
                ok=True,
                remote_post_id=str(data.get("id")),
                status=data.get("status", status),
                detail=data.get("link", url),
            )
        except Exception as exc:  # noqa: BLE001 — adapter must not crash the desk
            return WordPressResult(
                dry_run=False,
                ok=False,
                remote_post_id=None,
                status="failed",
                detail=str(exc),
            )
