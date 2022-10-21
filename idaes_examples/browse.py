"""
Graphical examples browser
"""
# stdlib
import argparse
from importlib import resources
import json
import logging
from logging.handlers import RotatingFileHandler
from operator import attrgetter
from pathlib import Path
import re
import sys
from subprocess import Popen, PIPE, TimeoutExpired
import time
from typing import Tuple, List

# third-party
import PySimpleGUI as sg

# package
import idaes_examples
from idaes_examples.build import find_notebooks, read_toc, NB_CELLS, Ext
from idaes_examples.util import add_vb, process_vb

# -------------
#   Logging
# -------------

use_file = False
log_dir = Path.home() / ".idaes" / "logs"
if log_dir.exists():
    use_file = True
else:
    try:
        log_dir.mkdir(exist_ok=True, parents=True)
        use_file = True
    except OSError:
        pass
_log = logging.getLogger("idaes_examples")
if use_file:
    _h = RotatingFileHandler(
        log_dir / "nb_browser.log", maxBytes=64 * 1024, backupCount=5
    )
else:
    _h = logging.StreamHandler()
_h.setFormatter(
    logging.Formatter("[%(levelname)s] %(asctime)s %(name)s::%(module)s - %(message)s")
)
_log.addHandler(_h)
_log.setLevel(logging.INFO)

L_START, L_END = "-start-", "-end-"

# -------------


def get_root() -> Path:
    """Find notebook source root."""
    path = None
    stack = [resources.files(idaes_examples)]
    while stack:
        d = stack.pop()
        _log.debug(f"resource: {d}")
        if d.is_file():
            pass
        else:
            p = Path(d)
            if p.stem == "nb":
                path = p
                break
            for item in d.iterdir():
                stack.append(item)
    return path


class Notebooks:
    DEFAULT_SORT_KEYS = ("section", "name", "type")

    def __init__(self, sort_keys=DEFAULT_SORT_KEYS):
        self._nb = {}
        self._root = get_root()
        self._toc = read_toc(self._root)
        find_notebooks(self._root, self._toc, self._add_notebook)
        self._sorted_values = sorted(
            list(self._nb.values()), key=attrgetter(*sort_keys)
        )
        self._tree = self._as_tree()

    def _add_notebook(self, path: Path):
        name = path.stem
        section = path.relative_to(self._root).parts[:-1]

        for ext in Ext.DOC.value, Ext.EX.value, Ext.SOL.value:
            tpath = path.parent / f"{name}_{ext}.ipynb"
            if tpath.exists():
                key = (section, name, ext)
                _log.debug(f"Add notebook. key='{key}'")
                self._nb[key] = Notebook(name, section, tpath, nbtype=ext)

    def __len__(self):
        return len(self._nb)

    @property
    def notebooks(self):
        return self._nb

    def titles(self):
        return [nb.title for nb in self._nb.values()]

    def __getitem__(self, key):
        return self._nb[key]

    def as_tree(self) -> sg.TreeData:
        return self._tree

    def _as_tree(self) -> sg.TreeData:
        td = sg.TreeData()
        root_key = "root"

        # organize notebooks hierarchically
        data = {}
        for nb in self._sorted_values:
            if nb.section not in data:
                data[nb.section] = {}
            if nb.name not in data[nb.section]:
                data[nb.section][nb.name] = []
            data[nb.section][nb.name].append(nb)

        # copy hierarchy into an sg.TreeData object
        td.insert("", text="Notebooks", key=root_key, values=[])
        for section in data:
            section_key = f"s_{section}"
            td.insert(root_key, key=section_key, text=section, values=[])
            for name, nblist in data[section].items():
                base_key = None
                for nb in nblist:
                    if nb.type == Ext.DOC.value:
                        base_key = f"nb+{section}+{nb.name}+{nb.type}"
                        td.insert(section_key, key=base_key, text=nb.title, values=[nb.path])
                        break
                if len(nblist) > 1:
                    for nb in nblist:
                        if nb.type != Ext.DOC.value:
                            sub_key = f"nb+{section}+{nb.name}+{nb.type}"
                            subtitle = nb.type.title()
                            td.insert(base_key, key=sub_key, text=subtitle, values=[nb.path])

        return td


class Notebook:
    def __init__(self, name: str, section: Tuple, path: Path, nbtype="plain"):
        self.name, self._section = name, section
        self._path = path
        self._get_description()
        self._type = nbtype

    @property
    def section(self) -> str:
        return ":".join(self._section)

    @property
    def title(self) -> str:
        return self._short_desc

    @property
    def description(self) -> str:
        return self._long_desc

    @property
    def description_lines(self) -> List[str]:
        return self._lines

    @property
    def type(self) -> str:
        return self._type

    @property
    def path(self) -> Path:
        return self._path

    def _get_description(self):
        desc = False
        with self._path.open("r") as f:
            data = json.load(f)
        cells = data[NB_CELLS]
        if len(cells) > 0:
            c1 = cells[0]
            if c1["cell_type"] == "markdown" and "source" in c1 and c1["source"]:
                self._long_desc = "".join(c1["source"])
                self._lines = c1["source"]
                for line in self._lines:
                    if line.strip().startswith("#"):
                        self._short_desc = line[line.rfind("#") + 1 :].strip()
                        break
                desc = True
        if not desc:
            self._short_desc, self._long_desc = "No description", "No description"


# -------------
#     GUI
# -------------

