# CS 768 Assignment

### TL;DR

This is a standard python project with a `pyproject.toml`. Set up a virtual
environment and install the required packages.

To reproduce[^1] the report:

1. `mkdir data`
2. `curl -o data/dataset https://www.cse.iitb.ac.in/~adityas/cs768-assignment-dataset`
3. `curl -o data/embeddings https://www.cse.iitb.ac.in/~adityas/cs768-assignment-embeddings`
4. `python scripts/analyze_graph.py` (for [task 1](#task-1-build-a-citation-graph))
5. `typst compile report/master.typ --root .` will generate the report at
   `report/master.pdf`.
6. For task 2, the code is as per the assignment requirements.

### Setup

0. Install [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Other package managers are inferior in every way. They should probably
     work, but I will not test them.
1. Run `uv sync`.
2. Download the [dataset](https://drive.google.com/file/d/1J73io_KqCoPEAlH3teLWGoZ78yk5n7ll/view?usp=sharing).

### Preprocessing

Preprocess the assignment dataset using [`scripts/preprocess_dataset.py`](https://github.com/adityasz/cs768-assignment/blob/master/scripts/preprocess_dataset.py).
The preprocessed dataset is just a gzipped JSON file.

- Command-line reference:

  ```console
  $ uv run scripts/preprocess_dataset.py --help
  usage: preprocess_dataset.py [-h] [-d DATA] [-o OUTPUT] [--clean] [--preprocess] [--log [LOG]] [--json [JSON]]

  options:
    -h, --help           show this help message and exit
    -d, --data DATA      path to the assignment dataset (default: dataset_papers)
    -o, --output OUTPUT  path to store the processed dataset (default: data/dataset)
    --clean              stop after cleaning dataset
    --preprocess         stop after preprocessing dataset
    --log [LOG]          log to a fifo (the path is optional and defaults to /tmp/cs768-citations)
    --json [JSON]        save the dataset as json (the path is optional and defaults to data/dataset.json)
  ```

- The preprocessed dataset is available [here](https://www.cse.iitb.ac.in/~adityas/cs768-assignment-dataset).

### Task 1: Build a citation graph

[`scripts/analyze_graph.py`](https://github.com/adityasz/cs768-assignment/blob/master/scripts/analyze_graph.py) does everything required for this task.

- Command-line reference:

  ```console
  $ uv run scripts/analyze_graph.py --help
  usage: analyze_graph.py [-h] [-d DATA] [--stats STATS] [--in-hist IN_HIST] [--out-hist OUT_HIST]

  options:
    -h, --help           show this help message and exit
    -d, --data DATA      path to the preprocessed dataset (default: data/dataset)
    --stats STATS        path to save the statistics to (default: output/stats.json)
    --in-hist IN_HIST    path to save the in-degree histogram to (default: output/hist_in_deg.svg)
    --out-hist OUT_HIST  path to save the out-degree histogram to (default: output/hist_out_deg.svg)
  ```

### Task 2: Machine Learning

Generate embeddings using [`scripts/generate_embeddings.py`](https://github.com/adityasz/cs768-assignment/blob/master/scripts/generate_embeddings.py).

- Command-line reference:

  ```console
  $ uv run scripts/generate_embeddings.py --help
  usage: generate_embeddings.py [-h] [-d DATA] [-o OUTPUT] [--device DEVICE] [--batch-size BATCH_SIZE]

  options:
    -h, --help            show this help message and exit
    -d, --data DATA       path to the preprocessed dataset (default: data/dataset)
    -o, --output OUTPUT   path to save the embeddings (default: data/embeddings)
    --device DEVICE       device to use for generating embeddings
    --batch-size BATCH_SIZE
                          batch size to use for generating embeddings
  ```

- The generated embeddings are available [here](https://www.cse.iitb.ac.in/~adityas/cs768-assignment-embeddings).

The code for this task is organized as per the assignment requirements.

### Report

<details>
    <summary>Install Typst</summary>

- macOS: `brew install typst`

- Linux:
  - Install a Rust [toolchain](https://rustup.rs/) if you don't have it:

    ```console
    $ curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    ```

  - After adding `cargo` to `PATH`:

    ```console
    $ cargo install --git https://github.com/typst/typst --locked typst-cli
    ```
</details>

Run `typst compile report/master.typ --root .` to get the report at `report/master.pdf`.

  - If you overrode output paths in the scripts, pass the same flags to the
    compile command by appending `--input flag=value` for each flag. `root` has
    to be a common parent of all paths (and is `.` in the above command since
    all output is generated in `./output` by default).

    ```console
    $ typst compile report/master.typ --root /path/to/root                \
          --input stats=/path/to/root/a/stats                             \
          --input in-hist=/path/to/root/b/in_degree_histogram.[svg|png]   \
          --input out-hist=/path/to/root/c/out_degree_histogram.[svg|png]
    ```

[^1]: Note that the plots generated on your machine will look ugly unless you use
[this](https://github.com/adityasz/.dotfiles/blob/master/.config/matplotlib/matplotlibrc)
matplotlibrc and have its fonts installed. (Unfortunately, Typst does not have
an up-to-date matplotlib backend, and hence svg files have to be used, resulting
in stupid issues. Since Typst is not stable, backends written by the community
break on almost every update.)
