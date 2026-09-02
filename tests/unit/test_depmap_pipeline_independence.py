"""FR-017: the reproducible analysis pipeline must gain no dependency on this server.

The companion S-prime pipeline achieves byte-reproducibility by reading checksum-pinned
release files. A live call from inside it would break that guarantee silently, and the
failure would show up as irreproducible published numbers rather than as a test failure.

This repository cannot import the pipeline, so the invariant is enforced from this side:
the DepMap modules must not reach toward the pipeline, and the server must say so where a
future contributor will read it. What this cannot prove is the converse, that the pipeline
never imports this package; that has to be enforced in the pipeline's own suite.
"""

import ast
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.depmap]

SRC = Path(__file__).resolve().parents[2] / "src" / "lifesciences_mcp"
DEPMAP_MODULES = [
    SRC / "models" / "depmap.py",
    SRC / "clients" / "depmap.py",
    SRC / "servers" / "depmap.py",
]

ALLOWED_TOP_LEVEL = {
    # standard library
    "ast",
    "asyncio",
    "collections",
    "json",
    "math",
    "pathlib",
    "re",
    "typing",
    # declared dependencies
    "httpx",
    "pydantic",
    "fastmcp",
    # this package
    "lifesciences_mcp",
}


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize("module", DEPMAP_MODULES, ids=lambda p: p.name)
def test_no_import_reaches_outside_the_declared_dependencies(module: Path):
    """A new import is how a pipeline coupling would arrive; this makes it visible."""
    unexpected = _imported_roots(module) - ALLOWED_TOP_LEVEL
    assert not unexpected, (
        f"{module.name} imports {sorted(unexpected)}, which is not a declared dependency. "
        f"If this is intentional, add it to pyproject.toml and to ALLOWED_TOP_LEVEL here."
    )


@pytest.mark.parametrize("module", DEPMAP_MODULES, ids=lambda p: p.name)
def test_no_filesystem_path_into_the_pipeline(module: Path):
    """Prose references to the pipeline are fine; a path or import is not."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        text = node.value.strip()
        # A path constant has a separator and no whitespace. Documentation naming the
        # pipeline is provenance, and is exactly what should stay.
        if any(ch.isspace() for ch in text):
            continue
        if "sprime" in text.lower() and ("/" in text or "\\" in text):
            pytest.fail(f"{module.name} contains a path into the analysis pipeline: {node.value!r}")


def test_server_states_the_invariant():
    """The rule has to be readable where someone would otherwise break it."""
    docstring = ast.get_docstring(ast.parse((SRC / "servers" / "depmap.py").read_text("utf-8")))
    assert docstring is not None
    lowered = docstring.lower()
    assert "pipeline" in lowered
    assert "file-based" in lowered or "no dependency" in lowered
