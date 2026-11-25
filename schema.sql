-- Схема базы данных PhytoVision (PostgreSQL 12+).
-- Три уровня: категория -> род -> растение -> справка по уходу (третья нормальная форма).
SET client_encoding = 'UTF8';

CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    name_ru     VARCHAR(64) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS genera (
    genus_id     SERIAL PRIMARY KEY,
    name_lat     VARCHAR(64)  NOT NULL UNIQUE,   -- Ficus
    name_ru      VARCHAR(128) NOT NULL,          -- Фикус
    care_summary TEXT                            -- общая справка по роду (если в роде несколько видов)
);

CREATE TABLE IF NOT EXISTS plants (
    plant_id    SERIAL PRIMARY KEY,
    class_id    VARCHAR(96)  NOT NULL UNIQUE,    -- метка класса нейросети: Ficus_elastica
    name_lat    VARCHAR(128) NOT NULL,
    name_ru     VARCHAR(160) NOT NULL,
    genus_id    INTEGER NOT NULL REFERENCES genera(genus_id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    taxon_rank  VARCHAR(8)   NOT NULL CHECK (taxon_rank IN ('species', 'genus'))
);
CREATE INDEX IF NOT EXISTS idx_plants_genus    ON plants (genus_id);
CREATE INDEX IF NOT EXISTS idx_plants_category ON plants (category_id);

CREATE TABLE IF NOT EXISTS plant_care (
    plant_id    INTEGER PRIMARY KEY REFERENCES plants(plant_id) ON DELETE CASCADE,
    summary     TEXT NOT NULL,   -- кратко о растении
    light       TEXT NOT NULL,   -- свет
    watering    TEXT NOT NULL,   -- полив
    temperature TEXT NOT NULL,   -- температура
    feeding     TEXT NOT NULL,   -- подкормка
    tips        TEXT NOT NULL    -- советы и частые проблемы
);

-- Удобное представление: всё о растении одним запросом.
CREATE OR REPLACE VIEW v_plant_info AS
SELECT p.class_id, p.name_ru, p.name_lat, g.name_ru AS genus_ru, g.name_lat AS genus_lat,
       c.name_ru AS category_ru, p.taxon_rank,
       pc.summary, pc.light, pc.watering, pc.temperature, pc.feeding, pc.tips
FROM plants p
JOIN genera g     ON g.genus_id = p.genus_id
JOIN categories c ON c.category_id = p.category_id
JOIN plant_care pc ON pc.plant_id = p.plant_id;
