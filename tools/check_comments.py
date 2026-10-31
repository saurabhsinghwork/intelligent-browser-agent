"""Audit executable statement documentation without changing source files."""
# Parse Python syntax rather than counting blank or multiline continuation lines.
import ast
# Inspect only version-controlled-style source folders, not dependencies or runtime profiles.
from pathlib import Path
# Keep output grouped by owned source file.
findings = {}
# Walk production code and the application entry point.
paths = [Path("app.py")] + [path for folder in ("agent", "browser", "config", "domain", "models", "services", "ui") for path in Path(folder).glob("*.py")]
# Inspect each source without importing or executing it.
for path in paths:
    # Read UTF-8 source with optional older BOM compatibility.
    source = path.read_text(encoding="utf-8-sig")
    # Keep physical lines for preceding explanatory comments.
    lines = source.splitlines()
    # Parse the actual module syntax.
    tree = ast.parse(source)
    # Every file should explain its role.
    issues = [] if ast.get_docstring(tree) else ["module docstring missing"]
    # Inspect real statements rather than braces or multiline arguments.
    for node in ast.walk(tree):
        # Every public/private helper deserves a purpose description.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not ast.get_docstring(node):
            # Record the concrete missing documentation location.
            issues.append(f"{node.lineno}: {getattr(node,'name','')} docstring missing")
        # Skip text docstrings themselves and multiline expression continuations.
        if not isinstance(node, ast.stmt) or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            # Definitions are covered by their own docstrings above.
            continue
        # The preceding meaningful line should explain this operation.
        prior = node.lineno - 2
        # Ignore blank separation while locating its explanation.
        while prior >= 0 and not lines[prior].strip():
            # Keep searching only backward, without executing code.
            prior -= 1
        # A same-line comment is an equivalent explicit explanation.
        if prior >= 0 and not lines[prior].lstrip().startswith("#") and " #" not in lines[node.lineno-1]:
            # Report enough original text for a human to add a meaningful explanation.
            issues.append(f"{node.lineno}: {lines[node.lineno-1].strip()[:95]}")
    # Keep the report concise by excluding fully documented modules.
    if issues:
        # Retain per-file documentation findings.
        findings[str(path)] = issues
# Print only source documentation findings, never runtime configuration or secrets.
print(findings)
