"""Каталог растений: единый источник данных (catalog/plants.yaml).

Из него берутся: список классов для обучения, русские названия для вывода
модели и справки по уходу для базы PostgreSQL.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from .config import ROOT

CATALOG_PATH = ROOT / "catalog" / "plants.yaml"
CARE_FIELDS = ("summary", "light", "watering", "temperature", "feeding", "tips")
RANKS = ("species", "genus")
_ID_RE = re.compile(r"^[A-Z][a-z]+(_[a-z-]+)?$")


def validate(data: dict) -> None:
    errors: list[str] = []
    cats, genera = set(data["categories"]), data["genera"]
    seen: set[str] = set()
    for p in data["plants"]:
        pid = p.get("id", "?")
        if pid in seen:
            errors.append(f"{pid}: дубликат id")
        seen.add(pid)
        if not _ID_RE.match(pid):
            errors.append(f"{pid}: id должен иметь вид Genus_species")
        if p.get("genus") not in genera:
            errors.append(f"{pid}: род {p.get('genus')} не описан в genera")
        if pid.split("_")[0] != p.get("genus"):
            errors.append(f"{pid}: id не совпадает с родом")
        if p.get("rank") not in RANKS:
            errors.append(f"{pid}: неверный rank")
        if p.get("rank") == "genus" and pid != p.get("genus"):
            errors.append(f"{pid}: для rank=genus id должен быть названием рода")
        if p.get("category") not in cats:
            errors.append(f"{pid}: неизвестная категория")
        for key in ("latin", "ru", "inat"):
            if not p.get(key):
                errors.append(f"{pid}: пустое поле {key}")
        care = p.get("care") or {}
        for f in CARE_FIELDS:
            if not str(care.get(f, "")).strip():
                errors.append(f"{pid}: пустое поле care.{f}")
    for g, v in genera.items():
        if not v.get("ru"):
            errors.append(f"род {g}: нет русского названия")
    if errors:
        raise ValueError("Ошибки каталога:\n" + "\n".join(errors))


@lru_cache(maxsize=1)
def load_catalog(path: str | Path = CATALOG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    validate(data)
    return data


def class_ids() -> list[str]:
    return sorted(p["id"] for p in load_catalog()["plants"])


def plants_by_id() -> dict[str, dict]:
    return {p["id"]: p for p in load_catalog()["plants"]}
