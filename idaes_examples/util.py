import logging
from pathlib import Path


NB_ROOT = "nb"  # root folder name


def add_vb(p, dest="vb"):
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        dest=dest,
        default=0,
        help="Increase verbosity",
    )


def process_vb(log, vb):
    if vb >= 2:
        log.setLevel(logging.DEBUG)
    elif vb == 1:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARNING)


def allow_repo_root(src_path, func) -> Path:
    """This allows commands to (also) work if src_path is the repo root (as opposed
    to the directory with the notebooks in it).
    """
    if not (src_path / NB_ROOT).exists():
        mod = func.__module__.split(".")[0]
        if (src_path / mod / NB_ROOT).exists():
            src_path /= mod
    return src_path

