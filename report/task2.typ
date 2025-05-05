#import "template/report/lib.typ": *


= Machine learning

For citation prediction, I looked up several papers to get an idea of how to
approach this problem. There were several different approaches, and
@citation-recommendation achieves good results. They first do a nearest neighbor
search based on the embeddings of the papers (prefetching stage), and then use a
SciBERT based model to rerank the initial list. However, they also utilized
local citation context, and that is not available in this assignment's dataset.
Also, this assignment's dataset is very small -- it contains only titles and
abstracts, and training the network in @citation-recommendation wouldn't give
good results.

I tried training different GNNs, but to train a large transformer based model to
get initial features from the titles and abstracts requires a large dataset.
Also, @citation-recommendation itself uses SciBERT for reranking. So, I compared
several open source models from hugging face to get the initial features and
found SPECTER2 @specter-2 to be good (no rigorous testing was done, just a
handful of comparisons on the given dataset were made). I then generated
the initial embeddings and trained a GATv2-like network @gatv2. I trained it with
different positive- and negative-edge sampling ratios, but the recall at $K$ was
very low. Adding heuristics to rerank (like most cited among top-$N$, where I
would hope that the unknown $K > N$, etc.) did not help.

Simply returning the top-$K$ papers based on the cosine similarities of their
embeddings with the query paper resulted in a recall at $50$ of $~0.38$. I could
not beat this with heuristics or GNN -- though I did not have much time to try
because of other assignments and time constraints (maybe the GNN had a bug in
the sampling).

The code to generate embeddings is available in #link("https://github.com/adityasz/cs768-assignment/blob/master/scripts/generate_embeddings.py")[`scripts/generate_embeddings.py`].
