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



def test_ai_package_does_not_import_persistence_or_sqlalchemy():
    ai_root = Path(__file__).resolve().parents[1] / "app" / "opencoach" / "ai"
    violations = []

    for source in ai_root.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)

            for module in modules:
                if (
                    module == "sqlalchemy"
                    or module.startswith("sqlalchemy.")
                    or module == "opencoach.database"
                    or module.startswith("opencoach.database.")
                ):
                    relative = source.relative_to(ai_root)
                    violations.append(f"{relative}:{node.lineno} -> {module}")

    assert not violations, (
        "Le package IA ne doit pas dépendre de la persistance :\n"
        + "\n".join(sorted(set(violations)))
    )



def test_core_coach_api_does_not_import_the_ai_package():
    api_root = Path(__file__).resolve().parents[1] / "app" / "opencoach" / "api"
    sources = [
        api_root / "coach.py",
        *(api_root / "coaching").rglob("*.py"),
    ]
    violations = []

    for source in sources:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                if module == "opencoach.ai" or module.startswith("opencoach.ai."):
                    violations.append(f"{source.relative_to(api_root)}:{node.lineno} -> {module}")

    assert not violations, (
        "Les routes Coach principales doivent rester utilisables sans le moteur IA :\n"
        + "\n".join(sorted(set(violations)))
    )
