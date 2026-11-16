"""Garde-fou : les domaines OpenCoach restent utilisables sans le moteur IA."""

import ast
from pathlib import Path


def test_business_packages_do_not_import_the_ai_package():
    package_root = Path(__file__).resolve().parents[1] / "app" / "opencoach"
    violations = []

    for source in package_root.rglob("*.py"):
        relative = source.relative_to(package_root)
        if relative.parts[0] in {"ai", "api"}:
            continue

        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            imported_module = None
            if isinstance(node, ast.Import):
                imported_module = next(
                    (
                        alias.name
                        for alias in node.names
                        if alias.name == "opencoach.ai"
                        or alias.name.startswith("opencoach.ai.")
                    ),
                    None,
                )
            elif isinstance(node, ast.ImportFrom):
                imported_module = node.module
            elif isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "import_module"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                    and (
                        node.args[0].value == "opencoach.ai"
                        or node.args[0].value.startswith("opencoach.ai.")
                    )
                ):
                    imported_module = node.args[0].value

            if imported_module and (
                imported_module == "opencoach.ai"
                or imported_module.startswith("opencoach.ai.")
            ):
                violations.append(
                    f"{relative}:{getattr(node, 'lineno', '?')} -> {imported_module}"
                )

    assert not violations, (
        "Les domaines métier ne doivent pas dépendre du moteur IA :\n"
        + "\n".join(sorted(set(violations)))
    )
