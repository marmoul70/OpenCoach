#!/usr/bin/env bash

# Vérifie que le modèle local par défaut est cohérent entre les points d'entrée.

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

python3 - "$PROJECT_ROOT" <<'PYTHON'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
env_example = root / ".env.example"
installer = root / "scripts/bootstrap/install-ai.sh"
benchmark = root / "scripts/ai/benchmark_models.py"
evaluation = root / "docs/AI_MODEL_EVALUATION.md"

for path in (env_example, installer, benchmark, evaluation):
    if not path.is_file():
        raise SystemExit(f"Fichier requis absent : {path.relative_to(root)}")

env_text = env_example.read_text(encoding="utf-8")
installer_text = installer.read_text(encoding="utf-8")
benchmark_text = benchmark.read_text(encoding="utf-8")
evaluation_text = evaluation.read_text(encoding="utf-8")

def one(pattern: str, content: str, label: str) -> str:
    matches = re.findall(pattern, content, flags=re.MULTILINE)
    if len(matches) != 1:
        raise SystemExit(f"{label} : une seule déclaration attendue, {len(matches)} trouvée(s).")
    return matches[0]

configured = one(r"^OPENCOACH_AI_MODEL=(\S+)$", env_text, ".env.example")
installer_default = one(r'^DEFAULT_MODEL="([^"]+)"$', installer_text, "install-ai.sh")
benchmark_default = one(r'default=\[os\.getenv\("OPENCOACH_AI_MODEL", "([^"]+)"\)\]', benchmark_text, "benchmark_models.py")
documented = one(r"^\*\*Modèle actuellement ciblé :\*\* \x60([^\x60]+)\x60", evaluation_text, "AI_MODEL_EVALUATION.md")

values = {
    ".env.example": configured,
    "install-ai.sh": installer_default,
    "benchmark_models.py": benchmark_default,
    "AI_MODEL_EVALUATION.md": documented,
}
for label, value in values.items():
    print(f"{label}: {value}")

if len(set(values.values())) != 1:
    raise SystemExit("ERREUR : les modèles IA par défaut ne sont pas alignés.")

print(f"[ OK ] Modèle IA de référence cohérent : {configured}")
PYTHON
