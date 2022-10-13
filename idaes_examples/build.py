"""
Build the examples
"""
import argparse
from enum import Enum
import json
import logging
from pathlib import Path
from subprocess import check_call
import sys
import time
import traceback
import webbrowser

# third-party
import yaml

# -------------
#   Logging
# -------------

_log = logging.getLogger("build")
_h = logging.StreamHandler()
_h.setFormatter(
    logging.Formatter("[%(levelname)s] %(asctime)s %(module)s - %(message)s")
)
_log.addHandler(_h)

NB_CELLS = "cells"  # key for list of cells in a Jupyter Notebook

# -------------
#  Preprocess
# -------------


class Tags(Enum):
    EX = "exercise"
    SOL = "solution"
    TUT = "tutorial"
    TEST = "testing"


def preprocess(srcdir=None):
    # Load table of contents from Jupyterbook
    src_path = Path(srcdir) if srcdir else Path(".")
    toc_path = src_path / "src" / "_toc.yml"
    if not toc_path.exists():
        raise FileNotFoundError(f"Could not find path: {toc_path}")
    with toc_path.open() as toc_file:
        toc = yaml.safe_load(toc_file)

    # Find and preprocess all notebooks in TOC
    t0, n = time.time(), 0
    for part in toc["parts"]:
        for chapter in part["chapters"]:
            for filemap in chapter["sections"]:
                filename = filemap["file"][:-4]  # strip "_doc" suffix
                path = src_path / f"src/{filename}.ipynb"
                if path.exists():
                    _preprocess(path)
                    n += 1

    dur = time.time() - t0
    _log.info(f"Preprocessed {n} notebooks in {dur:.1f} seconds")


# Which tags to exclude for which generated file
exclude_tags = {
    "test": {Tags.EX.value},
    "exercise": {Tags.TEST.value, Tags.SOL.value},
    "solution": {Tags.TEST.value},
    "doc": {Tags.EX.value, Tags.TEST.value},
}


def _preprocess(nb_path):
    _log.info(f"Preprocess: {nb_path}")
    t0 = time.time()

    # Load input file
    with nb_path.open() as nb_file:
        nb = json.load(nb_file)

    # Find cells to exclude
    had_tag = set()  # if tag occurred at all
    exclude_cells = {n: [] for n in exclude_tags}
    for cell_index, cell in enumerate(nb[NB_CELLS]):
        cell_tags = set(cell["metadata"].get("tags", []))
        for c in cell_tags:
            try:
                had_tag.add(Tags(c))
            except ValueError:  # not in Tags enum
                pass
        # Add cell to each notebook in which it should not be excluded
        for name, ex_tags in exclude_tags.items():
            if cell_tags & ex_tags:
                exclude_cells[name].insert(
                    0, cell_index
                )  # reverse order, so delete works

    # Wite output files
    nb_names = ["test", "doc"]
    is_tutorial = had_tag & {Tags.EX, Tags.SOL}
    if is_tutorial:
        nb_names.extend(["exercise", "solution"])
    for name in nb_names:
        # Generate notebook copy
        nb_copy = nb.copy()
        nb_copy[NB_CELLS] = nb[NB_CELLS].copy()
        for index in exclude_cells[name]:
            del nb_copy[NB_CELLS][index]  # indexes are in reverse order
        # Generate output file for copy
        nbcopy_path = nb_path.parent / f"{nb_path.stem}_{name}.ipynb"
        _log.debug(f"Generate '{name}' file: {nbcopy_path}")
        with nbcopy_path.open("w") as nbcopy_file:
            json.dump(nb_copy, nbcopy_file)

    dur = time.time() - t0
    _log.info(f"Prepocessed notebook {nb_path} in {dur:.2f} seconds")


# -------------
#  Jupyterbook
# -------------


def jupyterbook(srcdir=None):
    src_path = Path(srcdir) / "src"
    if not src_path.is_dir():
        raise FileNotFoundError(f"Could not find directory: {src_path}")
    check_call(["jupyter-book", "build", str(src_path)])


# -------------
#    View
# -------------


def view_docs(srcdir=None):
    docs_path = Path(srcdir) / "src" / "_build" / "html"
    if not docs_path.is_dir():
        raise FileNotFoundError(f"Could not find directory: {docs_path}")

    url = docs_path.absolute().as_uri() + "/index.html"
    webbrowser.open_new(url)
    return 0


# -------------
#  Commandline
# -------------


class Commands:
    @classmethod
    def pre(cls, args):
        cls.heading("Pre-process notebooks")
        return cls._run("pre-process notebooks", preprocess, srcdir=args.dir)

    @classmethod
    def build(cls, args):
        cls.heading("Build Jupyterbook")
        return cls._run("build jupyterbook", jupyterbook, srcdir=args.dir)

    @classmethod
    def view(cls, args):
        cls.heading("View Jupyterbook documentation")
        return cls._run("view jupyterbook", view_docs, srcdir=args.dir)

    @staticmethod
    def _run(name, func, **kwargs):
        try:
            func(**kwargs)
        except FileNotFoundError as err:
            _log.error(f"During '{name}': {err}")
            _log.error(
                "Check that your working or `-d/--dir` directory contains the Jupyter "
                "source notebooks"
            )
            return -2
        except Exception as err:
            _log.error(f"During '{name}': {err}")
            _log.error(traceback.format_exc())
            return -1

    @staticmethod
    def heading(message):
        print(f"-> {message}")


def add_vb(p, dest="vb"):
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        dest=dest,
        default=0,
        help="Increase verbosity",
    )


def process_vb(vb):
    if vb >= 2:
        _log.setLevel(logging.DEBUG)
    elif vb == 1:
        _log.setLevel(logging.INFO)
    else:
        _log.setLevel(logging.WARNING)


def main():
    p = argparse.ArgumentParser()
    add_vb(p)
    commands = p.add_subparsers(
        title="Commands", help="Commands to run", required=True, dest="command"
    )
    subp = {}
    for name, desc in (
        ("pre", "Pre-process notebooks"),
        ("build", "Build Jupyterbook"),
        ("view", "View Jupyterbook"),
    ):
        subp[name] = commands.add_parser(name, help=desc)
        subp[name].add_argument(
            "-d", "--dir", help="Source directory (default=<current>)", default="."
        )
        add_vb(subp[name], dest=f"vb_{name}")
    args = p.parse_args()
    subvb = getattr(args, f"vb_{args.command}")
    if subvb != args.vb:
        process_vb(subvb)
    else:
        process_vb(args.vb)
    func = getattr(Commands, args.command, None)
    if func is None:
        p.print_help()
        sys.exit(0)
    else:
        sys.exit(func(args))


if __name__ == "__main__":
    main()
