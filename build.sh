#!/bin/bash

# Build package
rm -rf dist
poetry build
twine check dist/*