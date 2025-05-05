import argparse

################################################
#               IMPORTANT                      #
################################################
# 1. Do not print anything other than the ranked list of papers.
# 2. Do not forget to remove all the debug prints while submitting.




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-paper-title", type=str, required=True)
    parser.add_argument("--test-paper-abstract", type=str, required=True)
    args = parser.parse_args()

    # print(args)

    ################################################
    #               YOUR CODE START                #
    ################################################
    import torch
    from adapters import AutoAdapterModel
    from torch.nn.functional import cosine_similarity
    from transformers import AutoTokenizer
    from cglp.data import arXivId, load_dataset

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = load_dataset("data/dataset")
    embeddings: torch.Tensor = torch.load("data/embeddings")
    idx_to_arxiv_id: dict[int, arXivId] = {id: arxiv_id
                                           for id, arxiv_id in enumerate(sorted(dataset.keys()))}

    tokenizer = AutoTokenizer.from_pretrained("allenai/specter2_base")
    model = AutoAdapterModel.from_pretrained("allenai/specter2_base")
    model.load_adapter("allenai/specter2", source="hf", load_as="specter2", set_active=True)
    model = model.to(device)

    input = tokenizer([args.test_paper_title + tokenizer.sep_token + args.test_paper_abstract],
                      padding=True, truncation=True, return_tensors="pt",
                      return_token_type_ids=False, max_length=512)
    input = {k: v.to(device) for k, v in input.items()}
    with torch.no_grad():
        output = model(**input)
    embedding = output.last_hidden_state[:, 0, :]

    # prepare a ranked list of papers like this:
    # result = ['paper1', 'paper2', 'paper3', 'paperK']  # Replace with your actual ranked list

    sims = cosine_similarity(embeddings.to(device), embedding.to(device), dim=1)
    result = [idx_to_arxiv_id[idx] for idx in torch.argsort(sims, descending=True).tolist()]

    ################################################
    #               YOUR CODE END                  #
    ################################################



    ################################################
    #               DO NOT CHANGE                  #
    ################################################
    print('\n'.join(result))

if __name__ == "__main__":
    main()
