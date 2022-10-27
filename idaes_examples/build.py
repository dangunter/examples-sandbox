"""
Build the examples
"""
import argparse
from enum import Enum
import json
import logging
from pathlib import Path
import shutil
from subprocess import check_call
import sys
import time
import traceback
from typing import Callable, Dict
import webbrowser

# third-party
import yaml

# package
from idaes_examples.util import add_vb, process_vb, allow_repo_root, NB_ROOT

# -------------
#   Logging
# -------------

_log = logging.getLogger(__name__)
_h = logging.StreamHandler()
_h.setFormatter(
    logging.Formatter("[%(levelname)s] %(asctime)s %(module)s - %(message)s")
)
_log.addHandler(_h)

NB_CELLS = "cells"  # key for list of cells in a Jupyter Notebook

# -------------
#  Preprocess
# -------------

test_path, src_path = None, None
src_suffix = "_src"
src_suffix_len = 4


class Tags(Enum):
    EX = "exercise"
    SOL = "solution"
    TEST = "testing"


class Ext(Enum):
    DOC = "doc"
    EX = "exercise"
    SOL = "solution"
    TEST = "test"


def preprocess(srcdir=None):
    global test_path, src_path

    src_path = allow_repo_root(Path(srcdir), main)
    src_path /= NB_ROOT
    test_path = src_path / "tests"

    toc = read_toc(src_path)

    t0 = time.time()
    n = find_notebooks(src_path, toc, _preprocess)
    dur = time.time() - t0
    _log.info(f"Preprocessed {n} notebooks in {dur:.1f} seconds")

    return n


def read_toc(src_path: Path) -> Dict:
    """Read and parse Jupyterbook table of contents.

    Args:
        src_path: Path to source directory containing TOC file

    Returns:
        Parsed TOC contents

    Raises:
        FileNotFoundError: If TOC file does not exist
    """
    toc_path = src_path / "_toc.yml"
    if not toc_path.exists():
        raise FileNotFoundError(f"Could not find path: {toc_path}")
    with toc_path.open() as toc_file:
        toc = yaml.safe_load(toc_file)
    return toc


def find_notebooks(
    nbpath: Path, toc: Dict, callback: Callable[[Path, ...], None], **kwargs
) -> int:
    """Find and preprocess all notebooks in a Jupyterbook TOC.

    Args:
        nbpath: Path to root of notebook files
        toc: Table of contents from Jupyterbook
        callback: Function called for each found notebook, with the path to that
                  notebook as its first argument.
        **kwargs: Additional arguments passed through to the callback

    Returns:
        Number of notebooks processed
    """
    n = 0
    for part in toc["parts"]:
        for chapter in part["chapters"]:
            for filemap in chapter["sections"]:
                filename = filemap["file"][:-4]  # strip "_doc" suffix
                filename += src_suffix
                path = nbpath / f"{filename}.ipynb"
                if path.exists():
                    callback(path, **kwargs)
                    n += 1
                else:
                    raise FileNotFoundError(f"Could not find notebook at: {path}")
    return n


# Which tags to exclude for which generated file
exclude_tags = {
    Ext.TEST.value: {Tags.EX.value},
    Ext.EX.value: {Tags.TEST.value, Tags.SOL.value},
    Ext.SOL.value: {Tags.TEST.value},
    Ext.DOC.value: {Tags.EX.value, Tags.TEST.value},
}


def _preprocess(nb_path: Path, **kwargs):
    _log.info(f"Preprocess: {nb_path}")
    t0 = time.time()

    # Load input file
    with nb_path.open('r', encoding='utf-8') as nb_file:
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
    nb_names = [Ext.TEST.value, Ext.DOC.value]
    is_tutorial = had_tag & {Tags.EX, Tags.SOL}
    if is_tutorial:
        nb_names.extend([Ext.EX.value, Ext.SOL.value])
    for name in nb_names:
        # Generate notebook copy
        nb_copy = nb.copy()
        nb_copy[NB_CELLS] = nb[NB_CELLS].copy()
        for index in exclude_cells[name]:
            del nb_copy[NB_CELLS][index]  # indexes are in reverse order
        # Generate output file for copy
        # if name == Ext.TEST.value:
        #     output_dir = test_path / nb_path.parent.relative_to(src_path)
        #     output_dir.mkdir(parents=True, exist_ok=True)
        #     # copy support files (assume flat: no directories!)
        #     for pattern in "*.py", "*.csv", "*.json", "*.yaml":
        #         for support_file in nb_path.parent.glob(pattern):
        #             shutil.copy(support_file, output_dir / support_file.name)
        #     output_name = nb_path.name
        # else:
        output_dir = nb_path.parent
        base_name = nb_path.stem[:-src_suffix_len]
        output_name = f"{base_name}_{name}.ipynb"
        nbcopy_path = output_dir / output_name
        _log.debug(f"Generate '{name}' file: {nbcopy_path}")
        with nbcopy_path.open("w") as nbcopy_file:
            json.dump(nb_copy, nbcopy_file)

    dur = time.time() - t0
    _log.info(f"Prepocessed notebook {nb_path} in {dur:.2f} seconds")


# -------------
#  Jupyterbook
# -------------


def jupyterbook(srcdir=None):
    path = allow_repo_root(Path(srcdir), main)
    path /= NB_ROOT
    if not path.is_dir():
        raise FileNotFoundError(f"Could not find directory: {path}")
    check_call(["jupyter-book", "build", str(path)])


# -------------
#    View
# -------------


def view_docs(srcdir=None):
    docs_path = Path(srcdir) / NB_ROOT / "_build" / "html"
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
        if not args.no_pre:
            cls.heading("Pre-process notebooks")
            cls._run("pre-process notebooks", preprocess, srcdir=args.dir)
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
    subp["build"].add_argument(
        "--no-pre", action="store_true", help="skip pre-processing", default=False,
    )
    args = p.parse_args()
    subvb = getattr(args, f"vb_{args.command}")
    if subvb != args.vb:
        process_vb(_log, subvb)
    else:
        process_vb(_log, args.vb)
    func = getattr(Commands, args.command, None)
    if func is None:
        p.print_help()
        sys.exit(0)
    else:
        sys.exit(func(args))


if __name__ == "__main__":
    main()
