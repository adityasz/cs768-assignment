import argparse
import logging
import os
import re
import shutil
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Optional

import bibtexparser as bp
from rapidfuzz import fuzz
from tqdm import tqdm

from cglp.data import Paper, save_dataset


arXivId = str
"""The unique identifier for a paper assigned by arXiv."""
BIB_FILE: str = "super_simple_refs.txt"
"""The name of the file containing the references in each paper directory."""


class ColoredLogger(logging.Logger):
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"

    def __init__(self, name):
        super().__init__(name)


logging.setLoggerClass(ColoredLogger)
logger: ColoredLogger = logging.getLogger(__name__) # type: ignore


def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--data", type=Path, default="dataset_papers",
        help="path to the assignment dataset (default: dataset_papers)")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("data/dataset"),
        help="path to store the processed dataset (default: data/dataset)")
    parser.add_argument("--clean", action="store_true", help="stop after cleaning dataset")
    parser.add_argument("--preprocess", action="store_true", help="stop after preprocessing dataset")
    parser.add_argument(
        "--log", nargs="?", type=Path, const="/tmp/cs768-citations",
        help="log to a fifo (the path is optional and defaults to /tmp/cs768-citations)"
    )
    parser.add_argument(
        "--json", nargs='?', type=Path, const="data/dataset.json",
        help="save the dataset as json (the path is optional and defaults to data/dataset.json)")
    return parser.parse_args()


def setup_logger(logfile: Optional[Path] = None):
    fmt: str = "[%(asctime)s] %(levelname)s: %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    logger.setLevel(logging.INFO)
    if logfile:
        if not logfile.is_fifo():
            if logfile.exists():
                os.remove(logfile)
            os.mkfifo(logfile)
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.INFO)
    else:
        file_handler = logging.StreamHandler()
        file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    logger.addHandler(file_handler)


def clean_dataset(ta_dataset: Path):
    """Keeps only the latest version of each paper."""
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


def process_bibliographies(dataset: Path) -> list[tuple[arXivId, str]]:
    """Processes bib and bbl files."""
    bibs: list[tuple[arXivId, str]] = []
    for dir in tqdm([dataset / dir for dir in sorted(os.listdir(dataset), reverse=True)],
                    desc="Simplifying references"):
        bib_file: Path = dir / BIB_FILE
        if bib_file.exists():
            bibs.append((dir.name, bib_file.read_text(encoding="utf-8").lower()))
            continue
        refs: str = ""
        for file in dir.iterdir():
            if file.suffix in (".bbl", ".bib"):
                content: str = file.read_text(encoding="utf-8", errors="ignore").lower()
                content = re.sub(r"^\s*title\s*=", "", content)
                content = re.sub(r"[^ a-z0-9\n\t]", "", content)
                content = re.sub(r"bibitem", "", content)
                content = re.sub(r"newblock", "", content)
                refs += content
            # too many broken bib files
            # elif file.suffix == ".bib":
            #     lib = bp.parse_file(str(file))
            #     for entry in lib.entries:
            #         for field in entry.fields:
            #             if field.key == "title":
            #                 refs += f"{entry['title']}\n"
        bibs.append((dir.name, refs))
        with open(bib_file, 'a') as f:
            f.write(refs)
    return bibs


def _get_cites(item: tuple[arXivId, str, list[str], dict[arXivId, Paper]]):
    citing_id, refs, titles, papers = item
    cites: list[tuple[arXivId, arXivId, str]] = []
    citing_year = int(citing_id[2:4])
    logger.info(f"processing citations for {citing_id}...")
    for cited_id, title in titles:
        if int(cited_id[2:4]) > citing_year + 3:
            continue
        if fuzz.partial_ratio(title, refs) > 95:
            cites.append((citing_id, cited_id, title))
            papers[citing_id].references.add(cited_id)
    return cites


def get_papers(dataset: Path, bibs: list[tuple[arXivId, str]]) -> dict[arXivId, Paper]:
    papers: dict[arXivId, Paper] = {}
    simple_titles: list[tuple[arXivId, str]] = []
    for p in tqdm(dataset.iterdir(), desc="Initializing papers"):
        papers[p.name] = Paper(
            (p / "title.txt").read_text(encoding="utf-8").strip(),
            (p / "abstract.txt").read_text(encoding="utf-8").strip(),
            set()
        )
        simple_titles.append((p.name, re.sub(r"[^ a-z0-9]", "", papers[p.name].title.lower())))

    logger.info("getting references...")
    jobs = [(id, bib, simple_titles, papers) for id, bib in bibs]
    with ProcessPoolExecutor(max_workers=6) as exe:
        for cites in tqdm(exe.map(_get_cites, jobs),
                          total=len(jobs),
                          desc="Getting references"):
            for citing_id, cited_id, simple_title in cites:
                logger.info(f"{logger.CYAN}arXiv:{citing_id:<10}{logger.RESET}"
                            f" cites {logger.MAGENTA}arXiv:{cited_id:<10}{logger.RESET}: "
                            f"{logger.YELLOW}{simple_title}{logger.RESET}")
    return papers


def main():
    args = parse_args()
    setup_logger(args.log)

    papers: dict[arXivId, Paper] = {}
    if args.data.is_dir():
        clean_dataset(args.data)
        if args.clean:
            return
        refs_files: list[tuple[arXivId, str]] = process_bibliographies(args.data)
        if args.preprocess:
            return
        papers = get_papers(args.data, refs_files)
    else:
        print(f"error: {args.data} is not a directory", file=sys.stderr)
        exit(1)

    if args.json:
        save_dataset(papers, args.output, args.json)
    else:
        save_dataset(papers, args.output)


if __name__ == "__main__":
    main()
