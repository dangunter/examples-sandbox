# IDAES Examples

This repository contains Jupyter Notebooks (and supporting Python scripts and data) that demonstrate the capabilities of the IDAES platform.

Using the `idaesx` command that comes with this repository, the contained Jupyter Notebooks can be opened and run locally (`idaesx gui`) or built into [Jupyterbook][jb] documentation (`idaesx build`).
The standard Python test runner, `pytest`, can be used to test that all the notebooks execute successfully.

The rest of this README is broken into separate sections for users, to view or run examples, and for developers, who may contribute modifications or new examples to the repository.

## For Users

### Install

For now, see the *For Developers* -> *Install* section.

### Browse notebooks

Use the `idaesx gui` command to get a simple graphical UI that lets you browse and open notebooks (in a Jupyter server) for local execution.

### Build documentation locally

Run `idaesx build` from the repository root. For more details, see the *For Developers* -> *Build documentation* section.

### Run tests

Run `pytest` from the repository root.
For more details, see the *For Developers* -> *Run tests* section.

## For Developers

This section is intented for people who are creating and modifying examples.
The examples are primarily in Jupyter Notebooks.
Python support files and data may be used to keep the notebooks focused on the interactive material.

### Install

Clone the repository from Github, setup your Python environment as you usually do, then run pip with the developer requirements:
```shell
pip install -r requirements-dev.txt
```

### Run tests

There are two ways to run tests: running all the notebooks (integration tests), and 
testing that notebooks work without running all their code (unit tests).

To run **integration tests**, from the *root* directory:
```shell
# from the root directory of the repository
pytest
```

To run the **unit tests** change to do the `idaes_examples` directory, then run the same command:
```shell
cd idaes_examples
pytest
```

Different tests are run in the idaes_examples directory because there is a *pytest.ini* file there. In the root directory, tests are configured by `pyproject.toml`, in the *tool.pytest.ini_options* section.

### Build documentation

The documentation is built using [Jupyterbook][jb].
We have written a thin layer around the Jupyterbook executable, which is installed as a command-line program *idaesx*.
To build the documentation, run:

```shell
idaesx build
```

The output will be in *idaes_examples/nb/_build/html*. As a convenience, you can open that HTML file with the command `idaesx view`.

### Preprocessing

The commands to run tests and build documentation both run a preprocessing step that creates separate copies of the Jupyter notebooks that are used for tests, tutorial exercise and solution, and documentation (see Notebook Names).
These generated files should ***not*** be added to the repository.
If you want to run that preprocessing step separately, use `idaesx pre`.
To remove pre-processed files, run `idaesx clean`.

### Notebook names

Notebooks all have a file name that fits the pattern notebook-name`_ext`.ipynb*.
When creating or modifying notebooks, you should always use `ext` = *src*.
Other extensions are automatically generated when running tests, building the documentation, and manually running the preprocessing step:

* notebook-name`_doc`.ipynb: For the documentation. Tests are stripped.
* notebook-name`_test`.ipynb: For testing. All cells are included.
* notebook-name`_exercise`.ipynb: For tutorial notebooks. Rests and solution cells are stripped.
* notebook-name`_solution`.ipynb: For tutorial notebooks. Tests are stripped and solution cells are left in.


### Create example

There are two main steps to creating a new notebook example.

1. Add Jupyter Notebook and supporting files
   1. If this is a new category of notebooks, create a directory. The directory name *should* be in lowercase with underscores between words. For example: 'machine_learning'.
   2. Notebook filename *should* be in lowercase with underscores and ***must*** end with '_src.ipynb'. For example: 'my_example_src.ipynb'.
   3. Add -- in the same directory as the notebook -- any data files, images, or Python files needed for it to run.
2. Add Jupyter notebook to the Jupyterbook table of contents in *idaes_examples/nb/_toc.yml*.
   1. The notebook will be a *section*. If you added a new directory, you will create a new *chapter*, otherwise it will go under an existing one. See [Jupyterbook][1] documentation for more details.
   2. Refer to the notebook as '*path/to/notebook-name*_doc' (replace '_src' with '_doc' and drop the '.ipynb' extension). For example: 'machine_learning/my_example_doc'.
   3. If you created a new directory for this notebook, make sure you add an *index.md* file to it. See other *index.md* files for the expected format.

You *should*  test the new notebook and build it locally before pushing the new file, i.e., run `pytest` and `idaesx build`.

#### Jupyter Notebook cell tags

Each source Jupyter notebook (ending in '_src.ipynb') is preprocessed to create additional notebooks which are a copy of the original with some cells (steps in the notebook execution) removed.

| Notebook type | Description        | Ends with     |
| ------------- | ------------------ | ------------- |
| source        | Notebook source    | _src.ipynb |
| testing       | Run for testing    | _test.ipynb  |
| exercise      | Tutorial exercises  | _exercise.ipynb |
| solution      | Tutorial exercises and solutions  | _solution.ipynb |
| documentation | Show in documentation | _doc.ipynb | 

This process uses the feature of Jupyter notebook [cell tags][celltags] to understand which additional notebooks to create.

The following tags are understood by the preprocessing step:

| Tag | Result |
| --- | ------ |
| testing | Remove this cell, except in the <em>testing</em> notebooks |
| exercise | The presence of this tag means a notebook is a tutorial. Generate an *exercise* and *solution* notebook, and keep this cell in both. Remove this cell in the *documentation* notebook. |
| solution | The presence of this tag means a notebook is a tutorial. Generate an *exercise* and *solution* notebook, but remove this cell in the *solution* notebook; keep the cell in the *documentation* notebook. |

In addition, the [Jupyterbook tags][hidecell] for hiding or removing cells will be passed through and used for generating the documentaton.

<!-- 
   References 
-->
[jb]: https://jupyterbook.org/
[hidecell]: https://jupyterbook.org/en/stable/interactive/hiding.html
[celltags]: https://jupyterbook.org/en/stable/content/metadata.html