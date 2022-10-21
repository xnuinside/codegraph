import glob
from pathlib import Path
from typing import List, Union


def get_python_paths_list(paths: Union[str, List]) -> List:
    """
        return list of paths to python files, that found in provided path
    :param paths: paths to folder or python file that need to tests
    :return:
    """
    if isinstance(paths, str):
        paths = [paths]
    if len(paths) == 1 and paths[0].endswith(".py"):
        # mean provided path to one python module
        path = Path(paths[0]).absolute()
        if not path.exists():
            raise ValueError(f"Path {path.as_posix()} does not exists")
        return [path.as_posix()]

    paths_list = []
    for path in paths:
        path = Path(path).absolute()
        if not path.exists():
            raise ValueError(f"Path {path.as_posix()} does not exists")
        path = path.as_posix()
        paths_list += [
            path
            for path in glob.glob(path + "/*", recursive=True)
            if path.endswith(".py") and not path.endswith("__init__.py")
        ]
    return paths_list
