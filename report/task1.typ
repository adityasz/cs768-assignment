#import "template/report/lib.typ": *
#import "@preview/zero:0.3.3": ztable


= Build a citation graph

#let filename = "/output/stats.txt"
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
  caption: [
    Some #link("https://github.com/Ninyo97/cs768-2025-assignment/blob/2b5176f24d605124e98240bbc8b69fd5e95ebd8a/README.md?plain=1#L27")[statistics]
    of the citation graph.]
)

#let in_hist = "/output/hist_in_deg.svg"
#let out_hist = "/output/hist_out_deg.svg"
#let combined_hist = "/output/hist_deg.svg"
#if "in-hist" in sys.inputs.keys() {
  in_hist = "/" + sys.inputs.in-hist
}
#if "out-hist" in sys.inputs.keys() {
  out_hist = "/" + sys.inputs.out-hist
}
#if "combined-hist" in sys.inputs.keys() {
  combined_hist = "/" + sys.inputs.combined-hist
}

#for (filename, type) in (in_hist, out_hist, combined_hist).zip(("in", "out", "combined")) {
  [
    #let caption = [The distribution of the #type\-degree of the nodes in the
                    citation graph.]
    #if type == "combined" {
      caption = [The in- and out-degree distributions of the nodes in the
                 citation graph.]
    }
    #figure(
      image(filename, width: 6in),
      caption: caption
    ) #label("fig:" + "label" + "-deg-hist")
  ]
}
