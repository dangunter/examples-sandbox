# Scripts for examples
This directory has utility scripts (and supporting files) for the repository.

**Table of Contents**

* Scripts for examples
  * Migration scripts
  * Other scripts

## Migration scripts

Some of these work together to help migrate files from the older examples-pse repository into the new structure.
They could be run from the root of this repository like this:

```
# Copy notebook files
python copy_files.py \
  ~/src/idaes/examples-pse/src \
  ../idaes_examples/nb \
  --map map.yml

# Generate Jupyterbook table of contents
python generate_toc.py \
  ../idaes_examples/nb \
  --map map.yml \
  --output new_toc.yml

# Add tags to notebook cells
python edit_tags.py \
  ../idaes_examples/nb \
  --map map.yml
```

`map.yml` is a mapping of directories in examples-pse to directories in the new structure.

## Other scripts

* `pytest_report.py` post-processes the JSON report from pytest for human consumption



