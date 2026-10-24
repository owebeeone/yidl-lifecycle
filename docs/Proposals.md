# Proposed constructor aliases

These options are not implemented in the released marker API.


Constructor spelling could differ from the property name:

```python
_slot_id: object = const(init_name="slot_id", default=None)
```

The proposed constructor accepts `slot_id`; the property remains `_slot_id`.
This creates no `slot_id` property or factory provider. `init_name` defaults
to the declared field name for new fields and inherits on overrides. `const`
defaults to `init=True`, so the example satisfies the prerequisite. An explicit
non-`None` alias requires `init=True`; `init=False` with the default `init_name=None`
still creates no constructor parameter. Duplicate constructor names and
inherited renaming are rejected.
Existing markers currently reject this new option; use the existing initvar
and copying-factory pattern until it is implemented.
