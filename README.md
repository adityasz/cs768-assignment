# CS 768 Assignment

### TL;DR

This is a standard python project with a `pyproject.toml`. Set up a virtual environment and install the required
packages.

To reproduce the report:

1. `mkdir data`
2. `curl -o data/dataset.pkl https://www.cse.iitb.ac.in/~adityas/cs768-assignment-dataset` (unsafe)
3. `python scripts/analyze_graph.py`
4. TODO: Task 2
5. [`typst`](https://github.com/typst/typst)`compile report/master.typ --root .`
   will produce the report at `report/master.pdf`.

### Setup

0. Install [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Other package managers are inferior in every way. They should probably work, but I will not test them.
1. Run `uv sync`.
2. Download the [dataset](https://drive.google.com/file/d/1J73io_KqCoPEAlH3teLWGoZ78yk5n7ll/view?usp=sharing).

### Preprocessing

Preprocess the dataset with `uv run scripts/preprocess_data.py`.
  - Command-line reference:
    ```console
    $ uv run scripts/preprocess_data.py --help
    usage: preprocess_data.py [-h] [-d DATA] [-o OUTPUT] [--json JSON]

    options:
      -h, --help           show this help message and exit
      -d, --data DATA      The path to the assignment dataset (tarball or directory).
      -o, --output OUTPUT  The path to store the processed dataset.
      --json JSON          The path to store the processed dataset as json.
    ```
  - The preprocessed dataset is available
    [here](https://www.cse.iitb.ac.in/~adityas/cs768-assignment-dataset.pkl).

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
    to be a common parent of all paths.
  ```console
  $ typst compile report/master.typ --root /path/to/root                     \
        --input stats=/path/to/root/a/stats                                  \
        --input in-hist=/path/to/root/b/in_degree_histogram.[svg|png]        \
        --input out-hist=/path/to/root/c/out_degree_histogram.[svg|png]      \
        --input combined-hist=/path/to/root/d/out_degree_histogram.[svg|png] \
  ```
  Note that the plots generated on your machine will look ugly unless you use
  [this](https://github.com/adityasz/.dotfiles/blob/master/.config/matplotlib/matplotlibrc)
  matplotlibrc and have its fonts installed. (Unfortunately, Typst does not have
  an up-to-date matplotlib backend, and hence svg files have to be used,
  resulting in stupid issues. Since Typst is not stable, backends written by the
  community break on almost every update.)
