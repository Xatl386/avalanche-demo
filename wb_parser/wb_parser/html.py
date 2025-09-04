from typing import List, Optional
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .api import DEFAULT_HEADERS


def extract_nms_from_html(url: str, session: Optional[requests.Session] = None) -> List[int]:
    sess = session or requests.Session()
    resp = sess.get(url, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    ids: List[int] = []

    # WB embeds product links like /catalog/<nmId>/detail.aspx (may not always be present if JS-rendered)
    for a in soup.select("a[href*='/catalog/'][href*='/detail.aspx']"):
        href = a.get("href", "")
        try:
            parts = href.split("/catalog/")[-1]
            nm_str = parts.split("/")[0]
            nm = int(nm_str)
            ids.append(nm)
        except Exception:
            continue

    # Deduplicate
    ids = sorted(set(ids))
    return ids


def derive_query_from_url(url: str) -> Optional[str]:
    """Best-effort: derive a search query from a brand/category/search URL.
    - /catalog/0/search.aspx?search=iphone -> iphone
    - /brands/xiaomi -> xiaomi
    - /catalog/.../playstation -> playstation
    """
    try:
        parsed = urlparse(url)
        if parsed.query:
            qs = parse_qs(parsed.query)
            if "search" in qs and qs["search"]:
                return qs["search"][0]
        path_parts = [p for p in parsed.path.split("/") if p]
        if not path_parts:
            return None
        # Brand page: /brands/<name>
        if path_parts[0] == "brands" and len(path_parts) >= 2:
            return path_parts[1].replace("-", " ")
        # Category path: use last segment as a query
        return path_parts[-1].replace("-", " ")
    except Exception:
        return None