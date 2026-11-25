"""Формирование структурированного и размеченного набора данных (цель ТЗ п. 3).

Ожидаемая структура:  data/raw/<Genus_species>/*.jpg
Результат: manifest.csv (path,label,split) и classes.json.
Выполняются: фильтрация битых файлов, удаление точных дубликатов (по MD5,
чтобы исключить утечку между train/test), стратифицированное разбиение.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split

from .catalog import class_ids
from .config import ROOT, load_params

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_valid(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


def main() -> None:
    p = load_params()["data"]
    raw = ROOT / p["raw_dir"]
    rows, seen = [], set()
    for cls_dir in sorted(d for d in raw.iterdir() if d.is_dir()):
        for f in sorted(cls_dir.rglob("*")):
            if f.suffix.lower() not in EXTS or not is_valid(f):
                continue
            h = md5(f)
            if h in seen:
                continue
            seen.add(h)
            rows.append({"path": str(f.relative_to(ROOT)), "label": cls_dir.name})
    df = pd.DataFrame(rows)

    known = set(class_ids())
    extra = sorted(set(df["label"]) - known)
    if extra:
        print("Пропущены папки, которых нет в catalog/plants.yaml:", extra)
    df = df[df["label"].isin(known)]

    counts = df["label"].value_counts()
    keep = counts[counts >= p["min_images_per_class"]].index
    df = df[df["label"].isin(keep)].reset_index(drop=True)
    classes = sorted(df["label"].unique())
    missing = sorted(known - set(classes))
    if missing:
        print(f"ВНИМАНИЕ: нет данных (или слишком мало фото) для {len(missing)} классов: {missing}")

    hold = p["val_size"] + p["test_size"]
    train, rest = train_test_split(
        df, test_size=hold, stratify=df["label"], random_state=p["seed"])
    val, test = train_test_split(
        rest, test_size=p["test_size"] / hold, stratify=rest["label"],
        random_state=p["seed"])
    df.loc[train.index, "split"] = "train"
    df.loc[val.index, "split"] = "val"
    df.loc[test.index, "split"] = "test"

    out = ROOT / p["manifest"]
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    with open(ROOT / p["classes"], "w", encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False, indent=2)
    print(f"Классов: {len(classes)}, изображений: {len(df)}")
    print(df["split"].value_counts().to_string())


if __name__ == "__main__":
    main()
