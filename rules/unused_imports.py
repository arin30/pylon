from rules.base import Finding
import ast

def all_string_literals(value_node):
    """Pull string literals out of a list/tuple AST node — used for __all__ = [...]"""
    names = set()
    if isinstance(value_node, (ast.List, ast.Tuple)):
        for elt in value_node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                names.add(elt.value)
    return names

def find_unused_imports(filepath: str) -> list[Finding]:
    """Given a Python file path, return a list of Findings, import names that are never used"""
    # get tree
    with open(filepath) as f:
        source = f.read() # string
    tree = ast.parse(source)
    
    # get list of imports
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for name in node.names:
                # check if .name or .asname (import os || import os as opersys)
                if name.asname is not None and name.asname == name.name:
                    continue # skip for deliberate pattern "import X as "
                # Plain dotted imports bind the top-level package; aliases and
                # from-imports bind the explicitly imported name.
                bound_name = name.asname or (name.name.split('.')[0] if isinstance(node, ast.Import) else name.name)
                imported[name.asname or name.name] = (node.lineno, bound_name)
    
    # every time code references a name: os.path.join(), path.exists(),... parser creates ast.Name with .id attribute
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)

        # __all__ = list of strings
        # names listed in __all__ = [...] or __all__ += [...] count as "used"
        # this catches the re-export-via-__all__ idiom (e.g. in numpy's __init__.py),
        # since those names never appear as an ast.Name, and only as string literals
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    used_names |= all_string_literals(node.value) # union
        if isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__":
                used_names |= all_string_literals(node.value)
    
    # compare
    result = []
    for name, (lineno, bound_name) in imported.items():
        if bound_name not in used_names:
            # unused import: create a Finding
            result.append(Finding(
                rule_id="unused-import",
                message=f"Unused import from '{name}'",
                line=lineno
            ))
    
    return result