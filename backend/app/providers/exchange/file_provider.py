from pathlib import Path

from app.domain.models import Security


def find_security_file(
    data_dir: Path,
    exchange: str,
) -> Path:
    patterns = {
        "NSE": ["NSE_CM_security_*.csv.gz"],
        "BSE": ["BSE_EQ_SCRIP_*.csv"],
    }

    files = []

    for pattern in patterns[exchange]:
        files.extend(data_dir.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"No {exchange} security file found in {data_dir}"
        )

    return max(files, key=lambda path: path.stat().st_mtime)