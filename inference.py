"""Программный интерфейс инференса (ТЗ п. 5.3, 5.5). Весь вывод на русском языке.

Пример::

    from phytovision.inference import PlantClassifier, format_report_ru
    clf = PlantClassifier("models/plant_classifier.onnx", "models/model_meta.json")
    result = clf.predict("photo.jpg")          # dict, готов к json.dumps
    print(format_report_ru(result))            # человекочитаемый отчёт

Формат результата::

    {"level": "species" | "genus", "level_ru": "вид" | "род",
     "message_ru": "...", "top1_probability": 0.91,
     "predictions": [{"rank": 1, "id": "Ficus_benjamina", "latin": "Ficus benjamina",
                      "name_ru": "Фикус Бенджамина", "probability": 0.91, ...}],
     "care": {...} | None, "inference_ms": 42.1}

Если уверенность в виде ниже порога, вероятности суммируются по роду и
возвращается родовая гипотеза (level == "genus") с названиями видов-кандидатов.
"""
from __future__ import annotations

import io
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Union

import numpy as np
import onnxruntime as ort
from PIL import Image

ImageInput = Union[str, Path, bytes, Image.Image]

CARE_LABELS = (("summary", "Кратко"), ("light", "Свет"), ("watering", "Полив"),
               ("temperature", "Температура"), ("feeding", "Подкормка"), ("tips", "Советы"))


