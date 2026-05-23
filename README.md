# yidl-lifecycle

Lifecycle decorator and transactional lifecycle runtime built on YIDL.

This repository is being split out of `yidl` so lifecycle can act as a real
downstream compiler package while `yidl` stays focused on the generic compiler
substrate.

## Development

From this repository root:

```bash
PYTHONPATH=../astichi/src uv run pytest -q
```

The project is expected to use the sibling `../yidl` checkout during local
development.

