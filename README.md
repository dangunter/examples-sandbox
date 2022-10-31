# examples-sandbox

IDAES examples

## For Users

Good luck!

## For Developers

This section is intented for people who are creating and modifying examples.
The examples are primarily in Jupyter Notebooks, though Python support files and data are commonly used to keep the notebooks short and more us

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

The documentation is built using [Jupyterbook][1].
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

[1]: https://jupyterbook.org/

