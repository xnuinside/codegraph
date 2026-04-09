from typing import Dict, List

from codegraph.parsers.base import BaseParser


class RustParser(BaseParser):
    language = "rust"

    def __init__(self, args=None) -> None:
        self._args = args

    def get_source_files(self, paths) -> List[str]:
        raise NotImplementedError("Rust parser is not implemented yet.")

    def parse_files(self, paths_list: List[str]) -> Dict:
        raise NotImplementedError("Rust parser is not implemented yet.")

    def usage_graph(self, modules_data: Dict) -> Dict:
        raise NotImplementedError("Rust parser is not implemented yet.")

    def get_entity_metadata(self, modules_data: Dict) -> Dict:
        raise NotImplementedError("Rust parser is not implemented yet.")
