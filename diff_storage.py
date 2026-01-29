"""
Порівняти два storage-dumps і показати, що змінилося.
"""

import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def diff_dict(a: dict, b: dict):
    keys = set(a.keys()) | set(b.keys())
    changed = []
    for k in sorted(keys):
        if a.get(k) != b.get(k):
            changed.append((k, a.get(k), b.get(k)))
    return changed


def main(a_path: str, b_path: str):
    a = load(Path(a_path))
    b = load(Path(b_path))

    print("=== Cookies diff (by name) ===")
    a_c = {c["name"]: c.get("value") for c in a.get("cookies", [])}
    b_c = {c["name"]: c.get("value") for c in b.get("cookies", [])}
    for name, av, bv in diff_dict(a_c, b_c):
        print(f"{name}: {av} -> {bv}")

    print("\n=== localStorage diff ===")
    for name, av, bv in diff_dict(a.get("localStorage", {}), b.get("localStorage", {})):
        print(f"{name}: {av} -> {bv}")

    print("\n=== sessionStorage diff ===")
    for name, av, bv in diff_dict(a.get("sessionStorage", {}), b.get("sessionStorage", {})):
        print(f"{name}: {av} -> {bv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", required=True, help="Файл стану A")
    parser.add_argument("--b", required=True, help="Файл стану B")
    args = parser.parse_args()
    main(args.a, args.b)
