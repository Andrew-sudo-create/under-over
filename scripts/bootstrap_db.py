from __future__ import annotations

from pathlib import Path
import sys

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.config import settings


def main() -> None:
    schema_path = PROJECT_ROOT / "db" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

    print(f"Database schema applied from {schema_path}")


if __name__ == "__main__":
    main()
