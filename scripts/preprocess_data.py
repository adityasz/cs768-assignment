import argparse
import logging
import os
import sys
import tarfile

from pathlib import Path
from tempfile import TemporaryDirectory
from tqdm import tqdm

from cglp.data import Paper, save_dataset


NUM_PAPERS: int = 6545
"""TODO: Remove when API call written"""

paperId = str
"""The unique identifier for a paper assigned by Semantic Scholar."""
arXivId = str
"""The unique identifier for a paper assigned by arXiv."""
logger = logging.getLogger()


def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", type=Path, default="dataset_papers.tar.gz",
                        help="path to the assignment dataset tarball or directory "
                             "(default: dataset_papers.tar.gz)")
    parser.add_argument("-o", "--output", type=Path, default="data/dataset",
                        help="path to store the processed dataset "
                             "(default: data/dataset)")
    parser.add_argument("--json", nargs='?', const=Path("data/dataset.json"),
                        help="save the dataset as json "
                             "(the path is optional and defaults to data/dataset.json)")
    return parser.parse_args()


class ReferencesNotComplete(Exception):
    """TODO"""
    def __init__(self, value: paperId):
        self.value: paperId = value
        super().__init__(f"References not complete for {value}")


def get_ids_references(
    batch: list[arXivId]
) -> tuple[dict[arXivId, paperId], dict[paperId, set[paperId]]]:
    """TODO: Make real API call"""
    try:
        get_ids_references.counter      # type: ignore
    except AttributeError:
        get_ids_references.counter = 0  # type: ignore
    paper_ids: list[paperId] = [
        str(id)
        for id in list(range(get_ids_references.counter,                # type: ignore
                             get_ids_references.counter + len(batch)))  # type: ignore
    ]
    arxiv_id_to_paper_id: dict[arXivId, paperId] = {
        aid: pid for (aid, pid) in zip(batch, paper_ids)
    }
    references: dict[paperId, set[paperId]] = {pid: set() for pid in paper_ids}
    import numpy as np
    for pid in paper_ids:
        references[pid] = set(
            str(x)
            for x in np.random.choice(NUM_PAPERS, np.random.randint(7, 50), replace=False)
            if str(x) != pid
        )
    get_ids_references.counter += len(batch)  # type: ignore
    return arxiv_id_to_paper_id, references


def get_papers(ta_dataset: Path) -> dict[paperId, Paper]:
    """TODO"""
    papers: dict[paperId, Paper] = {}

    arxiv_ids: list[arXivId] = os.listdir(ta_dataset)
    batch_size: int = 100
    num_arxiv_ids = len(arxiv_ids)
    num_batches = (num_arxiv_ids + batch_size - 1) // batch_size

    for batch_idx in tqdm(range(num_batches), desc="Processing batches"):
        i = batch_idx * batch_size
        batch = arxiv_ids[i : i + batch_size]
        arxiv_id_to_paper_id, references = get_ids_references(batch)
        for arxiv_id in batch:
            with open(ta_dataset/arxiv_id/"title.txt", 'r') as f:
                title: str = f.read()
            with open(ta_dataset/arxiv_id/"abstract.txt", 'r') as f:
                abstract: str = f.read()
            paper_id = arxiv_id_to_paper_id[arxiv_id]
            papers[paper_id] = Paper(title, abstract, arxiv_id, references[paper_id])

    for paper in papers.values():
        for paper_id in paper.references.copy():
            if paper_id not in papers.keys():
                paper.references.remove(paper_id)

    return papers


def main():
    args = parse_args()
    logging.basicConfig()  # TODO

    papers: dict[paperId, Paper] = {}
    if os.path.isdir(args.data):
        papers = get_papers(args.data)
    elif tarfile.is_tarfile(args.data):
        with tarfile.open(args.data, mode='r') as tar:
            with TemporaryDirectory() as tmpdir:
                tar.extractall(path=tmpdir, filter="data")
                papers = get_papers(tmpdir/Path("dataset_papers"))
    else:
        print(f"Error: {args.data} is neither a tarball nor a directory", file=sys.stderr)

    if args.json:
        save_dataset(papers, args.output, args.json)
    else:
        save_dataset(papers, args.output)


if __name__ == "__main__":
    main()
