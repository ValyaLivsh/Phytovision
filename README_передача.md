# Передача модуля PhytoVision (определение растений)

## Что внутри
- models/plant_classifier.onnx, models/model_meta.json: модель (ONNX) и метаданные (классы, русские названия, пороги)
- db/phytovision_dump.sql: полный дамп PostgreSQL (схема и справки по уходу за 50 растениями)
- db/schema.sql, db/seed.sql: то же самое по отдельности (альтернатива дампу)
- catalog/plants.yaml: список растений, русские названия, справки (источник данных для БД)
- src/phytovision: код инференса (inference.py), доступа к БД (care_db.py), REST API (api.py)
- metrics/: результаты на тесте

## Быстрый запуск (Docker)
    docker compose up --build
    # API: http://localhost:8000/docs   проверка: http://localhost:8000/health

## Восстановление базы вручную
    createdb -U postgres phytovision
    psql -U postgres -d phytovision -f db/phytovision_dump.sql
Строка подключения для приложения: переменная окружения PV_DB_DSN, например
    postgresql://pv:pv@localhost:5432/phytovision

## Как вызвать модуль
POST /predict (multipart, поле file, параметры top_k=3, care=true). Ответ (JSON) содержит:
level ("species" или "genus"), level_ru ("вид"/"род"), message_ru, predictions[] (rank, id, latin, name_ru,
probability), care (справка по уходу из БД), report_ru (готовый текст на русском), inference_ms.
Если уверенность в виде ниже порога (в model_meta.json: confidence_threshold), возвращается род
и список видов-кандидатов (species_ru).

## Вход модели
RGB-фото; предобработка (resize 1.14*размер, центральный кроп, нормализация ImageNet) выполняется в
inference.py. Размер входа и нормализация лежат в model_meta.json.
