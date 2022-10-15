"""
Graphical examples browser
"""
# stdlib
from importlib import resources
import json
import logging
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Tuple, List

# third-party
import PySimpleGUI as sg

# package
import idaes_examples
from idaes_examples.build import find_notebooks, read_toc, NB_CELLS, Tags

# -------------
#   Logging
# -------------

_log = logging.getLogger("build")
_h = logging.StreamHandler()
_h.setFormatter(
    logging.Formatter("[%(levelname)s] %(asctime)s %(module)s - %(message)s")
)
_log.addHandler(_h)


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
    def __init__(self):
        self._nb = {}
        self._root = get_root()
        self._toc = read_toc(self._root)
        find_notebooks(self._root, self._toc, self.add_notebook)

    def add_notebook(self, path: Path):
        name = path.stem
        section = path.relative_to(self._root).parts[:-1]
        key = (section, name, "plain")
        self._nb[key] = Notebook(name, section, path, nbtype="plain")

        for tag in Tags.EX, Tags.SOL:
            tpath = path.parent / f"{name}_{tag.value}.ipynb"
            if tpath.exists():
                key = (section, name, tag.value)
                self._nb[key] = Notebook(name, section, tpath, nbtype=tag.value)

    @property
    def notebooks(self):
        return self._nb

    def get(self, index, name=None):
        rows = list(self._nb.values())
        if name is None:
            return rows[index]
        return getattr(rows[index], name)

    def as_table(self, *columns: str) -> List[List[str]]:
        t = []
        for nb in self._nb.values():
            row = []
            for c in columns:
                v = getattr(nb, c)
                row.append(v)
            t.append(row)
        return t

    def row_groups(self, *columns: str) -> List[int]:
        row_groups, group_num, prev_key = [], -1, None
        for nb in self._nb.values():
            key = {getattr(nb, c) for c in columns}
            if key != prev_key:
                group_num += 1
                prev_key = key
            row_groups.append(group_num)
        return row_groups


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


def gui(notebooks):
    sg.theme("Material1")

    nb_table = notebooks.as_table("type", "section", "title")
    row_bg_colors = ("white", "lightgrey")
    nb_table_row_colors = [
        (i, row_bg_colors[g % 2])
        for i, g in enumerate(notebooks.row_groups("section", "name"))
    ]

    description_widget = sg.Multiline(
        expand_y=True,
        expand_x=True,
        write_only=True,
        background_color="white",
    )

    title_max = max([len(r[2]) for r in nb_table])
    table_widget = sg.Table(
        nb_table,
        headings=["Type", "Section", "Title"],
        auto_size_columns=False,
        col_widths=[8, 8, title_max],
        justification="lll",
        row_colors=nb_table_row_colors,
        expand_y=True,
        expand_x=True,
        enable_click_events=True,
        bind_return_key=True,
    )

    layout = [
        [
            sg.Frame(
                "Notebooks",
                [[table_widget]],
                expand_y=True,
                expand_x=True
            ),
            sg.Frame(
                "Description",
                [[description_widget]],
                expand_y=True,
                expand_x=True,
            ),
        ]
    ]
    # create main window
    window = sg.Window("IDAES Notebook Browser", layout, size=(1200, 600), finalize=True)

    nbdesc = NotebookDescription(notebooks, description_widget)

    table_widget.bind("<Double-Button-1>", "+CLICKED2+")
    table_widget.bind("<Return>", "+CLICKED2+")

    # Event Loop to process "events" and get the "values" of the inputs
    row = -1
    jupyter = Jupyter()
    while True:
        event, values = window.read()
        # if user closes window or clicks cancel
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
        if len(event) >= 2:
            if event[0] == 0:
                if event[1] == "+CLICKED+":
                    row, _ = event[2]
                    if row is not None:
                        nbdesc.clicked(row)
                elif event[1] == "+CLICKED2+" and row >= 0:
                    nb = notebooks.get(row)
                    _log.info(f"Open notebook '{nb.name}'")
                    jupyter.open(nb.path)
                else:
                    pass

    window.close()


class Jupyter:
    command = ["jupyter", "notebook"]

    def __init__(self):
        pass

    def open(self, nb_path: Path):
        _log.debug(f"(start) open notebook at path={nb_path}")
        Popen(self.command + [str(nb_path)], stdin=None, stdout=PIPE, stderr=PIPE)
        _log.debug(f"(end) open notebook at path={nb_path}")


class NotebookDescription:
    def __init__(self, nb, widget):
        self._text = ["Select a notebook to view its description"]
        self._nb = nb
        self._w = widget
        self._print()

    def clicked(self, row):
        self._text = self._nb.get(row).description_lines
        self._print()

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
            font_size, font_weight, font_color = 11, "", "black"
            # Change style for headings
            if lstr.startswith("#"):
                depth = 1
                while lstr.startswith("#" * depth):
                    depth += 1
                font_size += (4 - min(depth, 3)) * 2
                font_weight = "bold"
                line = line[depth:].strip() + "\n"
                font_color = "#33a"
            # Display line
            self._w.update(line, append=True, font_for_value=("Arial", font_size,
                                                              font_weight),
                           text_color_for_value=font_color)

# -------------
#   main
# -------------


if __name__ == "__main__":
    import sys

    nb = Notebooks()
    if "gui" in sys.argv or "ui" in sys.argv:
        gui(nb)
    else:
        for key, val in nb._nb.items():
            print(
                f"{val.type}{' '*(10 - len(val.type))} {'/'.join(key[0])}/{key[1]} {val.title}"
            )
