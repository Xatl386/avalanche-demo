import csv
import json
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from dateutil.tz import tzlocal


def now_local_str(fmt: str = "%Y-%m-%d %H:%M") -> str:
    return datetime.now(tzlocal()).strftime(fmt)


def write_csv(path: str, rows: Iterable[List[Any]], header: Optional[List[str]] = None) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        for row in rows:
            writer.writerow(row)


def write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_product_summary(p: Dict) -> Dict[str, Any]:
    # For search API products list
    return {
        "nmId": p.get("id") or p.get("nmId"),
        "name": p.get("name"),
        "brand": p.get("brand"),
        "price": p.get("salePriceU", 0) // 100 if p.get("salePriceU") else None,
        "oldPrice": p.get("priceU", 0) // 100 if p.get("priceU") else None,
        "rating": p.get("rating"),
        "feedbacks": p.get("feedbacks"),
        "link": f"https://www.wildberries.ru/catalog/{p.get('id') or p.get('nmId')}/detail.aspx",
        "pics": p.get("pics")}  # count


def normalize_card(card: Dict) -> Dict[str, Any]:
    # For card API details
    prices = (card.get("sizes") or [{}])[0].get("price", {}) if card.get("sizes") else {}
    colors = [c.get("name") for c in (card.get("colors") or []) if isinstance(c, dict)]
    sizes = [s.get("name") for s in (card.get("sizes") or []) if isinstance(s, dict)]
    return {
        "nmId": card.get("id") or card.get("nmId"),
        "name": card.get("name"),
        "brand": card.get("brand"),
        "salePrice": prices.get("total") // 100 if prices.get("total") else None,
        "basicPrice": prices.get("basic") // 100 if prices.get("basic") else None,
        "rating": card.get("rating"),
        "feedbacks": card.get("feedbacks"),
        "colors": colors,
        "sizes": sizes,
        "pics": card.get("pics")}  # count