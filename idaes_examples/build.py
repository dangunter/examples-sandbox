"""
Build the examples
"""
import argparse
import json
import logging
from pathlib import Path
from subprocess import check_call
import sys
import traceback

import yaml

_log = logging.getLogger("build")
_h = logging.StreamHandler()
_h.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s"))
_log.addHandler(_h)
_log.setLevel(logging.DEBUG)


def _run(name, func):
    try:
        func()
    except Exception as err:
        _log.error(f"During '{name}': {err}")
        _log.error(traceback.format_exc())
        return -1


def preprocess():
    toc_path = Path("src") / "_toc.yml"
    with toc_path.open() as toc_file:
        toc = yaml.safe_load(toc_file)
    for part in toc["parts"]:
        for chapter in part["chapters"]:
            for filemap in chapter["sections"]:
                filename = filemap["file"][:-4]  # strip "_doc" suffix
                path = Path(f"src/{filename}.ipynb")
                if path.exists():
                    _preprocess(path)


# Which tags to exclude for which generated file
exclude_tags = {
    "test": {"exercise"},
    "exercise": {"testing", "solution"},
    "solution": {"testing"},
    "doc": {"exercise", "testing"},
}


def _preprocess(nb_path):
    _log.info(f"Preprocess: {nb_path}")
    # Load input file
    with nb_path.open() as nb_file:
        nb = json.load(nb_file)
    is_tutorial = False
    # Process each type of generated file
    for name, tags in exclude_tags.items():
        _log.debug(f"Preprocess for '{name}'")
        # Create copy of input, with no cells
        nbcopy = {
            "nbformat": nb["nbformat"],
            "nbformat_minor": nb["nbformat_minor"],
            "metadata": nb["metadata"],
            "cells": [],
        }
        # Add cells that are not excluded for this type of file
        for cell in nb["cells"]:
            cell_tags = set(cell["metadata"].get("tags", []))
            if not is_tutorial and ("exercise" in cell_tags or "solution" in cell_tags):
                is_tutorial = True
            if not (cell_tags & tags):
                cell["metadata"]["tags"] = []
                nbcopy["cells"].append(cell)
        # Skip tutorial files if not a tutorial
        if not is_tutorial and name in ("exercise", "solution"):
            _log.debug(f"Do not generate '{name}' file: not a tutorial")
            continue
        # Generate output file
        nbcopy_path = nb_path.parent / f"{nb_path.stem}_{name}.ipynb"
        _log.debug(f"Generate '{name}' file: {nbcopy_path}")
        with nbcopy_path.open("w") as nbcopy_file:
            json.dump(nbcopy, nbcopy_file)


def jupyterbook():
    check_call(["jupyter-book", "build", "src"])


def banner(message, top=False):
    prefix = ">" if top else ">>"
    print(f"-{prefix} {message}")


def usage():
    name = sys.argv[0]
    print(f"Usage: {name} [subcommand]")
    print("Subcommands:")
    print("  pre ...........  Pre-process notebooks")
    print("  book ..........  Build Jupyterbook")
    print("  where........... Print location of notebook source files")
    
def main():
    p = argparse.ArgumentParser()
    p.add_argument("command")
    args = p.parse_args()
    cmd = args.command.lower()
    if cmd == "book":
        banner("Build Jupyterbook", top=True)
        sys.exit(_run("build jupyterbook", jupyterbook))
    elif cmd == "pre":
        banner("Pre-process notebooks", top=True)
        sys.exit(_run("pre-process notebooks", preprocess))
    elif cmd == "where":
        fpath = Path(__file__).parent / "src"
        print(fpath)
        sys.exit(0)
    else:
        usage()
        sys.exit(0)
        
if __name__ == "__main__":
    main()
 
