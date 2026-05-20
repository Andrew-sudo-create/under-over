from scraper.ingestion import run_ingestion
from scraper.property24 import Property24Adapter


def test_run_ingestion_sample_mode_dry_run() -> None:
    result = run_ingestion(
        Property24Adapter(),
        write_to_db=False,
        sample_mode=True,
    )

    assert result.mode == "sample"
    assert result.discovered_count == 1
    assert result.processed_count == 1
    assert result.written_count == 0
    assert result.errors == []
