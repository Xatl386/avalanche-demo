import argparse
import math
from typing import Any, Dict, Iterable, List, Optional

import requests
from tqdm import tqdm

from .api import search_products, fetch_product_cards
from .html import extract_nms_from_html, derive_query_from_url
from .io_util import now_local_str, write_csv, write_json, normalize_product_summary, normalize_card


def iter_search(query: str, pages: int, limit: int, sort: Optional[str], dest: str, regions: str) -> Iterable[Dict[str, Any]]:
    sess = requests.Session()
    for page in range(1, pages + 1):
        result = search_products(query=query, page=page, limit=limit, sort=sort, dest=dest, regions=regions, session=sess)
        for p in result.get("products", []):
            yield p
        if not result.get("products"):
            break


def chunked(lst: List[Any], size: int) -> Iterable[List[Any]]:
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def resolve_cards(nm_ids: List[int], dest: str, regions: str) -> List[Dict[str, Any]]:
    sess = requests.Session()
    cards: List[Dict[str, Any]] = []
    for batch in tqdm(list(chunked(nm_ids, 100)), desc="cards", unit="batch"):
        data = fetch_product_cards(batch, dest=dest, regions=regions, session=sess)
        for grp in data.get("data", {}).get("products", []):
            if isinstance(grp, dict) and grp.get("id"):
                cards.append(grp)
            elif isinstance(grp, list):
                cards.extend(x for x in grp if isinstance(x, dict))
    return cards


def to_rows(products: List[Dict[str, Any]], include_date: bool = True) -> List[List[Any]]:
    rows: List[List[Any]] = []
    date_str = now_local_str()
    for p in products:
        n = normalize_product_summary(p)
        row = [n.get("link"), n.get("name"), n.get("price"), n.get("oldPrice"), n.get("rating"), n.get("feedbacks")]
        if include_date:
            row = [date_str] + row
        rows.append(row)
    return rows


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Wildberries parser CLI")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--query", help="Ключевые слова для поиска")
    g.add_argument("--url", help="Ссылка на бренд/категорию на wildberries.ru")

    parser.add_argument("--pages", type=int, default=3, help="Число страниц пагинации для поиска")
    parser.add_argument("--limit", type=int, default=100, help="Лимит товаров на страницу (поиск)")
    parser.add_argument("--sort", help="Параметр сортировки (если доступно)")

    parser.add_argument("--dest", default="-1257786", help="dest параметр для регионов")
    parser.add_argument("--regions", default="80,64,38,4,115,83,33,68,70,30,86,15,31,66,110,48,1,22", help="regions список")

    parser.add_argument("--csv", help="Путь для CSV вывода")
    parser.add_argument("--json", help="Путь для JSON вывода")
    parser.add_argument("--no-date", dest="no_date", action="store_true", help="Не добавлять дату в CSV")

    args = parser.parse_args(argv)

    products: List[Dict[str, Any]] = []
    cards: List[Dict[str, Any]] = []

    if args.query:
        for p in tqdm(iter_search(args.query, args.pages, args.limit, args.sort, args.dest, args.regions), total=args.pages, desc="search pages"):
            products.append(p)
    else:
        # Try HTML ids; on failure fallback to derived query
        nm_ids: List[int] = []
        try:
            nm_ids = extract_nms_from_html(args.url)
        except Exception:
            nm_ids = []
        if nm_ids:
            cards = resolve_cards(nm_ids, dest=args.dest, regions=args.regions)
        else:
            q = derive_query_from_url(args.url)
            if not q:
                print("Не удалось извлечь товары со страницы и сформировать запрос.")
                return 2
            for p in tqdm(iter_search(q, args.pages, args.limit, args.sort, args.dest, args.regions), total=args.pages, desc="search pages"):
                products.append(p)

    # Output
    if args.csv:
        if args.query or products:
            header = ["Дата", "Ссылка на товар", "Название товара", "Цена", "Старая цена", "Рейтинг", "Количество отзывов"]
            rows = to_rows(products, include_date=not args.no_date)
            if args.no_date:
                header = header[1:]
            write_csv(args.csv, rows, header=header)
        else:
            out_rows: List[List[Any]] = []
            date_str = now_local_str()
            for c in cards:
                n = normalize_card(c)
                row = [n.get("nmId"), n.get("name"), n.get("brand"), n.get("salePrice"), n.get("basicPrice"), ", ".join(n.get("colors") or []), ", ".join(n.get("sizes") or [])]
                if not args.no_date:
                    row = [date_str] + row
                out_rows.append(row)
            header = ["Дата", "nmId", "Название", "Бренд", "Цена", "Базовая цена", "Цвета", "Размеры"]
            if args.no_date:
                header = header[1:]
            write_csv(args.csv, out_rows, header=header)

    if args.json:
        if args.query or products:
            data = [normalize_product_summary(p) for p in products]
        else:
            data = [normalize_card(c) for c in cards]
        write_json(args.json, data)

    if not (args.csv or args.json):
        if args.query or products:
            for n in [normalize_product_summary(p) for p in products[:20]]:
                print(f"{n['brand']}: {n['name']} — {n['price']} ₽ ({n['link']})")
        else:
            for n in [normalize_card(c) for c in cards[:20]]:
                print(f"{n['brand']}: {n['name']} — {n['salePrice']} ₽ (nmId={n['nmId']})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())