#import "template/report/lib.typ": *
#import "@preview/zero:0.3.3": ztable


= Build a citation graph

`*.bbl` files do not follow a standard spec. It is impossible to parse them
reliably. A large number of the `*.bib` files were also "broken". So, I first
tried to use #link("https://www.semanticscholar.org/")[Semantic Scholar]'s
Academic Graph API -- the code for this is in
#link("https://github.com/adityasz/cs768-assignment/blob/master/scripts/create_dataset_semantic_scholar.py")[`scripts/create_dataset_semantic_scholar.py`].

They have a huge dataset that contains the references of essentially every
paper. They block IITB LAN (at least the public IP of Hostel 3 is blocked), but
Eduroam works (I am responsible and added sufficient time delay between calls so
as to not get rate limited: The block is due to someone else). They also support
batched API calls: With a batch of 300 papers, only $~22$ API calls (5 seconds
apart) are enough to fetch everything. The only problem is that their references
lists are incomplete, and it identifies only $~18 thin 000$ edges in the given
dataset.

#link("https://openalex.org/")[OpenAlex] also claims to have a graph database.
Their #link("https://docs.openalex.org/api-entities/works")[`Work`] object has a
#link("https://docs.openalex.org/api-entities/works/work-object#referenced_works")[`referenced_works`]
list that consists of citations going _from_ one work _to_ another work. The
problem here is that `referenced_works` is empty for every paper I looked up.

So, I had to manually parse `.bbl` files. I did the following:

+ Make everything lowercase.
+ Remove all characters not in the class `[^ a-z0-9\n\t]`.
+ Remove `bititem` and `newblock` from all `*.bbl` files.
+ For `bib` files that are not broken, just extract the titles.
+ Combine the preprocessed data form all the `.bib` and `.bbl` files of each
  paper into one file named `super_simple_refs.txt`.

Now, for each arXiv ID, I fuzzy searched every other arXiv ID in its
`super_simple_refs.txt`. #link("https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html#partial-ratio")[`rapidfuzz.fuzz.partial_ratio`]
with a threshold of 95 was used. Search was done in parallel across 6 cores
(laptops have thermal constraints and they can only run a small number of cores
at a high frequency -- using more cores does not help beyond a certain amount,
depending on the task and the heat sink's heat dissipation capacity).

The code for this is in #link("https://github.com/adityasz/cs768-assignment/blob/master/scripts/preprocess_dataset.py")[`scripts/preprocess_dataset.py`].

The data was preprocessed into a ```python dict[arXivId, Paper]```, where
```python arXivId = str``` and `Paper` is a ```dataclass``` with the following
structure:

```python
from dataclasses import dataclass


@dataclass
class Paper:
    title: str
    """The title of the paper."""
    abstract: str
    """The abstract of the paper."""
    references: set[arXivId]
    """The arXiv IDs of the papers that this paper cites."""
```

The dataset is stored as a gzipped JSON file. NetworkX was then used to build a
directed graph based on the references. The code for this is in
#link("https://github.com/adityasz/cs768-assignment/blob/master/scripts/analyze_graph.py")[`scripts/analyze_graph.py`].
The statistics are in @tab:stats. The (log-scale) histograms of the in- and
out-degrees are in @fig:in-deg-hist and @fig:out-deg-hist.


#let filename = "/output/stats.json"
#if "stats" in sys.inputs.keys() {
  filename = "/" + sys.inputs.stats
}
#let stats = json(filename)
#let keys = (
  "num_edges": [Number of edges],
  "num_isolated_nodes": [Number of isolated nodes],
  "avg_node_deg": [Average node degree],
  "diameter": [Diameter]
)
#figure(
  align(center)[
    #ztable(
      stroke: none,
      columns: 2,
      format: (none, auto),
      align: (left, auto),
      table.hline(stroke: 1pt),
      table.vline(x: 1, stroke: 1pt),
      ..for (key, header) in keys {
        let cols = (header, [])
        if key == "avg_node_deg" {
          cols.at(1) = [#calc.round(float(stats.at(key)), digits: 2)]
        } else {
          cols.at(1) = [#int(stats.at(key))]
        }
        cols
      },
      table.hline(stroke: 1pt),
    )
  ],
  supplement: [Table],
  caption: [Some statistics of the citation graph.]
) <tab:stats>

#let in_hist = "/output/hist_in_deg.svg"
#let out_hist = "/output/hist_out_deg.svg"
#if "in-hist" in sys.inputs.keys() {
  in_hist = "/" + sys.inputs.in-hist
}
#if "out-hist" in sys.inputs.keys() {
  out_hist = "/" + sys.inputs.out-hist
}

#for (filename, type) in (in_hist, out_hist).zip(("in", "out")) {
  [
    #let caption = [The distribution of the #type\-degree of the nodes in the
                    citation graph.]
    #figure(
      image(filename, width: 6in),
      caption: caption
    ) #label("fig:" + type + "-deg-hist")
  ]
}

#pagebreak()
