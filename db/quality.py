from __future__ import annotations

import psycopg
from psycopg.rows import dict_row


def get_data_quality_report(database_url: str) -> dict:
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    count(*) as total_rows,
                    sum(case when city is null or city = '' then 1 else 0 end) as missing_city_count,
                    sum(case when suburb is null or suburb = '' then 1 else 0 end) as missing_suburb_count,
                    sum(case when property_type is null or property_type = '' then 1 else 0 end) as missing_property_type_count,
                    sum(case when asking_price is null then 1 else 0 end) as missing_asking_price_count
                from listings_normalized
                """
            )
            totals = cur.fetchone() or {}

            cur.execute(
                """
                select
                    coalesce(city, 'UNKNOWN') as city,
                    count(*) as listing_count,
                    sum(case when asking_price is null then 1 else 0 end) as missing_price_count
                from listings_normalized
                group by coalesce(city, 'UNKNOWN')
                order by listing_count desc, city asc
                limit 20
                """
            )
            by_city = cur.fetchall()

    total_rows = int(totals.get("total_rows", 0) or 0)
    missing_city_count = int(totals.get("missing_city_count", 0) or 0)
    missing_suburb_count = int(totals.get("missing_suburb_count", 0) or 0)
    missing_property_type_count = int(totals.get("missing_property_type_count", 0) or 0)
    missing_asking_price_count = int(totals.get("missing_asking_price_count", 0) or 0)

    def _pct(count: int) -> float:
        if total_rows == 0:
            return 0.0
        return round((count / total_rows) * 100, 2)

    return {
        "total_rows": total_rows,
        "missing_rates": {
            "city_pct": _pct(missing_city_count),
            "suburb_pct": _pct(missing_suburb_count),
            "property_type_pct": _pct(missing_property_type_count),
            "asking_price_pct": _pct(missing_asking_price_count),
        },
        "counts": {
            "missing_city_count": missing_city_count,
            "missing_suburb_count": missing_suburb_count,
            "missing_property_type_count": missing_property_type_count,
            "missing_asking_price_count": missing_asking_price_count,
        },
        "by_city": by_city,
    }
