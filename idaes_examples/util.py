import logging


def add_vb(p, dest="vb"):
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        dest="vb",
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


