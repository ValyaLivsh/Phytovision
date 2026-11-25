"""Генерация db/seed.sql из catalog/plants.yaml.

Запуск:  python -m phytovision.make_seed
Скрипт идемпотентен: повторная загрузка seed.sql обновляет данные, а не дублирует их.
"""
from .catalog import load_catalog
from .config import ROOT


def q(value) -> str:
    """SQL-литерал: NULL или строка с удвоенными апострофами."""
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def build_sql() -> str:
    cat = load_catalog()
    out = ["-- Файл создан автоматически (python -m phytovision.make_seed). Не редактировать вручную.",
           "SET client_encoding = 'UTF8';", "BEGIN;", ""]
    for name in cat["categories"]:
        out.append(f"INSERT INTO categories (name_ru) VALUES ({q(name)}) ON CONFLICT (name_ru) DO NOTHING;")
    out.append("")
    for latin, g in cat["genera"].items():
        out.append(
            "INSERT INTO genera (name_lat, name_ru, care_summary) "
            f"VALUES ({q(latin)}, {q(g['ru'])}, {q(g.get('care'))}) "
            "ON CONFLICT (name_lat) DO UPDATE SET name_ru = EXCLUDED.name_ru, "
            "care_summary = EXCLUDED.care_summary;")
    out.append("")
    for p in cat["plants"]:
        out.append(
            "INSERT INTO plants (class_id, name_lat, name_ru, genus_id, category_id, taxon_rank) VALUES ("
            f"{q(p['id'])}, {q(p['latin'])}, {q(p['ru'])}, "
            f"(SELECT genus_id FROM genera WHERE name_lat = {q(p['genus'])}), "
            f"(SELECT category_id FROM categories WHERE name_ru = {q(p['category'])}), {q(p['rank'])}) "
            "ON CONFLICT (class_id) DO UPDATE SET name_lat = EXCLUDED.name_lat, "
            "name_ru = EXCLUDED.name_ru, genus_id = EXCLUDED.genus_id, "
            "category_id = EXCLUDED.category_id, taxon_rank = EXCLUDED.taxon_rank;")
        c = p["care"]
        out.append(
            "INSERT INTO plant_care (plant_id, summary, light, watering, temperature, feeding, tips) VALUES ("
            f"(SELECT plant_id FROM plants WHERE class_id = {q(p['id'])}), "
            f"{q(c['summary'])}, {q(c['light'])}, {q(c['watering'])}, {q(c['temperature'])}, "
            f"{q(c['feeding'])}, {q(c['tips'])}) "
            "ON CONFLICT (plant_id) DO UPDATE SET summary = EXCLUDED.summary, light = EXCLUDED.light, "
            "watering = EXCLUDED.watering, temperature = EXCLUDED.temperature, "
            "feeding = EXCLUDED.feeding, tips = EXCLUDED.tips;")
    out += ["", "COMMIT;", ""]
    return "\n".join(out)


def main() -> None:
    path = ROOT / "db" / "seed.sql"
    path.write_text(build_sql(), encoding="utf-8")
    print(f"Записано: {path}")


if __name__ == "__main__":
    main()
