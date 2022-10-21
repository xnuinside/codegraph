# till will not be released poetry plugins to get possible add custom steos in build process
# https://github.com/python-poetry/poetry/pull/3733
sed '/## Changelog/q' README.md > new_README.md
cat CHANGELOG.txt >> new_README.md
rm README.md
mv new_README.md README.md
m2r2 README.md
mv README.rst docs/README.rst
rm -r dist
poetry build
twine check dist/*