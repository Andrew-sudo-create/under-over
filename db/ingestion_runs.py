from __future__ import annotations

import json
from typing import TYPE_CHECKING

import psycopg
from psycopg.rows import dict_row

if TYPE_CHECKING:
    from scraper.ingestion import IngestionResult


def save_ingestion_run(conn: psycopg.Connection, result: "IngestionResult") -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into ingestion_runs (
                source, mode, search_url, started_at, finished_at,
                discovered_count, processed_count, written_count, error_count, errors, quality_summary
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
            """,
            (
                result.source,
                result.mode,
                result.search_url,
                result.started_at,
                result.finished_at,
                result.discovered_count,
                result.processed_count,
                result.written_count,
                len(result.errors),
                json.dumps(result.errors),
                json.dumps(result.quality_summary),
            ),
        )


def get_recent_ingestion_runs(database_url: str, limit: int = 20) -> list[dict]:
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    id,
                    source,
                    mode,
                    search_url,
                    started_at,
                    finished_at,
                    discovered_count,
                    processed_count,
                    written_count,
                    error_count,
                    errors,
                    quality_summary,
                    created_at
                from ingestion_runs
                order by created_at desc
                limit %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    output: list[dict] = []
    for row in rows:
        row["started_at"] = row["started_at"].isoformat()
        row["finished_at"] = row["finished_at"].isoformat()
        row["created_at"] = row["created_at"].isoformat()
        output.append(row)
    return output
