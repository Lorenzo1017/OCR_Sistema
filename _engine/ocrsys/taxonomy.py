from pathlib import Path
import yaml


class Taxonomy:
    def __init__(self, paths: set):
        self._paths = paths

    @classmethod
    def load(cls, yaml_path: Path) -> "Taxonomy":
        data = yaml.safe_load(yaml_path.read_text()) or {}
        return cls(cls._flatten(data))

    @staticmethod
    def _flatten(node, prefix="") -> set:
        paths = set()
        if isinstance(node, dict):
            for key, child in node.items():
                p = f"{prefix}/{key}" if prefix else key
                child_paths = Taxonomy._flatten(child, p)
                if child_paths:
                    paths |= child_paths
                else:
                    paths.add(p)
        elif isinstance(node, list):
            if not node:
                if prefix:
                    paths.add(prefix)
            else:
                for leaf in node:
                    paths.add(f"{prefix}/{leaf}")
        return paths

    def valid_paths(self) -> set:
        return set(self._paths)

    def is_valid(self, path: str) -> bool:
        return bool(path) and path in self._paths
