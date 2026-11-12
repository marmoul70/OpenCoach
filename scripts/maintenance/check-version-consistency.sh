#!/usr/bin/env bash

# Vérifie l'alignement des versions déclarées par OpenCoach.

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

python3 - "$PROJECT_ROOT" <<'PYTHON'
import json
import sys
import tomllib
from pathlib import Path

root = Path(sys.argv[1])
version_file = root / "VERSION"
pyproject_file = root / "pyproject.toml"
package_file = root / "frontend" / "package.json"
lock_file = root / "frontend" / "package-lock.json"

required = (version_file, pyproject_file, package_file, lock_file)
missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
if missing:
    raise SystemExit("Fichiers de version manquants : " + ", ".join(missing))

versions = {
    "VERSION": version_file.read_text(encoding="utf-8").strip(),
    "pyproject.toml": tomllib.loads(pyproject_file.read_text(encoding="utf-8"))["project"]["version"],
    "frontend/package.json": json.loads(package_file.read_text(encoding="utf-8"))["version"],
    "frontend/package-lock.json": json.loads(lock_file.read_text(encoding="utf-8"))["version"],
    "frontend/package-lock.json packages[\"\"]": json.loads(lock_file.read_text(encoding="utf-8"))["packages"][""]["version"],
}

for name, version in versions.items():
    print(f"{name}: {version}")

unique = set(versions.values())
if len(unique) != 1 or not next(iter(unique)):
    raise SystemExit("ERREUR : les versions OpenCoach ne sont pas cohérentes.")

print(f"[ OK ] Toutes les versions OpenCoach sont alignées : {next(iter(unique))}")
PYTHON
