"""
Tests for notebooks (without running them)
"""
# stdlib
import os
from pathlib import Path
import subprocess
from typing import List

# third-party
import pytest

# package
from idaes_examples.common import read_toc, find_notebooks


# -------------------
#  Fixtures
# -------------------

@pytest.fixture(scope="module")
def notebooks() -> List[Path]:
    src_path = find_toc(Path(__file__).parent)
    assert src_path is not None, "Cannot find _toc.yml"
    toc = read_toc(src_path)

    notebooks = []

    def add_notebook(p, **kwargs):
        notebooks.append(p)

    find_notebooks(src_path, toc, callback=add_notebook)
    return notebooks


def find_toc(p: Path):
    """Walk up from 'p' looking for the '_toc.yml' file"""
    while p != p.parent:
        if (p / "_toc.yml").exists():
            return p
        p = p.parent
    return None


# -------------------
#  Tests
# -------------------

def test_smoke(notebooks: List[Path]):
    assert len(notebooks) > 0
    for nb_path in notebooks:
        assert nb_path.exists()
        assert nb_path.stat().st_size > 0


# Use 'black --check' to test whether syntax is OK in Jupyter notebooks.
# This requires that black[jupyter] has been installed.
def test_black():
    working_dir = Path(__file__).parent
    command = ["black", "--check", "--include", ".*_src\\.ipynb", str(working_dir)]
    proc = subprocess.Popen(command, stderr=subprocess.PIPE)
    _, stderr_data = proc.communicate(timeout=20)
    if proc.returncode != 0:
        # print out errors for pytest's captured stdout
        for line in stderr_data.decode("utf-8").split(os.linesep):
            if line.startswith("error"):
                print(line)
        assert False, "Black format check failed for *_src.ipynb"