FONT = ("Helvetica", 11)


def gui(notebooks):
    sg.theme("Material1")

    nb_tree = notebooks.as_tree()

    description_widget = sg.Multiline(
        expand_y=True,
        expand_x=True,
        write_only=True,
        background_color="white",
    )

    title_max = max(len(t) for t in notebooks.titles())

    nb_widget = sg.Tree(
        nb_tree,
        headings=[],
        col0_width=title_max,
        select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
        key="-TREE-",
        show_expanded=True,
        expand_y=True,
        expand_x=True,
        enable_events=True,
        font=FONT,
    )

    open_widget = sg.Button(
        "Open",
        tooltip="Open the selected notebook",
        button_color=("white", "#03f"),
        disabled_button_color=("grey", "grey"),
        key="open",
        disabled=True,
        pad=(10, 10),
        auto_size_button=False
    )
    layout = [
        [
            sg.Frame("Notebooks", [[nb_widget]], expand_y=True, expand_x=True),
            sg.Frame(
                "Description",
                [[description_widget]],
                expand_y=True,
                expand_x=True,
            ),
        ],
        [open_widget],
    ]
    # create main window
    window = sg.Window(
        "IDAES Notebook Browser", layout, size=(1200, 600), finalize=True
    )

    nbdesc = NotebookDescription(notebooks, description_widget)

    # Event Loop to process "events" and get the "values" of the inputs
    row = -1
    jupyter = Jupyter()
    while True:
        event, values = window.read()
        # if user closes window or clicks cancel
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
        # print(event, values)
        if isinstance(event, int):
            _log.debug("Unhandled event")
        elif event == "-TREE-":
            what = values.get("-TREE-", [""])[0]
            if what == "root" or what.startswith("s_"):
                window["open"].update(disabled=True)
            elif what:
                _, section, name, type_ = what.split("+")
                nbdesc.show(section, name, type_)
                window["open"].update(disabled=False)
        elif event == "open":
            what = values.get("-TREE-", [None])[0]
            if what:
                _, section, name, type_ = what.split("+")
                path = nbdesc.get_path(section, name, type_)
                jupyter.open(path)

    _log.info("Stop running notebooks")
    jupyter.stop()
    _log.info("Close main window")
    window.close()
    return 0


class Jupyter:

    COMMAND = "jupyter"

    def __init__(self):
        self._ports = set()

    def open(self, nb_path: Path):
        _log.info(f"(start) open notebook at path={nb_path}")
        p = Popen([self.COMMAND, "notebook", str(nb_path)], stderr=PIPE)
        buf, m, port = "", None, "unknown"
        while True:
            s = p.stderr.read(100).decode("utf-8")
            if not s:
                break
            buf += s
            m = re.search(r"http://.*:(\d{4})/\?token", buf, flags=re.M)
            if m:
                break
        if m:
            port = m.group(1)
            self._ports.add(port)
        _log.info(f"(end) open notebook at path={nb_path} port={port}")

    def stop(self):
        for port in self._ports:
            self._stop(port)

    @classmethod
    def _stop(cls, port):
        _log.info(f"(start) stop running notebook, port={port}")
        p = Popen([cls.COMMAND, "notebook", "stop", port])
        try:
            p.wait(timeout=5)
            _log.info(f"(end) stop running notebook, port={port}: Success")
        except TimeoutExpired:
            _log.info(f"(end) stop running notebook, port={port}: Timeout")


class NotebookDescription:
    def __init__(self, nb: dict, widget):
        self._text = ["Select a notebook to view its description"]
        self._nb = nb
        self._w = widget
        self._print()

    def show(self, section, name, type_):
        key = ((section,), name, type_)
        self._text = self._nb[key].description_lines
        self._print()

    def get_path(self, section, name, type_) -> Path:
        key = ((section,), name, type_)
        return self._nb[key].path

    def _print(self):
        self._w.update("")
        pre = True
        for line in self._text:
            # Check that line is non-empty and not a leading blank
            if not line:
                continue
            lstr = line.strip()
            if pre and lstr == "":
                continue
            # Check that line is not an image
            if lstr.startswith("!["):
                continue
            # Line will be displayed
            pre = False
            font_size, font_weight, font_color = FONT[1], "", "#444"
            # Change style for headings
            if lstr.startswith("#"):
                depth = 1
                while lstr.startswith("#" * depth):
                    depth += 1
                font_size += (4 - min(depth, 3)) * 2
                font_weight = "bold"
                line = line[depth:].strip() + "\n"
                font_color = "#333"
            # Display line
            self._w.update(
                line,
                append=True,
                font_for_value=(FONT[0], font_size, font_weight),
                text_color_for_value=font_color,
            )


# -------------
#   main
# -------------


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--console", action="store_true", dest="console")
    add_vb(p)
    args = p.parse_args()
    process_vb(_log, args.vb)

    _log.info(f"Find notebooks {L_START}")
    nb = Notebooks()
    _log.info(f"Find notebooks {L_END}: num={len(nb)}")
    if args.console:
        for val in nb._sorted_values:
            pth = Path(val.path).relative_to(Path.cwd())
            print(f"{val.type}{' '*(10 - len(val.type))} {val.title} -> {pth}")
        status = 0
    else:
        _log.info(f"Run GUI {L_START}")
        status = gui(nb)
        _log.info(f"Run GUI {L_END}")
    return status


if __name__ == "__main__":
    sys.exit(main())
