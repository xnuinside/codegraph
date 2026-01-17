#!/bin/bash
# Build script for codegraph
# https://github.com/python-poetry/poetry/pull/3733

set -e

# Create README with changelog from CHANGELOG.md
sed '/## Changelog/q' README.md > new_README.md
# Skip the header line "# Changelog" from CHANGELOG.md and append the rest
tail -n +3 CHANGELOG.md >> new_README.md
rm README.md
mv new_README.md README.md

# Convert to RST for PyPI
m2r2 README.md
mv README.rst docs/README.rst

# Build package
rm -rf dist
poetry build
twine check dist/*