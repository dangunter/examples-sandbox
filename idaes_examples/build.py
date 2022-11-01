"""
Build the examples
"""
import argparse
import json
import logging
from pathlib import Path
import re
from subprocess import check_call
import sys
import time
import traceback
import webbrowser

# package
from idaes_examples.common import (
    add_vb,
    process_vb,
    allow_repo_root,
    NB_ROOT,
    NB_CELLS,
    read_toc,
    find_notebooks,
    src_suffix,
    src_suffix_len,
    Ext,
    Tags
)
from idaes_examples import browse

# -------------
#   Logging
# -------------

_log = logging.getLogger(__name__)
_h = logging.StreamHandler()
_h.setFormatter(
    logging.Formatter("[%(levelname)s] %(asctime)s %(module)s - %(message)s")
)
_log.addHandler(_h)

# -------------
#  Preprocess
# -------------

DEV_DIR = "_dev"  # special directory to include in preprocessing


def preprocess(srcdir=None):
    src_path = allow_repo_root(Path(srcdir), main)
    src_path /= NB_ROOT
    toc = read_toc(src_path)
    t0 = time.time()
    n = find_notebooks(src_path, toc, _preprocess)
    for dev_file in (src_path / DEV_DIR).glob(f"*{src_suffix}.ipynb"):
        _preprocess(dev_file)
    dur = time.time() - t0
    _log.info(f"Preprocessed {n} notebooks in {dur:.1f} seconds")
    return n


# Which tags to exclude for which generated file
exclude_tags = {
    Ext.TEST.value: {Tags.EX.value, Tags.NOAUTO.value},
    Ext.EX.value: {Tags.TEST.value, Tags.SOL.value, Tags.AUTO.value},
    Ext.SOL.value: {Tags.TEST.value, Tags.AUTO.value},
    Ext.DOC.value: {Tags.TEST.value, Tags.NOAUTO.value},
    Ext.USER.value: {Tags.TEST.value, Tags.AUTO.value}  # same as _solution
}

# notebook filenames, e.g. in markdown links
# NOTE: assume no spaces in filenames
nb_file_pat = re.compile(f"([a-zA-Z0-9_\\-:.+]+){src_suffix}\\.ipynb")
nb_file_subs = {e.value: f"\\1_{e.value}.ipynb" for e in Ext if e != Ext.DOC}
# For MyST, replace .ipynb with .md in the 'doc' notebook's link
nb_file_subs[Ext.DOC.value] = f"\\1_{Ext.DOC.value}.md"


def _preprocess(nb_path: Path, **kwargs):
    _log.info(f"Preprocess: {nb_path}")
    t0 = time.time()

    # Load input file
    with nb_path.open("r", encoding="utf-8") as nb_file:
        nb = json.load(nb_file)

    # Get cells to exclude, also ones with notebook xrefs
    had_tag = set()  # if tag occurred at all
    exclude_cells = {n: [] for n in exclude_tags}
    xref_cells = {}  # {cell-index: [list of line indexes]}
    for cell_index, cell in enumerate(nb[NB_CELLS]):
        # Get tags for cell
        cell_tags = set(cell["metadata"].get("tags", []))
        for c in cell_tags:
            try:
                had_tag.add(Tags(c))
            except ValueError:  # not in Tags enum
                pass
        # Potentially add to lists of excluded cells
        for name, ex_tags in exclude_tags.items():
            if cell_tags & ex_tags:
                # add in reverse order to make delete easier
                exclude_cells[name].insert(0, cell_index)
        # Look for (and save) lines with cross references
        xref_lines = [
            i for i, line in enumerate(cell["source"]) if nb_file_pat.search(line)
        ]
        if xref_lines:
            xref_cells[cell_index] = xref_lines

    # Write output files

    nb_names = [Ext.TEST.value, Ext.DOC.value, Ext.USER.value]
    is_tutorial = had_tag & {Tags.EX, Tags.SOL}
    if is_tutorial:
        nb_names.extend([Ext.EX.value, Ext.SOL.value])

    for name in nb_names:
        nb_copy = nb.copy()
        nb_copy[NB_CELLS] = nb[NB_CELLS].copy()
        # Fix (any) cross-references to use current file extension ('name')
        saved_source = []  # save (index, orig-source) for all changed cells
        for cell_index, cell in enumerate(nb_copy[NB_CELLS]):
            if cell_index not in xref_cells or cell_index in exclude_cells[name]:
                continue
            cs = cell["source"]  # alias
            saved_source.append((cell_index, cs.copy()))  # save orig
            for line_index in xref_cells[cell_index]:
                subst = nb_file_pat.sub(nb_file_subs[name], cs[line_index])
                cs[line_index] = subst
        # Delete excluded cells
        for index in exclude_cells[name]:
            del nb_copy[NB_CELLS][index]  # indexes are in reverse order
        # Generate output file
        output_dir = nb_path.parent
        base_name = nb_path.stem[:-src_suffix_len]
        output_name = f"{base_name}_{name}.ipynb"
        nbcopy_path = output_dir / output_name
        _log.debug(f"Generate '{name}' file: {nbcopy_path}")
        with nbcopy_path.open("w") as nbcopy_file:
            json.dump(nb_copy, nbcopy_file)
        # Restore modified sources
        for i, s in saved_source:
            nb[NB_CELLS][i]["source"] = s

    dur = time.time() - t0
    _log.info(f"Prepocessed notebook {nb_path} in {dur:.2f} seconds")


# -------------
# Clean
# -------------


def clean(srcdir=None):
    src_path = allow_repo_root(Path(srcdir), main) / NB_ROOT
    toc = read_toc(src_path)
    find_notebooks(src_path, toc, _clean)


def _clean(nb_path: Path, **kwargs):
    """Remove generated files"""
    nb_names = [Ext.TEST.value, Ext.DOC.value, Ext.EX.value, Ext.SOL.value]
    for name in nb_names:
        base_name = nb_path.stem[:-src_suffix_len]
        gen_name = f"{base_name}_{name}.ipynb"
        gen_path = nb_path.parent / gen_name
        if gen_path.exists():
            _log.debug(f"Remove generated file '{gen_path}'")
            gen_path.unlink()


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
    src_path = allow_repo_root(Path(srcdir), main) / NB_ROOT
    docs_path = src_path / "_build" / "html"
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

    @classmethod
    def clean(cls, args):
        cls.heading("Remove generated notebooks")
        return cls._run("remove generated notebooks", clean, srcdir=args.dir)

    @classmethod
    def gui(cls, args):
        browse._log.setLevel(_log.getEffectiveLevel())
        nb = browse.Notebooks()
        if args.console:
            for val in nb._sorted_values:
                pth = Path(val.path).relative_to(Path.cwd())
                print(f"{val.type}{' '*(10 - len(val.type))} {val.title} -> {pth}")
            status = 0
        else:
            _log.info(f"Run GUI start")
            status = browse.gui(nb)
            _log.info(f"Run GUI end")
        return status

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
        ("clean", "Remove generated files"),
        ("gui", "Graphical notebook browser"),
    ):
        subp[name] = commands.add_parser(name, help=desc)
        subp[name].add_argument(
            "-d", "--dir", help="Source directory (default=<current>)", default="."
        )
        add_vb(subp[name], dest=f"vb_{name}")
    subp["build"].add_argument(
        "--no-pre",
        action="store_true",
        help="skip pre-processing",
        default=False,
    )
    subp["gui"].add_argument("--console", action="store_true", dest="console")
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
