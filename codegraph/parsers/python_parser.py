import ast
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Text, Tuple

from codegraph.parser import AsyncFunction, Class, Function
from codegraph.parsers.base import BaseParser
from codegraph.utils import get_python_paths_list

try:
    import typed_ast.ast27 as ast27
except ImportError:  # pragma: no cover - optional dependency
    ast27 = None


@dataclass
class ImportInfo:
    module_aliases: Dict[str, str]
    entity_aliases: Dict[str, str]
    module_imports: Set[str]


@dataclass
class ModuleData:
    ast_tree: object
    entities: List[object]
    entity_nodes: Dict[str, object]
    imports: ImportInfo


class PythonParser(BaseParser):
    language = "python"

    def __init__(self, args=None, python_version: Optional[str] = None) -> None:
        if python_version is None and args is not None:
            python_version = getattr(args, "python_version", None)
        self._python_version = python_version
        self._major, self._minor = self._parse_python_version(self._python_version)
        self._ast_mod = ast27 if self._major == 2 else ast
        self._feature_version = self._minor if self._major == 3 else None
        self._module_names_set: Set[str] = set()

    def get_source_files(self, paths) -> List[str]:
        return get_python_paths_list(paths)

    def parse_files(self, paths_list: List[str]) -> Dict:
        self._module_names_set = {os.path.basename(path).replace(".py", "") for path in paths_list}
        all_data = {}
        for path in paths_list:
            source = self._read_file_content(path)
            ast_tree = self._parse_source(source, path)
            entities, entity_nodes = self._extract_entities(ast_tree, os.path.basename(path))
            imports = self._collect_imports(ast_tree)
            all_data[path] = ModuleData(
                ast_tree=ast_tree,
                entities=entities,
                entity_nodes=entity_nodes,
                imports=imports,
            )
        return all_data

    def usage_graph(self, modules_data: Dict) -> Dict:
        dependencies: Dict[str, Dict[str, List[str]]] = {}

        for module_path, module_data in modules_data.items():
            local_entities = {entity.name for entity in module_data.entities}
            module_aliases = module_data.imports.module_aliases
            entity_aliases = module_data.imports.entity_aliases

            dependencies[module_path] = {}
            module_level_deps = self._collect_dependencies_in_module(
                module_data.ast_tree,
                local_entities,
                module_aliases,
                entity_aliases,
            )
            module_level_deps += [f"{mod}._" for mod in module_data.imports.module_imports]
            dependencies[module_path]["_"] = self._deduplicate(module_level_deps)

            for entity in module_data.entities:
                node = module_data.entity_nodes[entity.name]
                entity_deps = self._collect_dependencies_in_entity(
                    node,
                    local_entities,
                    module_aliases,
                    entity_aliases,
                )
                dependencies[module_path][entity.name] = self._deduplicate(entity_deps)

        return dependencies

    def get_entity_metadata(self, modules_data: Dict) -> Dict:
        data = {}
        for module_path, module_data in modules_data.items():
            data[module_path] = {}
            for entity in module_data.entities:
                lines = 0
                if entity.lineno and entity.endno:
                    lines = entity.endno - entity.lineno + 1

                entity_type = "function"
                if isinstance(entity, Class):
                    entity_type = "class"
                elif isinstance(entity, (Function, AsyncFunction)):
                    entity_type = "function"

                data[module_path][entity.name] = {
                    "lines": lines,
                    "entity_type": entity_type,
                    "lineno": entity.lineno,
                    "endno": entity.endno,
                }
        return data

    def _read_file_content(self, path: Text) -> Text:
        with open(path, "r+", encoding="utf-8") as file_read:
            return file_read.read()

    def _parse_source(self, source: Text, filename: Text):
        if self._major == 2:
            if ast27 is None:
                raise ImportError("typed_ast is required to parse Python 2 source code.")
            return ast27.parse(source, filename=filename, mode="exec")

        return self._parse_with_feature_version(source, filename, self._feature_version)

    def _parse_with_feature_version(self, source: Text, filename: Text, feature_version: Optional[int]):
        if feature_version is None:
            return ast.parse(source, filename=filename, mode="exec")
        try:
            return ast.parse(
                source,
                filename=filename,
                mode="exec",
                feature_version=feature_version,
            )
        except TypeError:
            return ast.parse(source, filename=filename, mode="exec")

    def _parse_python_version(self, version: Optional[str]) -> Tuple[int, Optional[int]]:
        if not version:
            return 3, None
        parts = version.split(".")
        try:
            major = int(parts[0])
        except ValueError:
            return 3, None
        minor = None
        if len(parts) > 1:
            try:
                minor = int(parts[1])
            except ValueError:
                minor = None
        return major, minor

    def _extract_entities(self, ast_tree, filename: Text) -> (List[object], Dict[str, object]):
        entities: List[object] = []
        entity_nodes: Dict[str, object] = {}
        ast_mod = self._ast_mod
        async_def = getattr(self._ast_mod, "AsyncFunctionDef", None)

        for node in getattr(ast_tree, "body", []):
            if isinstance(node, self._ast_mod.FunctionDef):
                func = Function(node.name, filename, node.lineno)
                func.endno = self._get_end_lineno(node, self._ast_mod)
                entities.append(func)
                entity_nodes[node.name] = node
            elif async_def and isinstance(node, async_def):
                func = AsyncFunction(node.name, filename, node.lineno)
                func.endno = self._get_end_lineno(node, self._ast_mod)
                entities.append(func)
                entity_nodes[node.name] = node
            elif isinstance(node, self._ast_mod.ClassDef):
                bases = [self._get_name_from_expr(base, ast_mod) for base in node.bases]
                bases = [b for b in bases if b]
                cls = Class(node.name, bases, filename, node.lineno)
                cls.endno = self._get_end_lineno(node, self._ast_mod)
                entities.append(cls)
                entity_nodes[node.name] = node

        return entities, entity_nodes

    def _collect_imports(self, ast_tree) -> ImportInfo:
        module_aliases: Dict[str, str] = {}
        entity_aliases: Dict[str, str] = {}
        module_imports: Set[str] = set()
        ast_mod = self._ast_mod

        for node in getattr(ast_tree, "body", []):
            if isinstance(node, ast_mod.Import):
                for alias in node.names:
                    full_name = alias.name
                    alias_name = alias.asname or full_name.split(".")[0]
                    resolved = self._resolve_imported_module(full_name)
                    if resolved:
                        module_aliases[alias_name] = resolved
                        module_imports.add(resolved)
            elif isinstance(node, ast_mod.ImportFrom):
                base = node.module or ""
                for alias in node.names:
                    name = alias.name
                    alias_name = alias.asname or name
                    full_name = f"{base}.{name}" if base else name
                    resolved = self._resolve_imported_module(full_name)
                    if resolved:
                        module_imports.add(resolved)
                    entity_aliases[alias_name] = full_name

        return ImportInfo(
            module_aliases=module_aliases,
            entity_aliases=entity_aliases,
            module_imports=module_imports,
        )

    def _resolve_imported_module(self, full_name: str) -> Optional[str]:
        parts = full_name.split(".")
        for i in range(len(parts) - 1, -1, -1):
            candidate = parts[i]
            if candidate in self._module_names_set:
                return candidate
        return None

    def _collect_dependencies_in_module(
        self,
        ast_tree,
        local_entities: Set[str],
        module_aliases: Dict[str, str],
        entity_aliases: Dict[str, str],
    ) -> List[str]:
        deps: List[str] = []
        ast_mod = self._ast_mod
        collector = self._make_dependency_collector(local_entities, module_aliases, entity_aliases, ast_mod)
        for node in getattr(ast_tree, "body", []):
            if isinstance(node, (ast_mod.FunctionDef, ast_mod.ClassDef)):
                continue
            async_def = getattr(self._ast_mod, "AsyncFunctionDef", None)
            if async_def and isinstance(node, async_def):
                continue
            collector.visit(node)
        deps.extend(collector.dependencies)
        return deps

    def _collect_dependencies_in_entity(
        self,
        node,
        local_entities: Set[str],
        module_aliases: Dict[str, str],
        entity_aliases: Dict[str, str],
    ) -> List[str]:
        deps: List[str] = []
        ast_mod = self._ast_mod

        if isinstance(node, ast_mod.ClassDef):
            for base in node.bases:
                if isinstance(base, ast_mod.Attribute):
                    dep = self._resolve_attribute(base, local_entities, module_aliases, entity_aliases, ast_mod)
                elif isinstance(base, ast_mod.Name):
                    dep = self._resolve_name(base.id, local_entities, module_aliases, entity_aliases)
                else:
                    dep = None
                if dep:
                    deps.append(dep)
            collector = self._make_dependency_collector(local_entities, module_aliases, entity_aliases, ast_mod)
            for child in node.body:
                collector.visit(child)
            deps.extend(collector.dependencies)
            return deps

        collector = self._make_dependency_collector(local_entities, module_aliases, entity_aliases, ast_mod)
        collector.visit(node)
        deps.extend(collector.dependencies)
        return deps

    def _make_dependency_collector(self, local_entities, module_aliases, entity_aliases, ast_mod):
        parser = self

        class DependencyCollector(ast_mod.NodeVisitor):
            def __init__(self):
                self.dependencies: List[str] = []

            def visit_Call(self, call_node):
                dep = parser._resolve_call_target(
                    call_node.func, local_entities, module_aliases, entity_aliases, ast_mod
                )
                if dep:
                    self.dependencies.append(dep)
                self.generic_visit(call_node)

        return DependencyCollector()

    def _resolve_call_target(
        self,
        func_node,
        local_entities: Set[str],
        module_aliases: Dict[str, str],
        entity_aliases: Dict[str, str],
        ast_mod,
    ) -> Optional[str]:
        if isinstance(func_node, ast_mod.Name):
            return self._resolve_name(func_node.id, local_entities, module_aliases, entity_aliases)
        if isinstance(func_node, ast_mod.Attribute):
            return self._resolve_attribute(func_node, local_entities, module_aliases, entity_aliases, ast_mod)
        return None

    def _resolve_attribute(
        self,
        node,
        local_entities: Set[str],
        module_aliases: Dict[str, str],
        entity_aliases: Dict[str, str],
        ast_mod,
    ) -> Optional[str]:
        parts = self._flatten_attribute(node, ast_mod)
        if not parts:
            return None
        base = parts[0]
        if base in module_aliases:
            module_name = module_aliases[base]
            suffix = ".".join(parts[1:])
            return f"{module_name}.{suffix}" if suffix else module_name
        if base in entity_aliases:
            base_name = entity_aliases[base]
            suffix = ".".join(parts[1:])
            return f"{base_name}.{suffix}" if suffix else base_name
        if base in local_entities:
            return base
        return None

    def _resolve_name(
        self,
        name: str,
        local_entities: Set[str],
        module_aliases: Dict[str, str],
        entity_aliases: Dict[str, str],
    ) -> Optional[str]:
        if name in entity_aliases:
            return entity_aliases[name]
        if name in local_entities:
            return name
        if name in module_aliases:
            return module_aliases[name]
        return None

    def _flatten_attribute(self, node, ast_mod) -> List[str]:
        parts: List[str] = []
        while isinstance(node, ast_mod.Attribute):
            parts.insert(0, node.attr)
            node = node.value
        if isinstance(node, ast_mod.Name):
            parts.insert(0, node.id)
            return parts
        return []

    def _get_name_from_expr(self, node, ast_mod) -> Optional[str]:
        if isinstance(node, ast_mod.Name):
            return node.id
        if isinstance(node, ast_mod.Attribute):
            parts = self._flatten_attribute(node, ast_mod)
            return ".".join(parts) if parts else None
        return None

    def _get_end_lineno(self, node, ast_mod) -> int:
        end_lineno = getattr(node, "end_lineno", None)
        if end_lineno:
            return end_lineno
        max_lineno = getattr(node, "lineno", 0) or 0
        for child in ast_mod.walk(node):
            lineno = getattr(child, "lineno", None)
            if lineno and lineno > max_lineno:
                max_lineno = lineno
        return max_lineno

    def _deduplicate(self, items: List[str]) -> List[str]:
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
