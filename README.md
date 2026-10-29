## Pylon

Pylon is a static analysis CLI for Python that flags real issues in your code and, on request, explains them and suggests fixes using an LLM.

Pylon mostly utilises Python's included [ast module](https://docs.python.org/3/library/ast.html) to traverse source code.

Built in collaboration with [Soham200613](https://github.com/Soham200613) and [GraydenDonaldson](https://github.com/GraydenDonaldson)

## Implemented rules

- **Unused imports**: imports that are never referenced. Correctly handles Python's re-export idioms (`from .app import Flask as Flask`, `__all__ = [...]`) so it doesn't flag deliberate public re-exports as dead code.
- **Mutable default arguments**: `def f(x=[])` shares the same object across every call, a classic source of hard-to-trace bugs. Catches both literal syntax (`[]`, `{}`) and constructor calls (`list()`, `dict()`, `set()`).
- **Bare `except:` clauses**: catching all exceptions, including `KeyboardInterrupt` and `SystemExit`, silently swallows bugs. Recognizes and skips the deliberate catch-and-reraise pattern (`except: ... raise`), rather than flagging every bare except indiscriminately.
- **Wildcard imports**: `from module import *` pollutes the namespace and makes it impossible to tell where a name came from.
- **Comparing with `==` instead of `is` for `None`/`True`/`False`** — non-idiomatic and can misbehave with custom `__eq__`. Check `ast.Compare` nodes where one side is an `ast.Constant` with value `None`/`True`/`False` and the operator is `Eq`/`NotEq`.
- **Shadowed funcions/methods/class definitions**: functions later shadowed without an @overload stub and other exceptions are silently shadowed by python

- **Shadowed builtins**: parameters and variable bindings named `list`, `dict`, `id`, `type`, etc. hide Python's builtins. Attribute names and ordinary builtin references are not flagged.

## Rules yet to be implemented

- **Excessive function arguments**: functions with too many parameters are hard to maintain and often signal the function is doing too much.
- **Unused function arguments**: parameters never referenced in the function body, often signaling incomplete refactoring. Same "walk and collect `ast.Name` usages" pattern as unused imports, applied per-function.
- **Global variable mutation inside functions**: using `global` to mutate outer-scope state is a common source of hard-to-trace bugs. Check for `ast.Global` nodes within functions.
- **Deeply nested code (high cyclomatic complexity)**: functions with many nested `if`/`for`/`while`/`try` blocks are hard to read and test. Requires tracking nesting depth/branch count while walking, rather than matching a single node type.
- **Redefining function in same scope**: functions that are later redefined in the same scope silently shadow, hinting to dead code
- **Format-string arg count mismatch**: `%` operator and `logging` calls with a mismatch in the number of format requests and args supplied

## LLM layer

Passing `--explain` sends each finding, along with its surrounding source code, to an LLM for a short, specific judgment on whether it's a genuine issue or a likely false positive. This is deliberately kept separate from the deterministic rule engine: rules encode patterns worth hard-coding that have few special deliberate cases, while the LLM layer handles judgment calls that don't generalize cleanly into a fixed rule. For example, correctly identifying that an unused `from __future__ import annotations` import is not actually dead code, despite never appearing as a referenced name in its respective file.

Supports multiple providers behind a shared interface — local models via [ollama](https://ollama.com) for fast, free iteration, or Anthropic/OpenAI for production-quality explanations:

```bash
pylon path/to/file.py --explain --provider ollama   # default
pylon path/to/file.py --explain --provider anthropic
pylon path/to/file.py --explain --provider openai
pylon path/to/file.py --explain # will use default ollama qwen2.5:7b-coder
```

Note that users of openai/anthropic models should add their respective API keys to `.env.example` and then rename to `.env`

## Installation, in current non-published state from source code
```bash
git clone https://github.com/Anonymoose725/pylon.git
cd pylon
python3 -m venv .venv
source .venv/bin/activate # for linux/mac, or .venv\Scripts\activate on Windows
pip install -e .
```

## Detailed setup, for contributors

Clone the repo:
```bash
git clone https://github.com/Anonymoose725/pylon.git
cd pylon
```

Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies from requirements.txt:
```bash
pip install -r requirements.txt
```

Run the test suite to confirm everything works:
```bash
pytest testing/ -v
```

## Milestones & metrics

Validated against 5 actively maintained production codebases to confirm the tool works at real scale and to catch genuine false-positive patterns before they'd be found by an actual user.

| Repo | Files | Lines | Findings |
|---|---|---|---|
| Flask | 24 | 9,513 | 32 |
| Requests | 19 | 6,394 | 56 |
| Click | 17 | 12,821 | 19 |
| Django | 907 | 165,529 | 198 |
| NumPy | 428 | 260,868 | 764 |
| **Total** | **1,395** | **455,125** | **1,069** |

- **Reduced false-positive unused-import findings by 34%** (1,479 → 976) by diagnosing and fixing two Python re-export idioms (`from x import Y as Y` and `__all__` re-exports) that the AST-based detector initially misread as dead code
- **Correctly identified a genuine bare-except anti-pattern** in Flask's core WSGI dispatch logic (`app.py`), then refined the rule to distinguish safe catch-and-reraise handlers from true error suppression via AST-level exception analysis
- **Processes ~365 files/sec** (Django) and remains performant on dense, large codebases (~83 files/sec on NumPy's 260K-line source tree due to larger file sizes)
- Every rule is covered by positive *and* negative test cases (`pytest`) — proving each rule catches real issues without false-flagging safe, idiomatic code


## Roadmap

1. Implement the roadmap rules listed above!
2. Implement a --fat flag that assumes a user is testing on a large number of files/repos, compacting the large list of findings into a more digestible (and collapsible?) format, potentially outside the CLI
3. Add a false-positive flagging mechanism to the CLI, so users can mark findings as false positives, with and without having seen an `--explain` explanation first. This is the basis for measuring whether the LLM layer's context genuinely reduces false-positive flags in practice
4. Publish to PyPI under a distinct package name (`pylon`/`pylon-cli` are already taken)
