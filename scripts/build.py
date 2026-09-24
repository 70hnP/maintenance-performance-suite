#!/usr/bin/env python3
"""Build reproducible data artifacts and embed the payload in the HTML app."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "dataset.json"
HTML = ROOT / "src" / "mockup" / "index.html"


def main() -> int:
    subprocess.run([sys.executable, "data/generate_synthetic.py"], cwd=ROOT, check=True)
    payload = json.loads(DATASET.read_text(encoding="utf-8"))
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    html = HTML.read_text(encoding="utf-8")
    pattern = r'(<script id="ds" type="application/json">).*?(</script>)'
    updated, count = re.subn(pattern, lambda match: match.group(1) + compact + match.group(2), html, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("No se encontró un único bloque de dataset embebido en el mockup")
    HTML.write_text(updated, encoding="utf-8", newline="\n")
    print(f"OK - build reproducible - {len(payload['ordenes'])} ordenes - HTML sincronizado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
