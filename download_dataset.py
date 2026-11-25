"""Скачивание фотографий с iNaturalist по каталогу catalog/plants.yaml.

Запуск:  python -m phytovision.download_dataset --per-class 150
Скачивание можно прерывать и запускать заново: уже имеющиеся файлы пропускаются.

Берутся только фото со свободными лицензиями (CC0, CC-BY, CC-BY-NC). Сначала
наблюдения, помеченные как культурные/комнатные (captive), затем научные наблюдения
(research grade). Источник каждого файла записывается в data/download_log.csv
(автор и лицензия нужны для указания в работе). Уровень «tier» в журнале позволяет
отфильтровать менее надёжные снимки.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import time

import requests

from .catalog import load_catalog
from .config import ROOT

API = "https://api.inaturalist.org/v1"
HEADERS = {"User-Agent": "PhytoVision-coursework/0.2 (educational project)"}
LICENSES = "cc0,cc-by,cc-by-nc"
TIERS = (("cultivated", {"captive": "true"}), ("research", {"quality_grade": "research"}))
PAGE = 200


def get_json(session: requests.Session, path: str, params: dict) -> dict:
    for attempt in range(4):
        try:
            r = session.get(f"{API}/{path}", params=params, timeout=60)
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1)); continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
    return {"results": []}


def resolve_taxon(session, query: str):
    """Находит id таксона по точному названию (или по синониму).

    Пробует несколько вариантов запроса (дефис, регистр) и выводит, что вернул
    iNaturalist, если таксон найти не удалось."""
    seen: list[str] = []
    for q_text in dict.fromkeys([query, query.replace("-", " "), query.split()[0] + " " + query.split()[-1]]):
        for extra in ({"is_active": "true"}, {}):
            results = get_json(session, "taxa", {"q": q_text, "per_page": 30, **extra})["results"]
            q = query.lower()
            for t in results:
                if t["name"].lower() == q:
                    return t["id"], t["name"]
            for t in results:
                if (t.get("matched_term") or "").lower() in (q, q_text.lower()):
                    return t["id"], t["name"]
            seen += [t["name"] for t in results[:5]]
            time.sleep(2)
    print(f"   iNaturalist вернул: {sorted(set(seen))[:10] or 'ничего (возможно, лимит запросов, повторите позже)'}")
    return None


def collect(session, taxon_id: int, want: int, have_ids: set[str]) -> list[dict]:
    found: dict[int, dict] = {}
    for tier_name, tier_params in TIERS:
        for page in range(1, 6):
            if len(found) + len(have_ids) >= want:
                break
            data = get_json(session, "observations", {
                "taxon_id": taxon_id, "photos": "true", "photo_license": LICENSES,
                "per_page": PAGE, "order_by": "random", "page": page, **tier_params})
            for o in data["results"]:
                if o["id"] in found or str(o["id"]) in have_ids or not o.get("photos"):
                    continue
                ph = o["photos"][0]
                found[o["id"]] = {"obs_id": o["id"], "tier": tier_name,
                                  "license": ph.get("license_code"),
                                  "user": (o.get("user") or {}).get("login"),
                                  "url": ph["url"].replace("square", "medium")}
            time.sleep(1)
            if len(data["results"]) < PAGE:
                break
    return list(found.values())[: max(0, want - len(have_ids))]


def fetch_image(item: dict, folder):
    try:
        r = requests.get(item["url"], headers=HEADERS, timeout=30)
        r.raise_for_status()
        (folder / f"{item['obs_id']}.jpg").write_bytes(r.content)
        return item
    except requests.RequestException:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=150)
    ap.add_argument("--only", default="", help="id классов через запятую (по умолчанию все)")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    plants = load_catalog()["plants"]
    if a.only:
        wanted = set(a.only.split(","))
        plants = [p for p in plants if p["id"] in wanted]
    raw = ROOT / "data" / "raw"
    log_path = ROOT / "data" / "download_log.csv"
    new_log = not log_path.exists()
    session = requests.Session(); session.headers.update(HEADERS)

    with open(log_path, "a", newline="", encoding="utf-8") as lf:
        writer = csv.DictWriter(lf, fieldnames=["class_id", "obs_id", "tier", "license", "user", "url"])
        if new_log:
            writer.writeheader()
        for p in plants:
            folder = raw / p["id"]; folder.mkdir(parents=True, exist_ok=True)
            have = {f.stem for f in folder.glob("*.jpg")}
            if len(have) >= a.per_class:
                print(f"{p['id']}: уже {len(have)} фото"); continue
            taxon = resolve_taxon(session, p["inat"])
            if not taxon:
                print(f"{p['id']}: таксон '{p['inat']}' не найден на iNaturalist, замените поле inat"); continue
            items = collect(session, taxon[0], a.per_class, have)
            with cf.ThreadPoolExecutor(a.workers) as ex:
                done = [r for r in ex.map(lambda it: fetch_image(it, folder), items) if r]
            for it in done:
                writer.writerow({"class_id": p["id"], **{k: it[k] for k in ("obs_id", "tier", "license", "user", "url")}})
            lf.flush()
            print(f"{p['id']}: было {len(have)}, добавлено {len(done)} (итого {len(have) + len(done)})")


if __name__ == "__main__":
    main()
