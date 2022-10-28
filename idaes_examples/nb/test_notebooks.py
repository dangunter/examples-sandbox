"""
Tests for notebooks (without running them)
"""
from pathlib import Path
from typing import List
import pytest
from idaes_examples.util import read_toc, allow_repo_root, NB_ROOT, find_notebooks


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


