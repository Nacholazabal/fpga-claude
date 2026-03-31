"""Vivado path discovery and subprocess runner."""

import glob
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path


CONFIG_DIR = Path.home() / ".fpga-claude"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def _save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def find_vivado() -> str:
    """Return path to the vivado executable, or raise RuntimeError."""
    cfg = _load_config()
    if "vivado_path" in cfg:
        p = cfg["vivado_path"]
        if Path(p).exists():
            return p
        # Cached path gone â€” re-discover
        del cfg["vivado_path"]

    path = _discover_vivado()

    cfg["vivado_path"] = path
    _save_config(cfg)
    return path


def _discover_vivado() -> str:
    is_windows = platform.system() == "Windows"

    # 1. Explicit env var override
    explicit = os.environ.get("VIVADO_PATH")
    if explicit and Path(explicit).exists():
        return explicit

    # 2. XILINX_VIVADO env var (set by Vivado settings64.bat / settings64.sh)
    xilinx_vivado = os.environ.get("XILINX_VIVADO")
    if xilinx_vivado:
        candidate = Path(xilinx_vivado) / "bin" / ("vivado.bat" if is_windows else "vivado")
        if candidate.exists():
            return str(candidate)

    # 3. Glob common install roots â€” pick highest version
    if is_windows:
        patterns = [
            "C:/Xilinx/Vivado/*/bin/vivado.bat",
            "D:/Xilinx/Vivado/*/bin/vivado.bat",
        ]
    else:
        patterns = [
            "/opt/Xilinx/Vivado/*/bin/vivado",
            "/tools/Xilinx/Vivado/*/bin/vivado",
            "/opt/Xilinx/Vivado/*/bin/vivado",
        ]

    candidates = []
    for pattern in patterns:
        candidates.extend(glob.glob(pattern))

    if candidates:
        # Sort by version string embedded in path (e.g. 2018.2, 2023.2)
        candidates.sort(reverse=True)
        return candidates[0]

    # 4. PATH lookup
    found = shutil.which("vivado") or shutil.which("vivado.bat")
    if found:
        return found

    raise RuntimeError(
        "Vivado not found. Set VIVADO_PATH=/path/to/vivado.bat (Windows) or "
        "XILINX_VIVADO=/path/to/Vivado/20XX.X and retry."
    )


def run_tcl(tcl_script: str, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a TCL script via 'vivado -mode tcl -source <script>' and return the result.

    Args:
        tcl_script: Path to the .tcl file to execute.
        timeout: Max seconds to wait (default 120).

    Returns:
        CompletedProcess with stdout, stderr, returncode.

    Raises:
        RuntimeError: If Vivado is not found.
        subprocess.TimeoutExpired: If the script exceeds timeout.
    """
    vivado = find_vivado()
    cmd = [vivado, "-mode", "tcl", "-source", tcl_script, "-nojournal", "-nolog"]

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=tempfile.gettempdir(),
    )


def filter_vivado_output(raw: str) -> str:
    """Strip Vivado INFO spam, keep warnings and errors."""
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Keep warnings, errors, and any FPGA_CLAUDE tagged output
        if any(stripped.startswith(tag) for tag in ("WARNING:", "ERROR:", "CRITICAL:", "FPGA_CLAUDE:")):
            lines.append(stripped)
        # Keep plain output that isn't an Xilinx log prefix
        elif not stripped.startswith("INFO:") and not stripped.startswith("//") and not stripped.startswith("#"):
            lines.append(stripped)
    return "\n".join(lines)
