"""HTTP-интерфейс к модулю. Ответы на русском языке.

Запуск:  uvicorn phytovision.api:app --host 0.0.0.0 --port 8000
Документация OpenAPI: http://localhost:8000/docs
Переменные окружения: PV_MODEL, PV_META, PV_DB_DSN, PV_DB_DISABLE=1 (без базы).
"""
import os
from functools import lru_cache

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from .care_db import CareRepository
from .inference import PlantClassifier, format_report_ru

app = FastAPI(title="PhytoVision: определение растений", version="0.2.0")
MAX_BYTES = 10 * 1024 * 1024


class Prediction(BaseModel):
    rank: int
    id: str
    latin: str
    name_ru: str
    probability: float
    genus: str | None = None
    genus_ru: str | None = None
    species_ru: list[str] | None = None


class Care(BaseModel):
    scope: str
    name_ru: str
    name_lat: str
    summary: str | None = None
    light: str | None = None
    watering: str | None = None
    temperature: str | None = None
    feeding: str | None = None
    tips: str | None = None
    species_ru: list[str] | None = None


class PredictResponse(BaseModel):
    level: str
    level_ru: str
    message_ru: str
    top1_probability: float
    predictions: list[Prediction]
    care: Care | None = None
    care_note_ru: str | None = None
    inference_ms: float
    report_ru: str


@lru_cache(maxsize=1)
def get_repo() -> CareRepository | None:
    return None if os.getenv("PV_DB_DISABLE") == "1" else CareRepository()


@lru_cache(maxsize=1)
def get_classifier() -> PlantClassifier:
    return PlantClassifier(os.getenv("PV_MODEL", "models/plant_classifier.onnx"),
                           os.getenv("PV_META", "models/model_meta.json"), get_repo())


@app.get("/health")
def health() -> dict:
    repo = get_repo()
    return {"статус": "ok", "классов": len(get_classifier().classes),
            "база_данных": ("отключена" if repo is None else "доступна" if repo.ping() else "недоступна")}


@app.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...), top_k: int = Query(3, ge=1, le=10),
                  care: bool = Query(True, description="добавить справку по уходу из БД")) -> dict:
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Файл больше 10 МБ")
    try:
        result = get_classifier().predict(data, top_k=top_k, with_care=care)
    except Exception:
        raise HTTPException(400, "Не удалось обработать изображение")
    result["report_ru"] = format_report_ru(result)
    return result
