-- Примеры запросов для демонстрации на защите.
-- 1. Справка по растению (так обращается к базе приложение):
SELECT * FROM v_plant_info WHERE class_id = 'Ficus_benjamina';

-- 2. Сколько растений в каждой категории:
SELECT c.name_ru, COUNT(*) AS plants
FROM plants p JOIN categories c USING (category_id)
GROUP BY c.name_ru ORDER BY plants DESC;

-- 3. Роды, в которых модель знает несколько видов (для ответа на уровне рода):
SELECT g.name_ru, g.name_lat, COUNT(*) AS species_count,
       STRING_AGG(p.name_ru, '; ' ORDER BY p.plant_id) AS species
FROM genera g JOIN plants p USING (genus_id)
GROUP BY g.genus_id HAVING COUNT(*) > 1 ORDER BY species_count DESC;

-- 4. Общая справка по роду:
SELECT name_ru, care_summary FROM genera WHERE name_lat = 'Aloe';
