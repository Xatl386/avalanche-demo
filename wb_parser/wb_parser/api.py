import time
from typing import Dict, List, Optional, Tuple

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru,en;q=0.9",
    "Connection": "keep-alive",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}

SEARCH_ENDPOINT = "https://search.wb.ru/exactmatch/ru/common/v5/search"
CARDS_ENDPOINT = "https://card.wb.ru/cards/v2/detail"

DEFAULT_DEST = "-1257786"
DEFAULT_REGIONS = "80,64,38,4,115,83,33,68,70,30,86,15,31,66,110,48,1,22"

class ApiError(Exception):
    pass


def _raise_for_status(resp: requests.Response) -> None:
    if not resp.ok:
        raise ApiError(f"HTTP {resp.status_code}: {resp.text[:200]}")


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=0.6, min=0.5, max=8), reraise=True,
       retry=retry_if_exception_type((requests.RequestException, ApiError)))
def search_products(
    query: str,
    page: int = 1,
    limit: int = 100,
    sort: Optional[str] = None,
    dest: str = DEFAULT_DEST,
    regions: str = DEFAULT_REGIONS,
    shard: Optional[str] = None,
    suppress_empty: bool = True,
    session: Optional[requests.Session] = None,
) -> Dict:
    params = {
        "query": query,
        "resultset": "catalog",
        "page": page,
        "limit": limit,
        "dest": dest,
        "regions": regions,
    }
    if shard:
        params["shard"] = shard
    if sort:
        params["sort"] = sort

    sess = session or requests.Session()
    resp = sess.get(SEARCH_ENDPOINT, params=params, headers=DEFAULT_HEADERS, timeout=20)
    _raise_for_status(resp)
    data = resp.json()
    if suppress_empty and (not data or not data.get("data", {}).get("products")):
        # Some responses are "is_empty"; return normalized empty
        return {"products": [], "total": data.get("data", {}).get("total", 0), "raw": data}
    return {"products": data.get("data", {}).get("products", []), "total": data.get("data", {}).get("total", 0), "raw": data}


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=0.6, min=0.5, max=8), reraise=True,
       retry=retry_if_exception_type((requests.RequestException, ApiError)))
def fetch_product_cards(
    nm_ids: List[int],
    dest: str = DEFAULT_DEST,
    regions: str = DEFAULT_REGIONS,
    session: Optional[requests.Session] = None,
) -> Dict:
    if not nm_ids:
        return {"cards": []}
    params = {
        "nm": ",".join(str(x) for x in nm_ids),
        "dest": dest,
        "regions": regions,
    }
    sess = session or requests.Session()
    resp = sess.get(CARDS_ENDPOINT, params=params, headers=DEFAULT_HEADERS, timeout=20)
    _raise_for_status(resp)
    return resp.json()