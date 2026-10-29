# def add_item(item, items=[]):
#     items.append(item)
#     return items
# "if no list is passed, start with an empty list."
# but in python, the same list is shared every time the function is called
# this means the default list grows as it accumulates new items
# avoid with ast detection!
from rules.base import Finding
import ast

def find_mutable_defaults(filepath: str) -> list[Finding]:
    """given a python file path, return a list of Findings for functions with mutable default arguments"""
    with open(filepath) as f:
        src = f.read()
    tree = ast.parse(src)
    
    result = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                # args is an argument node
                # defaults and kw_defaults cover positional and keyword-only values
                # check if default is a mutable literal  
                if is_mutable(default):
                    result.append(Finding(
                        rule_id="mutable-default",
                        message=f"Mutable default argument in function def '{node.name}'",
                        line=node.lineno
                    ))
    return result

def is_mutable(node):
    if isinstance(node, (ast.List, ast.Dict, ast.Set)):
        # if its a direct object of one of our mutable types
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        # if its a call to a function with id belonging to one of our mutable types
        # i.e. set(), which is an initialization returning an empty set
        return node.func.id in ("list", "dict", "set")
    return False