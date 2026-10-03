from pathlib import Path

import pytest

from app.providers.exchange.file_provider import find_security_file


def test_finds_latest_nse_file(tmp_path: Path):
    older = tmp_path / "NSE_CM_security_20261001.csv.gz"
    newer = tmp_path / "NSE_CM_security_20261002.csv.gz"

    older.touch()
    newer.touch()

    result = find_security_file(tmp_path, "NSE")

    assert result == newer


def test_raises_when_no_bse_file_exists(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        find_security_file(tmp_path, "BSE")