# Ran with Jupyter REPL; bad code; meant for internal testing
# %%
import torch
import torch.nn.functional as F
from adapters import AutoAdapterModel
from transformers import AutoTokenizer

from cglp.data import load_dataset, arXivId

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# %%

dataset = load_dataset("../data/dataset")
# %%

tokenizer = AutoTokenizer.from_pretrained("allenai/specter2_base")
specter2_model = AutoAdapterModel.from_pretrained("allenai/specter2_base")
specter2_model.load_adapter("allenai/specter2", source="hf", load_as="specter2", set_active=True)
specter2_model = specter2_model.to(device)
# %%
idx_to_arxiv_id: dict[int, arXivId] = {id: arxiv_id
                                       for id, arxiv_id in enumerate(sorted(dataset.keys()))}
arxiv_idx_to_id = {arxiv_id: id for id, arxiv_id in enumerate(sorted(dataset.keys()))}
data: dict[int, tuple[str, str, set[int]]] = {
    arxiv_idx_to_id[arxiv_id]: (
        paper.title, paper.abstract, set(arxiv_idx_to_id[cited_id] for cited_id in paper.references)
    )
    for arxiv_id, paper in dataset.items()
}
nodes: list[str] = [title + tokenizer.sep_token + abstract
                    for _, (title, abstract, _) in sorted(data.items())]
edges = [(u, v)
         for u, (title, abstract, refs) in data.items()
         for v in refs]
# %%

embeddings = torch.load("data/embeddings")
# %%

K = 50
# M = 1000
# recalls = []
# running_mean = 0.0
# idxs = torch.randint(0, len(dataset), (M,)).tolist()
# for idx in idxs:
#     if idx % 200:
#         print(running_mean)
#     refs = data[idx][2]
#     if not refs:
#         continue
#     sims = F.cosine_similarity(
#         embeddings.to(device),
#         embeddings[idx].to(device).unsqueeze(0),
#         dim=1
#     )
#     sims[idx] = -1.0
#     topk = sims.topk(K).indices.cpu().tolist()
#     recall = len(set(topk) & refs) / len(refs)
#     recalls.append(recall)
#     running_mean = running_mean * 0.99 + recall * 0.01
# recalls = torch.tensor(recalls)
# print(f"Mean Recall: {recalls.mean():.4f}")
# %%

idx = 1797
print(idx_to_arxiv_id[idx])
# %%
sims = F.cosine_similarity(
    embeddings.to(device),
    embeddings[idx].to(device).unsqueeze(0),
    dim=1
)
sims[idx] = -1.0
topk = sims.topk(K).indices.cpu().tolist()
print([idx_to_arxiv_id[idx] for idx in topk])
refs = data[idx][2]
recall = len(set(topk) & refs) / len(refs)
print(recall)
