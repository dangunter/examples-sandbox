# Scripts for examples
This directory has utility scripts (and supporting files) for the repository.

## Migration scripts

Some of these work together to help migrate files from the older examples-pse repository into the new structure.
They could be run from the root of this repository like this:
```python
# Copy notebook files
python scripts/copy_files.py \
  ~/src/idaes/examples-pse/src nb \
  --map map.yml

# Generate Jupyterbook table of contents
python generate_toc.py nb \
  --map scripts/map.yml \
  --target new_toc.yml

# Add tags to notebook cells
python edit_tags.py nb \
  --map scripts/map.yml
```

`map.yml` is a mapping of directories in examples-pse to directories in the new structure.

## Other scripts

* `pytest_report.py` post-processes the JSON report from pytest for human consumption



