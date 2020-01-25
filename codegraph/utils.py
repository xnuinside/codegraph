import os
import glob
from typing import List


def get_paths_list(paths: List) -> List:
    """
        return list of paths to python files, that found in provided path
    :param paths: paths to folder or python file that need to tests
    :return:
    """
    if len(paths) == 1 and paths[0].endswith('.py'):
        return [paths[0]]
    paths_list = []
    for path in paths:
        paths_list += [path for path in glob.glob(path+'/*', recursive=True)
                       if path.endswith('.py') and not path.endswith('__init__.py')]
    return paths_list
