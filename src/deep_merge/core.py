"""Core merge logic for the deep_merge library.

The library merges nested mappings (dicts) with explicit, predictable rules
for how lists and null/None values interact during the merge. There is one
tun knob exposed: `list_strategy`, because list-merging is where every merge
library diverges in behaviour. We chose to make it explicit rather than pick
a silent default that surprises callers.

Design decisions (see README for the user-facing summary):

- Mappings are merged recursively, key by key.
- If both values at a key are mappings, we recurse.
- If both values are lists, the `list_strategy` decides: `replace` (right
  wins, the default) or `concatenate` (left then right).
- If exactly one side is None, the non-None side wins. This is deliberate:
  a null in a config overlay should not wipe out a base value. If you want
  to null something out, you need to handle that in your own code; this
  library does not infer intent from nulls.
- If types differ and neither is None, the right side replaces the left.
  This is the least surprising rule: the overlay is authoritative for
  scalar-vs-scalar conflicts where we cannot meaningfully merge.
- The base is never mutated. We always copy mappings so callers can reuse
  the inputs safely.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class MergeConfig:
    """Configuration for :func:`deep_merge`.

    Currently the only tun is ``list_strategy`` because that is the only place
    where sensible libraries genuinely disagree. Exposing just this keeps the
    surface small while letting callers pick the list behaviour they need.

    Parameters
    ----------
    list_strategy:
        One of ``"replace"`` or ``"concatenate"``. ``"replace"`` (default)
        means the right-hand list replaces the left; ``"concatenate"`` means
        the left list is extended with the right. Any other value raises
        ``ValueError`` at merge time, which is preferable to silently doing
        something unexpected.
    """

    __slots__ = ("list_strategy",)

    def __init__(self, list_strategy: str = "replace") -> None:
        self.list_strategy = list_strategy

    def _validate(self) -> None:
        if self.list_strategy not in ("replace", "concatenate"):
            raise ValueError(
                "list_strategy must be 'replace' or 'concatenate', got "
                f"{self.list_strategy!r}"
            )


def _merge_lists(left: list, right: list, strategy: str) -> list:
    if strategy == "replace":
        # Return a shallow copy of right so the caller cannot mutate the
        # overlay's list through the merged result.
        return list(right)
    # concatenate
    return [*left, *right]


def _deep_merge_impl(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    config: MergeConfig,
) -> dict:
    # Start from a shallow copy of the left mapping. We do NOT deepcopy the
    # entire left here because we will selectively copy as we descend, which
    # avoids copying values that will simply be replaced by the right side.
    result: dict = dict(left)

    for key, right_val in right.items():
        if key not in result:
            # Key only in right. Deep copy so the merged structure does not
            # alias the overlay's nested structures.
            result[key] = deepcopy(right_val)
            continue

        left_val = result[key]

        # None handling: a None on either side yields the non-None side.
        if left_val is None and right_val is None:
            result[key] = None
            continue
        if left_val is None:
            result[key] = deepcopy(right_val)
            continue
        if right_val is None:
            # left_val stays as-is; already not aliased to a fresh dict we own
            # only if it came from `dict(left)`. To be safe against the caller
            # mutating left later, deep copy nested structures.
            result[key] = deepcopy(left_val)
            continue

        # Both non-None. Decide based on types.
        if isinstance(left_val, Mapping) and isinstance(right_val, Mapping):
            result[key] = _deep_merge_impl(left_val, right_val, config)
        elif isinstance(left_val, list) and isinstance(right_val, list):
            result[key] = _merge_lists(left_val, right_val, config.list_strategy)
        else:
            # Type mismatch or unmergeable scalars: right wins.
            result[key] = deepcopy(right_val)

    return result


def deep_merge(
    base: Mapping[str, Any],
    overlay: Mapping[str, Any],
    config: MergeConfig | None = None,
) -> dict:
    """Merge two mappings recursively and return a new dict.

    Neither ``base`` nor ``overlay`` is mutated. The returned dict is a fresh
    structure; nested dicts/lists are copied as needed so that later mutation
    of the inputs cannot affect the result.

    Parameters
    ----------
    base:
        The starting mapping. Values here are defaults.
    overlay:
        The mapping layered on top of ``base``. Values here win except where
        the merge rules recurse (both sides mappings) or concatenate lists.
    config:
        Optional :class:`MergeConfig`. If ``None``, a default config with
        ``list_strategy='replace'`` is used.

    Returns
    -------
    dict
        A freshly-allocated dict containing the merged data.

    Raises
    ------
    ValueError
        If ``config.list_strategy`` is not a recognised value.
    """
    if config is None:
        config = MergeConfig()
    config._validate()
    return _deep_merge_impl(base, overlay, config)
