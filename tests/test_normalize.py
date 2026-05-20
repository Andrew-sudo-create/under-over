from scraper.normalize import normalize_text, parse_float, parse_int


def test_parse_int_with_currency_like_string() -> None:
    assert parse_int("R 1,650,000") == 1650000


def test_parse_float_with_decimal_string() -> None:
    assert parse_float("1.5") == 1.5


def test_normalize_text_trims_and_compacts_whitespace() -> None:
    assert normalize_text("  Sandton   Central  ") == "Sandton Central"
