import argparse
import json
import logging
import os
import re
import shutil
import sys
import tarfile
import time
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union

import requests
from requests.models import HTTPError, Response
from tqdm import tqdm

from cglp.data import Paper, save_dataset

paperId = str
"""The unique identifier for a paper assigned by Semantic Scholar."""
arXivId = str
"""The unique identifier for a paper assigned by arXiv."""

BATCH_SIZE: int = 200
"""Number of papers in each request to Semantic Scholar."""
RATE_LIMIT_DELAY: int = 5
"""Delay between requests to Semantic Scholar."""

logger = logging.getLogger()


def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--data", type=Path, default="dataset_papers.tar.gz",
        help="path to the assignment dataset tarball or directory (default: dataset_papers.tar.gz)")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("data/dataset"),
        help="path to store the processed dataset (default: data/dataset)")
    parser.add_argument("--request", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--log", type=Path, default="logs/semanticscholar")
    parser.add_argument(
        "--json", nargs='?', type=Path, const="data/dataset.json",
        help="save the dataset as json (the path is optional and defaults to data/dataset.json)")
    return parser.parse_args()


def setup_logger():
    fmt: str = "[%(asctime)s] %(levelname)s: %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    logger.addHandler(console_handler)


def clean_dataset(ta_dataset: Path):
    dirs = [dir for dir in ta_dataset.iterdir() if dir.is_dir()]
    groups: dict[str, list[Path]] = defaultdict(list)
    for d in dirs:
        if m := re.match(r"^(\d{4}\.\d{4,5})(v\d+)?$", d.name):
            base_id = m.group(1)
            groups[base_id].append(d)

    for base_id, paths in groups.items():
        def version_num(p: Path) -> int:
            vm = re.search(r"v(\d+)$", p.name)
            return int(vm.group(1)) if vm else 0
        chosen = max(paths, key=version_num)
        for p in paths:
            if p != chosen:
                logger.info(f"removing {str(p)} in favor of {str(chosen)}")
                shutil.rmtree(p)
        target = ta_dataset / base_id
        if chosen.name != base_id:
            if target.exists():
                shutil.rmtree(target)
            chosen.rename(target)


def get_papers(
    ta_dataset: Path,
    filename: Path,
    make_requests: bool = False,
    clean: bool = False
) -> dict[paperId, Paper]:
    arxiv_ids: list[arXivId] = sorted(os.listdir(ta_dataset))

    paper_data: dict[arXivId, dict[str, Union[int, str, list[dict[str, str]]]]] = {}
    if filename.exists():
        with open(filename, 'r') as f:
            paper_data = json.load(f)
    else:
        filename.parent.mkdir(parents=True, exist_ok=True)

    missing_ids: list[arXivId] = [arxiv_id for arxiv_id in arxiv_ids if arxiv_id not in paper_data]

    if missing_ids and make_requests:
        num_batches = (len(missing_ids) + BATCH_SIZE - 1) // BATCH_SIZE
        for batch_idx in tqdm(range(num_batches), desc="Processing batches"):
            i = batch_idx * BATCH_SIZE
            batch = missing_ids[i : i + BATCH_SIZE]
            ids: list[str] = [f"ARXIV:{id}" for id in batch]
            logger.info("sending request...")
            r: Response = requests.post(
                "https://api.semanticscholar.org/graph/v1/paper/batch",
                params={"fields": "referenceCount,references"},
                json={"ids": ids}
            )
            try:
                r.raise_for_status()
            except HTTPError as e:
                logger.error(f"request failed with status code {r.status_code}: {e}",
                             exc_info=True)
            for arxiv_id, data in zip(batch, r.json()):
                paper_data[arxiv_id] = data
            with open(filename, 'w') as f:
                json.dump(paper_data, f, indent=4)
            if batch_idx + BATCH_SIZE < len(missing_ids):
                time.sleep(RATE_LIMIT_DELAY)
    elif missing_ids:
        logger.warning(f"no data found for {len(missing_ids)} papers: {', '.join(missing_ids)}")

    papers: dict[paperId, Paper] = {}
    arxiv_id_to_paper_id: dict[arXivId, paperId] = {}

    bad_data: int = 0
    incomplete_references: int = 0
    for arxiv_id, data in tqdm(paper_data.items(), desc="Processing papers"):
        if not isinstance(data, dict):
            logger.warning(f"bad data for arXiv:{arxiv_id}")
            bad_data += 1
            if clean:
                del paper_data[arxiv_id]
            continue
        paper_id  = data.get("paperId")
        ref_count = data.get("referenceCount")
        references = data.get("references")
        if not isinstance(paper_id, paperId):
            logger.warning(f"bad paperId for arXiv:{arxiv_id}")
            bad_data += 1
            if clean:
                del paper_data[arxiv_id]
            continue
        if not isinstance(ref_count, int):
            logger.warning(f"bad referenceCount for arXiv:{arxiv_id}")
            bad_data += 1
            if clean:
                del paper_data[arxiv_id]
            continue
        if not isinstance(references, list):
            logger.warning(f"bad references for arXiv:{arxiv_id}")
            bad_data += 1
            if clean:
                del paper_data[arxiv_id]
            continue
        arxiv_id_to_paper_id[arxiv_id] = paper_id
        if len(references) < int(0.75 * ref_count):
            logger.warning(f"incomplete references for paper arXiv:{arxiv_id}: "
                           f"referenceCount == {ref_count} != {len(references)}")
            if clean:
                incomplete_references += 1
                del paper_data[arxiv_id]
                continue
            incomplete_references += 1
        with open(ta_dataset/arxiv_id/"title.txt", 'r') as f:
            title: str = f.read()
        with open(ta_dataset/arxiv_id/"abstract.txt", 'r') as f:
            abstract: str = f.read()
        papers[paper_id] = Paper(title, abstract, arxiv_id,
                                 set(paper["paperId"] for paper in references))
    if incomplete_references:
        logger.warning(f"{incomplete_references} incomplete references")
    if bad_data:
        logger.warning(f"{bad_data} papers with bad data")
    return papers




def main():
    args = parse_args()
    setup_logger()

    papers: dict[paperId, Paper] = {}
    if os.path.isdir(args.data):
        clean_dataset(args.data)
        papers = get_papers(args.data, args.log, args.request, args.clean)
    elif tarfile.is_tarfile(args.data):
        with tarfile.open(args.data, mode='r') as tar:
            with TemporaryDirectory() as tmpdir:
                tar.extractall(path=tmpdir, filter="data")
                clean_dataset(tmpdir/Path("dataset_papers"))
                papers = get_papers(
                    tmpdir/Path("dataset_papers"), args.log, args.request, args.clean)
    else:
        print(f"Error: {args.data} is neither a tarball nor a directory", file=sys.stderr)
        exit(1)

    if args.json:
        save_dataset(papers, args.output, args.json)
    else:
        save_dataset(papers, args.output)


if __name__ == "__main__":
    main()
