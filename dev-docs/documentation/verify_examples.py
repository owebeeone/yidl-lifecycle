"""Execute the user-facing examples against the installed library."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[2]
GUIDES = (
    "README.md", "docs/GettingStarted.md", "docs/Concepts.md",
    "docs/Collections.md", "docs/Transactions.md", "docs/Initialization.md",
    "docs/Hooks.md", "docs/Resources.md",
)


def check():
    examples = sorted((ROOT / "examples").glob("*.py"))
    for path in examples:
        with redirect_stdout(io.StringIO()):
            runpy.run_path(str(path), run_name="__main__")
        print("PASS", path.relative_to(ROOT))

    count = 0
    for name in GUIDES:
        path = ROOT / name
        markdown = path.read_text()
        namespace = {"__name__": "__main__", "__file__": str(path)}
        captured = io.StringIO()
        with redirect_stdout(captured):
            for block in re.findall(r"```python\n(.*?)```", markdown, re.S):
                exec(compile(block, str(path), "exec"), namespace)
                count += 1
        for expected in re.findall(r"```text\n(.*?)```", markdown, re.S):
            if expected.strip() not in captured.getvalue():
                raise AssertionError(f"Documented output differs: {name}")
        print("PASS guide", name)
    evidence = {"examples": len(examples), "guide_blocks": count}
    output = ROOT / "build/docs-example-evidence.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence


if __name__ == "__main__":
    print(json.dumps(check(), sort_keys=True))
