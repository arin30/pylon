import ast
import builtins

from rules.base import Finding


BUILTIN_NAMES = frozenset(name for name in dir(builtins) if not name.startswith('_'))


def find_shadowed_builtins(filepath: str) -> list[Finding]:
    """Find parameter and assignment names that shadow Python builtins."""
    with open(filepath) as f:
        tree = ast.parse(f.read())

    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            name = node.arg
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
        else:
            continue

        if name in BUILTIN_NAMES:
            result.append(Finding(
                rule_id='shadowed-builtin',
                message=f"'{name}' shadows a Python builtin",
                line=node.lineno,
            ))

    result.sort(key=lambda finding: finding.line)
    return result
