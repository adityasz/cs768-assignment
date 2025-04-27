import gzip
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from .paper import Paper, paperId


def load_dataset(filename: Path) -> dict[paperId, Paper]:
    """Load the dataset from a gzipped JSON file."""
    with gzip.open(filename, 'rt') as f:
        data: dict[str, Any] = json.load(f)
    return {
        pid: Paper.from_dict(pdata)
        for pid, pdata in data.items()
    }


def save_dataset(
    papers: dict[paperId, Paper],
    output_path: Path,
    json_path: Optional[Path] = None
):
    """Save the dataset to a gzipped JSON file.

    Gzipped JSON is efficient enough. The only inefficiency in this data format
    is that we are also saving the keys, which are not required since the files
    are meant to be consumed by `load_dataset()`. But we will anyways need some
    delimiter to separate keys and values, and hence the overhead is not as big
    (probably less than 1% of the total size).

    Each line of the above paragraph (except the last line) ends at the 79th
    column without any padding, which is so rare that it is worth pointing out.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output_path, 'wt') as f:
        json.dump({
            pid: {
                k: list(v) if isinstance(v, set)
                else v for k, v in asdict(paper).items()
            } for pid, paper in papers.items()
        }, f)

    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(output_path, 'rt') as gz_file:
            with open(json_path, 'w') as json_file:
                json_file.write(gz_file.read())
