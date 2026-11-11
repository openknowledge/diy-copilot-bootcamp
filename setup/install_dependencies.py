"""Installs the workshop dependencies into the Python environment that runs this script.

Used by the setup cell of the notebooks in Google Colab:

    python setup/install_dependencies.py

Why not simply `uv sync`?
- `uv sync` installs into a separate virtual environment (.venv), which the notebook
  kernel doesn't see. We have to install into the kernel's own environment.
- `uv sync` installs exactly the locked versions of *all* packages. In Colab this would
  replace preinstalled packages like numpy or pandas, which Colab itself depends on.

What this script does instead:
1. Export the locked versions from uv.lock (without the `dev` group, which contains
   Jupyter and is only needed locally).
2. Drop the packages that are already installed in this environment, so Colab keeps its
   own versions of them.
3. Install the dependencies from pyproject.toml with uv, using the remaining locked
   versions as constraints. Our packages (litellm, mcp, chromadb, ...) therefore get
   exactly the versions the workshop was tested with.
"""

import importlib.metadata
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def normalize(name: str) -> str:
    """Normalizes a package name (PEP 503), e.g. 'Google_ADK' -> 'google-adk'."""
    return re.sub(r"[-_.]+", "-", name).lower()


def main() -> None:
    if shutil.which("uv") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"], check=True)

    installed = {normalize(d.metadata["Name"]) for d in importlib.metadata.distributions() if d.metadata["Name"]}

    locked = subprocess.run(
        ["uv", "export", "--frozen", "--no-dev", "--no-hashes", "--no-emit-project", "--no-header", "--no-annotate"],
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    constraints, kept = [], []
    for line in locked.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = normalize(re.split(r"[=<>!~;\[ ]", line, maxsplit=1)[0])
        if name in installed:
            kept.append(name)
        else:
            constraints.append(line)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as file:
        file.write("\n".join(constraints))
        constraints_file = file.name

    subprocess.run(
        [
            "uv", "pip", "install",
            "--python", sys.executable,
            "-r", str(REPO_DIR / "pyproject.toml"),
            "-c", constraints_file,
            "-q",
        ],
        check=True,
    )
    print(
        f"Installed the workshop dependencies ({len(constraints)} packages pinned to uv.lock, "
        f"{len(kept)} already provided by the environment)."
    )


if __name__ == "__main__":
    main()
