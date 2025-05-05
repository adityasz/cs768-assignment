import argparse
from pathlib import Path

import torch
from adapters import AutoAdapterModel
from transformers import AutoTokenizer
from tqdm import tqdm

from cglp.data import Paper, arXivId, load_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", type=Path, default="data/dataset",
                        help="path to the preprocessed dataset (default: data/dataset).")
    parser.add_argument("-o", "--output", type=Path, default="data/embeddings",
                        help="path to save the embeddings (default: data/embeddings).")
    parser.add_argument("--device", type=torch.device, default="cuda",
                        help="device to use for generating embeddings")
    parser.add_argument("--batch-size", type=int, default=128,
                        help="batch size to use for generating embeddings")
    return parser.parse_args()


def generate_embeddings(
    dataset: dict[arXivId, Paper],
    device: torch.device,
    batch_size: int
) -> torch.Tensor:
    """Generate embeddings for the nodes in the given citation graph."""
    tokenizer = AutoTokenizer.from_pretrained("allenai/specter2_base")
    model = AutoAdapterModel.from_pretrained("allenai/specter2_base")
    model.load_adapter("allenai/specter2", source="hf", load_as="specter2", set_active=True)
    model = model.to(device)

    nodes: list[str] = [paper.title + tokenizer.sep_token + paper.abstract
                        for _, paper in sorted(dataset.items())]

    embeddings = torch.zeros((len(nodes), 768))
    for i in tqdm(range(0, len(nodes), batch_size)):
        batch_data = nodes[i:i + batch_size]
        inputs = tokenizer(batch_data, padding=True, truncation=True, return_tensors="pt",
                           return_token_type_ids=False, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
        batch_embeddings = outputs.last_hidden_state[:, 0, :]
        embeddings[i : i + len(batch_data)] = batch_embeddings.cpu()
    return embeddings


def main():
    args = parse_args()

    dataset: dict[arXivId, Paper] = load_dataset(args.data)

    embeddings = generate_embeddings(dataset, args.device, args.batch_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(embeddings, args.output)


if __name__ == "__main__":
    main()
