### Install all dependencies

Project uses poetry as a package manager, so if you don't have it - first of all read official doc & install it: https://python-poetry.org/docs/



```
    # after that do install
    poetry install

    # and activate project shell
    poetry shell

```

### Install pre-commit hook

To follow code styles and successfully pass github pipelines install pre-commit hooks

```

    pre-commit install

```

### Formatting and linting

Before committing changes, run the formatter and linter:

```
    black .
    ruff check .
```
