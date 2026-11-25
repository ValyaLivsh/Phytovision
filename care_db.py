"""Доступ к справкам по уходу в PostgreSQL.

Строка подключения берётся из переменной окружения PV_DB_DSN, например:
    postgresql://pv:pv@localhost:5432/phytovision
"""
from __future__ import annotations

import os

DEFAULT_DSN = "postgresql://pv:pv@localhost:5432/phytovision"
CARE_COLUMNS = ("summary", "light", "watering", "temperature", "feeding", "tips")

_SPECIES_SQL = """
SELECT name_ru, name_lat, summary, light, watering, temperature, feeding, tips
FROM v_plant_info WHERE class_id = %s
"""


class CareRepository:
    """Читает справки по виду и по роду. Ошибки соединения пробрасываются вызывающему."""

    def __init__(self, dsn: str | None = None, timeout: int = 3):
        self.dsn = dsn or os.getenv("PV_DB_DSN", DEFAULT_DSN)
        self.timeout = timeout

    def _connect(self):
        import psycopg  # импорт здесь: модуль работает и без драйвера, если БД не нужна
        return psycopg.connect(self.dsn, connect_timeout=self.timeout)

    def ping(self) -> bool:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone() == (1,)
        except Exception:
            return False

    @staticmethod
    def _species_from_row(row, scope: str = "вид") -> dict:
        name_ru, name_lat, *fields = row
        care = {"scope": scope, "name_ru": name_ru, "name_lat": name_lat}
        care.update(dict(zip(CARE_COLUMNS, fields)))
        return care

    def species_care(self, class_id: str) -> dict | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(_SPECIES_SQL, (class_id,))
            row = cur.fetchone()
        return self._species_from_row(row) if row else None

    def genus_care(self, genus_lat: str) -> dict | None:
        """Справка по роду. Если у рода нет общей справки (в нём один вид),
        возвращается справка по его единственному виду."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT genus_id, name_ru, care_summary FROM genera WHERE name_lat = %s",
                        (genus_lat,))
            row = cur.fetchone()
            if not row:
                return None
            genus_id, name_ru, care = row
            cur.execute("SELECT class_id, name_ru FROM plants WHERE genus_id = %s ORDER BY plant_id",
                        (genus_id,))
            members = cur.fetchall()
            if care:
                result = {"scope": "род", "name_ru": name_ru, "name_lat": genus_lat,
                          "summary": care, "species_ru": [m[1] for m in members]}
                result.update({k: None for k in CARE_COLUMNS if k != "summary"})
                return result
            if members:
                cur.execute(_SPECIES_SQL, (members[0][0],))
                srow = cur.fetchone()
                if srow:
                    return self._species_from_row(srow, scope="род")
        return None
