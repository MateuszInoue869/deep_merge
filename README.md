# Deep Merge

Merge nested mappings (dicts) with explicit rules for lists and nulls. Standard library only, no dependencies.

```python
from deep_merge import deep_merge, MergeConfig

base = {"server": {"host": "localhost", "ports": [8080]}}
overlay = {"server": {"ports": [9090], "debug": True}}

merged = deep_merge(base, overlay)
# {'server': {'host': 'localhost', 'ports': [9090], 'debug': True}}

merged = deep_merge(base, overlay, MergeConfig(list_strategy="concatenate"))
# {'server': {'host': 'localhost', 'ports': [8080, 9090], 'debug': True}}
```

## Why

Every config-merge library eventually has to answer two questions: what happens to lists, and what does `null` mean. This library picks one answer for each and stops there.

- **Lists**: by default the overlay's list replaces the base list. If you pass `MergeConfig(list_strategy="concatenate")`, lists are joined left-to-right instead. There is no deduplication, no smart set-union, no type-aware element merging — both behaviours are simple and predictable.
- **Nulls**: a `None` on either side yields the non-`None` side. This means an overlay cannot blank out a base value by passing `null`. The reasoning is that `null` in a config overlay is ambiguous: it could mean "unset this" or "I have no opinion". This library treats it as "I have no opinion", because the other reading is more dangerous and easy to do explicitly by deleting the key before merging.

The trade-off: this library will not suit you if you need set semantics for lists, or if you want `null` to erase values. Both are real needs; they are just not what this library does.

## Edge you will hit

If the base and overlay disagree on type at a key (e.g. base has a list, overlay has a scalar), the overlay wins outright — there is no attempt to coerce. This is deliberate: silent coercion in a merge tool is how good configs get quietly corrupted. If you need to change a value's shape, do it in your own code where you can see it.

## API

- `deep_merge(base, overlay, config=None) -> dict` — the single entry point. Returns a fresh dict; inputs are not mutated.
- `MergeConfig(list_strategy="replace")` — the only configuration object. `list_strategy` accepts `"replace"` (default) or `"concatenate"`; any other value raises `ValueError` at merge time.

## Running the tests

```
PYTHONPATH=src python -m unittest discover -s tests
```
