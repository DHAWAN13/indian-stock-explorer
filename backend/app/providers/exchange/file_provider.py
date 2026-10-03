import re
from datetime import datetime
from pathlib import Path


def find_security_file(
    data_dir: Path,
    exchange: str,
) -> Path:
    patterns = {
        "NSE": "NSE_CM_security_*.csv.gz",
        "BSE": "BSE_EQ_SCRIP_*.csv",
    }

    if exchange not in patterns:
        raise ValueError(f"Unsupported exchange: {exchange}")

    files = list(data_dir.glob(patterns[exchange]))

    if not files:
        raise FileNotFoundError(
            f"No {exchange} security file found in {data_dir}"
        )

    dated_files = []

    for path in files:
        match = re.search(r"(\d{8})", path.name)

        if not match:
            continue

        file_date = datetime.strptime(
            match.group(1),
            "%d%m%Y",
        )

        dated_files.append((file_date, path))

    if not dated_files:
        raise ValueError(
            f"No dated {exchange} security file found"
        )

    return max(
        dated_files,
        key=lambda item: item[0],
    )[1]