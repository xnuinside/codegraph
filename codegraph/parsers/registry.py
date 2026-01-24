from typing import Dict, List, Type

from codegraph.parsers.base import BaseParser
from codegraph.parsers.python_parser import PythonParser
from codegraph.parsers.rust_parser import RustParser


_PARSERS: Dict[str, Type[BaseParser]] = {
    "python": PythonParser,
    "rust": RustParser,
}


def available_languages() -> List[str]:
    return sorted(_PARSERS.keys())


def get_parser(language: str, args=None) -> BaseParser:
    normalized = (language or "python").lower()
    if normalized not in _PARSERS:
        raise ValueError(f"Unsupported language: {language}")
    return _PARSERS[normalized](args=args)
