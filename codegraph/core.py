from argparse import Namespace
from typing import Dict, Set

from codegraph.parsers import get_parser


class CodeGraph:
    def __init__(self, args: Namespace):
        language = getattr(args, "language", "python")
        self.parser = get_parser(language, args=args)
        self.paths_list = self.parser.get_source_files(args.paths)
        self.modules_data = self.parser.parse_files(self.paths_list)

    def get_lines_numbers(self):
        """
           return data with entities names and start and end line
        :return: Example: {'/Users/user/package/module_name.py':
                {'function': (1, 2), 'function_with_constant_return_int': (5, 6),
                'function_with_constant_return_float': (9, 10),
                'function_with_statement_return': (13, 14)..}}

                first number in tuple - start line, second - last line
        """
        data = {}
        metadata = self.get_entity_metadata()
        for module, entities in metadata.items():
            data[module] = {}
            for name, info in entities.items():
                data[module][name] = (info.get("lineno"), info.get("endno"))
        return data

    def get_entity_metadata(self) -> Dict:
        return self.parser.get_entity_metadata(self.modules_data)

    def usage_graph(self) -> Dict:
        return self.parser.usage_graph(self.modules_data)

    def get_dependencies(self, file_path: str, distance: int) -> Dict[str, Set[str]]:
        """
        Get dependencies that are 'distance' nodes away from the given file.

        :param file_path: Path of the file to start from
        :param distance: Number of edges to traverse
        :return: Dictionary with distances as keys and sets of dependent files as values
        """
        usage_graph = self.usage_graph()
        return self.parser.get_dependencies(usage_graph, file_path, distance)
