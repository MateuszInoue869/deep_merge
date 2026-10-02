"""Deep Merge: a small, focused library for merging nested mappings.

Re-exports the single public entry point `deep_merge` and the configuration
dataclass `MergeConfig`.
"""

from deep_merge.core import MergeConfig, deep_merge

__all__ = ["MergeConfig", "deep_merge"]