def softmax(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


class Taxonomy:
    """Соответствие «метка класса -> латинское и русское название, род»."""

    def __init__(self, classes, latin=None, names_ru=None, genus=None, genera_ru=None):
        self.classes = list(classes)
        self.latin = {c: (latin or {}).get(c, c.replace("_", " ")) for c in self.classes}
        self.ru = {c: (names_ru or {}).get(c, self.latin[c]) for c in self.classes}
        self.genus = {c: (genus or {}).get(c, c.split("_")[0]) for c in self.classes}
        self.genus_ru = dict(genera_ru or {})
        self.members: dict[str, list[int]] = defaultdict(list)
        for i, c in enumerate(self.classes):
            self.members[self.genus[c]].append(i)

    @classmethod
    def from_meta(cls, meta: dict) -> "Taxonomy":
        return cls(meta["classes"], meta.get("latin"), meta.get("names_ru"),
                   meta.get("genus"), meta.get("genera_ru"))


def _pct(p: float) -> str:
    return f"{p * 100:.0f} %"


def rank_predictions(probs: np.ndarray, tax: Taxonomy, top_k: int = 3,
                     threshold: float = 0.5) -> dict:
    """Ранжированный список таксонов; при низкой уверенности — уровень рода."""
    top_k = max(1, min(top_k, len(tax.classes)))
    order = np.argsort(-probs)
    best = int(order[0])
    best_c = tax.classes[best]

    if probs[best] >= threshold:
        preds = []
        for r, i in enumerate(order[:top_k]):
            c = tax.classes[int(i)]
            preds.append({"rank": r + 1, "id": c, "latin": tax.latin[c], "name_ru": tax.ru[c],
                          "genus": tax.genus[c],
                          "genus_ru": tax.genus_ru.get(tax.genus[c], tax.genus[c]),
                          "probability": round(float(probs[i]), 4)})
        return {"level": "species", "level_ru": "вид",
                "message_ru": f"Определён вид: {tax.ru[best_c]} ({tax.latin[best_c]}). "
                              f"Уверенность: {_pct(preds[0]['probability'])}.",
                "top1_probability": preds[0]["probability"], "predictions": preds}

    gp = {g: float(sum(probs[i] for i in idx)) for g, idx in tax.members.items()}
    ranked = sorted(gp.items(), key=lambda kv: -kv[1])[:top_k]
    preds = []
    for r, (g, p) in enumerate(ranked):
        idx = sorted(tax.members[g], key=lambda i: -probs[i])
        preds.append({"rank": r + 1, "id": g, "latin": g, "name_ru": tax.genus_ru.get(g, g),
                      "probability": round(p, 4),
                      "species_ru": [tax.ru[tax.classes[i]] for i in idx]})
    top = preds[0]
    message = (f"Уверенность в виде недостаточна (лучший вариант — {tax.ru[best_c]}, "
               f"{_pct(float(probs[best]))}). Определён род: {top['name_ru']} ({top['latin']}), "
               f"суммарная вероятность {_pct(top['probability'])}.")
    if len(top["species_ru"]) > 1:
        message += " Возможные виды: " + "; ".join(top["species_ru"]) + "."
    return {"level": "genus", "level_ru": "род", "message_ru": message,
            "top1_probability": top["probability"], "predictions": preds}


def format_report_ru(result: dict) -> str:
    """Человекочитаемый отчёт на русском языке."""
    lines = [result["message_ru"], "",
             "Предположения (%s):" % ("виды" if result["level"] == "species" else "роды")]
    for p in result["predictions"]:
        line = f"  {p['rank']}. {p['name_ru']} ({p['latin']}) — {p['probability'] * 100:.1f} %"
        if p.get("species_ru") and len(p["species_ru"]) > 1:
            line += "; виды: " + ", ".join(p["species_ru"])
        lines.append(line)
    care = result.get("care")
    if care:
        lines += ["", f"Справка по уходу ({care['scope']}: {care['name_ru']}):"]
        lines += [f"  {label}: {care[key]}" for key, label in CARE_LABELS if care.get(key)]
    elif result.get("care_note_ru"):
        lines += ["", result["care_note_ru"]]
    return "\n".join(lines)


class PlantClassifier:
    def __init__(self, model_path: str | Path, meta_path: str | Path,
                 care_repo=None, providers: list[str] | None = None):
        with open(meta_path, encoding="utf-8") as f:
            self.meta = json.load(f)
        self.tax = Taxonomy.from_meta(self.meta)
        self.classes: list[str] = self.meta["classes"]
        self.size: int = self.meta["image_size"]
        self.mean = np.array(self.meta["mean"], dtype=np.float32).reshape(1, 1, 3)
        self.std = np.array(self.meta["std"], dtype=np.float32).reshape(1, 1, 3)
        self.care = care_repo      # CareRepository или None (справки отключены)
        self.session = ort.InferenceSession(
            str(model_path), providers=providers or ["CPUExecutionProvider"])

    @staticmethod
    def _load(image: ImageInput) -> Image.Image:
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        if isinstance(image, (bytes, bytearray)):
            return Image.open(io.BytesIO(image)).convert("RGB")
        return Image.open(image).convert("RGB")

    def preprocess(self, image: ImageInput) -> np.ndarray:
        """Resize(1.14*size) -> CenterCrop(size) -> normalize; как при валидации."""
        img = self._load(image)
        short = int(self.size * 1.14)
        w, h = img.size
        scale = short / min(w, h)
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.BICUBIC)
        w, h = img.size
        l, t = (w - self.size) // 2, (h - self.size) // 2
        img = img.crop((l, t, l + self.size, t + self.size))
        arr = (np.asarray(img, dtype=np.float32) / 255.0 - self.mean) / self.std
        return arr.transpose(2, 0, 1)[None]

    def _attach_care(self, result: dict) -> None:
        result["care"] = None
        if self.care is None:
            return
        top = result["predictions"][0]
        try:
            care = (self.care.species_care(top["id"]) if result["level"] == "species"
                    else self.care.genus_care(top["id"]))
        except Exception:
            result["care_note_ru"] = "Справка по уходу временно недоступна: нет связи с базой данных."
            return
        if care is None:
            result["care_note_ru"] = "Для этого растения в базе данных пока нет справки по уходу."
        result["care"] = care

    def predict(self, image: ImageInput, top_k: int | None = None,
                threshold: float | None = None, with_care: bool = True) -> dict:
        t0 = time.perf_counter()
        x = self.preprocess(image)
        logits = self.session.run(None, {"image": x})[0][0]
        result = rank_predictions(
            softmax(logits), self.tax, top_k or self.meta["top_k"],
            self.meta["confidence_threshold"] if threshold is None else threshold)
        if with_care:
            self._attach_care(result)
        else:
            result["care"] = None
        result["inference_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return result


def _cli() -> None:
    import argparse
    from .care_db import CareRepository
    ap = argparse.ArgumentParser(description="PhytoVision: определение растения по фото")
    ap.add_argument("image")
    ap.add_argument("--model", default="models/plant_classifier.onnx")
    ap.add_argument("--meta", default="models/model_meta.json")
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--no-db", action="store_true", help="не обращаться к базе PostgreSQL")
    ap.add_argument("--json", action="store_true", help="вывести результат в формате JSON")
    a = ap.parse_args()
    clf = PlantClassifier(a.model, a.meta, None if a.no_db else CareRepository())
    result = clf.predict(a.image, a.top_k)
    print(json.dumps(result, ensure_ascii=False, indent=2) if a.json else format_report_ru(result))


if __name__ == "__main__":
    _cli()
