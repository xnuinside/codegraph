import os
from typing import Text, Tuple, Dict, List
from argparse import Namespace
from collections import defaultdict
from codegraph.parser import create_objects_array, Import
from codegraph.utils import get_paths_list


aliases = {}


def read_file_content(path: Text) -> Text:
    with open(path, 'r+') as file_read:
        return file_read.read()


def parse_code_file(path: Text) -> List:
    """ read module source and parse to get objects array """
    source = read_file_content(path)
    parsed_module = create_objects_array(source=source, fname=os.path.basename(path))
    return parsed_module


def get_code_objects(paths_list: List) -> Dict:
    """
        get all code files data for paths list
    :param paths_list: list with paths to code files to parse
    :return:
    """
    all_data = {}
    for path in paths_list:
        content = parse_code_file(path)
        all_data[path] = content
    return all_data


def create_graph(args: Namespace) -> Dict:
    """
        method to create list of objects from py modules
    :param args:
    :return:
    """
    # get py modules list
    paths_list = get_paths_list(args.paths)
    # get py modules list
    add_dict = get_code_objects(paths_list)
    modules_entities = usage_graph(add_dict)
    return modules_entities


def get_module_name(code_path: Text) -> Text:
    module_name = os.path.basename(code_path).replace('.py', '')
    return module_name


def module_name_in_imports(imports: List, module_name: Text) -> bool:
    for import_ in imports:
        if module_name in import_:
            return True
    return False


def get_imports_and_entities_lines(code_objects: Dict) -> Tuple[Dict, Dict, Dict]:
    """
        joined together to avoid iteration several time
        imports - list of modules in code_objects Dict that used in current module
    """
    entities_lines = defaultdict(dict)
    imports = defaultdict(list)
    modules_ = code_objects.keys()
    names_map = {}
    for path in code_objects:
        _base_folder = os.path.basename(os.path.dirname(path))
        names_map[get_module_name(path)] = path
        # for each module in list
        if code_objects[path] and isinstance(code_objects[path][-1], Import):
            # extract imports if exist
            for import_ in code_objects[path].pop(-1).modules:
                pathed_import = import_
                alias = None
                if ' as ' in pathed_import:
                    pathed_import, alias = pathed_import.split(' as ')
                if _base_folder+'.' in pathed_import:
                    pathed_import = pathed_import.replace('.', '/').split(_base_folder+'/')[1]
                if '/' in pathed_import:
                    pathed_import = pathed_import.split('/')[0]
                for module_ in modules_:
                    if pathed_import and pathed_import in module_:
                        if alias:
                            aliases[pathed_import] = alias
                        imports[path].append(pathed_import)
        for entity in code_objects[path]:
            # create a dict with lines of start and end for each entity in module
            entities_lines[path][(entity.lineno, entity.endno)] = entity.name
    return entities_lines, imports, names_map


def search_entities_from_list_in_code(entities_list: List, module_name: Text, line:Text) -> Text:
    for entity in entities_list:
        if search_entity_usage(module_name, entity.name, line):
            yield entity


def search_entities_from_module_in_code(
        _module: Text, _path: Text, code_objects: Dict, code: List, current: bool =False) -> Dict:
    found_entities = defaultdict(list)
    for num, line in enumerate(code):
        if not line.startswith("#") and not line.startswith("\"") and not line.startswith("\'"):
            entities_in_line = [x for x in
                                search_entities_from_list_in_code(code_objects[_path], _module, line)]
            for entity in entities_in_line:
                prefix = f'{_module}.' if not current else ''
                found_entities[f'{prefix}{entity.name}'].append(num + 1)
    return found_entities


def collect_entities_usage_in_modules(code_objects: Dict,  imports: Dict, modules_names_map: Dict) -> Dict:
    entities_usage_in_modules = defaultdict(dict)
    for path in code_objects:
        entities_usage_in_modules[path] = defaultdict(list)
        # print(f"Start to work with module: {path}")
        # print(f"Imports in module: {imports}")
        module_content = read_file_content(path)
        # to reduce count of iteration, we not need lines with functions and classes defenitions
        module_content = module_content.replace("async ", "# async ").replace(
            "def ", "# def ").replace("class ", "# class ")
        # split by line
        code = module_content.split('\n')
        for _module in imports[path]:
            # search entities from other modules
            _path = modules_names_map[_module]
            entities_usage_in_modules[path].update(search_entities_from_module_in_code(
                _module, _path, code_objects, code))
        # search entities from current module
        entities_usage_in_modules[path].update(
            search_entities_from_module_in_code(get_module_name(path), path, code_objects, code, current=True))
    return entities_usage_in_modules


def populate_free_nodes(code_objects: Dict, dependencies: Dict) -> Dict:
    for path in code_objects:
        for entity in code_objects[path]:
            if entity.name not in dependencies[path]:
                dependencies[path][entity.name] = []
    return dependencies


def usage_graph(code_objects: Dict) -> Dict:
    """
        module name: function
    :param code_objects:
    :return:
    """
    entities_lines, imports, modules_names_map = get_imports_and_entities_lines(code_objects)
    entities_usage_in_modules = collect_entities_usage_in_modules(code_objects, imports, modules_names_map )
    # create edges
    dependencies = defaultdict(dict)
    for module in entities_usage_in_modules:
        dependencies[module] = defaultdict(list)
        for method_that_used in entities_usage_in_modules[module]:
            method_usage_lines = entities_usage_in_modules[module][method_that_used]
            for method_usage_line in method_usage_lines:
                for entity in entities_lines[module]:
                    if entity[0] <= method_usage_line <= entity[1]:
                        dependencies[module][entities_lines[module][entity]].append(method_that_used)
                        break
                else:
                    # mean in global of module
                    dependencies[module]['_'].append(method_that_used)
    dependencies = populate_free_nodes(code_objects, dependencies)
    return dependencies


def search_entity_usage(module_name: Text, name: Text, line: Text) -> bool:
    """ check exist method or entity usage in line or not """
    method_call = name + "("
    dot_access = name + "."
    if method_call in line or " " + dot_access in line \
            or f"{module_name}." + method_call in line or f"{module_name}." + dot_access in line:
        return True
    elif module_name in aliases:
        if aliases[module_name] + '.' + method_call in line:
            return True
    return False

