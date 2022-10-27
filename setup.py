#!/usr/bin/env python
"""
Institute for the Design of Advanced Energy Systems
Examples
"""
from setuptools import setup, find_namespace_packages

NAME = "idaes_examples"
VERSION = "0.0.1"

kwargs = dict(
    zip_safe=False,
    name=NAME,
    version=VERSION,
    packages=find_namespace_packages(),
    # Put abstract (non-versioned) deps here.
    # Concrete dependencies go in requirements[-dev].txt
    install_requires=[
        "pyyaml"
    ],
    entry_points={
       "console_scripts": [
           # XXX: Make this one script
           "idaesx = idaes_examples.build:main",
           "idaesx-browse = idaes_examples.browse:main",
       ]
    },
    # Only installed if [<key>] is added to package name
    extras_require={},
    package_data={
        # If any package contains these files, include them:
        "": [
            "*.template",
            "*.json",
            "*.yaml",
            "*.svg",
            "*.png",
            "*.jpg",
            "*.csv",
            "*.ipynb",
            "*.txt",
            "*.js",
            "*.css",
            "*.html",
            "*.json.gz",
            "*.dat",
            "*.h5",
            "*.pb",  # for Keras Surrogate folder
            "*.data-00000-of-00001",  # for Keras Surrogate folder
            "*.index",  # for Keras Surrogate folder
            "*.trc",
            "*.xlsx",  # idaes/dmf/tests/data_files - tabular import test files
        ]
    },
    include_package_data=True,
    data_files=[],
    maintainer="Dan Gunter",
    maintainer_email="dkgunter@lbl.gov",
    url="https://idaes.org",
    license="BSD",
    platforms=["any"],
    description="IDAES Process Systems Engineering Examples",
    long_description="IDAES Process Systems Engineering Examples",
    long_description_content_type="text/markdown",
    keywords=[NAME, "energy systems", "chemical engineering", "process modeling"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

setup(**kwargs)
