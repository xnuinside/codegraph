from abc import ABC, abstractmethod
from collections import deque
from typing import Dict, List, Set


class BaseParser(ABC):
    language: str

    @abstractmethod
    def get_source_files(self, paths) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def parse_files(self, paths_list: List[str]) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def usage_graph(self, modules_data: Dict) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def get_entity_metadata(self, modules_data: Dict) -> Dict:
        raise NotImplementedError

    def get_dependencies(self, usage_graph: Dict, file_path: str, distance: int) -> Dict[int, Set[str]]:
        """
        Default implementation that expects dependencies as "module.entity".
        Parsers can override this to handle language-specific dependency formats.
        """
        dependencies = {i: set() for i in range(1, distance + 1)}

        if file_path not in usage_graph:
            return dependencies

        queue = deque([(file_path, 0)])
        visited = set()

        while queue:
            current_file, current_distance = queue.popleft()

            if current_distance >= distance:
                continue

            if current_file not in visited:
                visited.add(current_file)

                for _, used_entities in usage_graph[current_file].items():
                    for used_entity in used_entities:
                        if "." in used_entity:
                            dependent_file = used_entity.split(".")[0] + ".py"
                            if dependent_file != current_file:
                                dependencies[current_distance + 1].add(dependent_file)
                                queue.append((dependent_file, current_distance + 1))

        return dependencies
