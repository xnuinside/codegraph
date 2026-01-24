import glob
from pathlib import Path
from typing import Iterable, List, Union


def get_paths_list(paths: Union[str, List], extensions: Iterable[str]) -> List[str]:
    if isinstance(paths, str):
        paths = [paths]
    if len(paths) == 1 and any(paths[0].endswith(ext) for ext in extensions):
        path = Path(paths[0]).absolute()
        if not path.exists():
            raise ValueError(f"Path {path.as_posix()} does not exists")
        return [path.as_posix()]

    paths_list = []
    for path in paths:
        path = Path(path).absolute()
        if not path.exists():
            raise ValueError(f"Path {path.as_posix()} does not exist")
        for ext in extensions:
            paths_list += [Path(p).as_posix() for p in glob.glob(str(path / "**" / f"*{ext}"), recursive=True)]
    return paths_list


def get_python_paths_list(paths: Union[str, List]) -> List[str]:
    """
        return list of paths to python files, that found in provided path
    :param paths: paths to folder or python file that need to tests
    :return:
    """
    return get_paths_list(paths, [".py"])
