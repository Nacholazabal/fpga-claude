"""ILA capture orchestration: build TCL args, run Vivado, parse output."""

import json
import os
import tempfile
from pathlib import Path

from .vivado import run_tcl, filter_vivado_output

# Path to the tcl/ directory (sibling of this package)
TCL_DIR = Path(__file__).parent.parent / "tcl"


def _parse_fpga_claude_output(raw: str) -> dict:
    """Extract FPGA_CLAUDE tagged lines from Vivado stdout."""
    result = {"info": [], "warnings": [], "errors": [], "json": None, "result_path": None}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("FPGA_CLAUDE:INFO:"):
            result["info"].append(line[len("FPGA_CLAUDE:INFO:"):])
        elif line.startswith("FPGA_CLAUDE:ERROR:"):
            result["errors"].append(line[len("FPGA_CLAUDE:ERROR:"):])
        elif line.startswith("FPGA_CLAUDE:JSON:"):
            try:
                result["json"] = json.loads(line[len("FPGA_CLAUDE:JSON:"):])
            except json.JSONDecodeError:
                result["errors"].append(f"Failed to parse JSON: {line}")
        elif line.startswith("FPGA_CLAUDE:RESULT:"):
            result["result_path"] = line[len("FPGA_CLAUDE:RESULT:"):]
        elif line.startswith("WARNING:"):
            result["warnings"].append(line)
    return result


def _tcl_path(path: str) -> str:
    """Normalize a path for TCL: forward slashes only."""
    return path.replace("\\", "/")


def connect(hw_server: str = "localhost:3121") -> dict:
    """Connect to hw_server and return device info as dict."""
    script = _tcl_path(str(TCL_DIR / "connect_hw.tcl"))
    # Write a temp TCL that sources the script with args
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tcl", delete=False) as f:
        f.write(f'set argv {{"{hw_server}"}}\n')
        f.write(f'source {{{script}}}\n')
        tmp = f.name

    try:
        result = run_tcl(tmp, timeout=30)
    finally:
        os.unlink(tmp)

    parsed = _parse_fpga_claude_output(result.stdout + result.stderr)
    if parsed["errors"]:
        raise RuntimeError("\n".join(parsed["errors"]))
    if parsed["json"] is None:
        raise RuntimeError(
            "No structured output from Vivado.\n"
            + filter_vivado_output(result.stdout + result.stderr)
        )
    return parsed["json"]


def list_ilas(hw_server: str = "localhost:3121", ltx_file: str = "none") -> dict:
    """List ILA cores and their probes from the connected device."""
    script = _tcl_path(str(TCL_DIR / "list_ilas.tcl"))
    ltx_tcl = _tcl_path(ltx_file) if ltx_file != "none" else "none"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tcl", delete=False) as f:
        f.write(f'set argv {{"{hw_server}" "{ltx_tcl}"}}\n')
        f.write(f'source {{{script}}}\n')
        tmp = f.name

    try:
        result = run_tcl(tmp, timeout=60)
    finally:
        os.unlink(tmp)

    parsed = _parse_fpga_claude_output(result.stdout + result.stderr)
    if parsed["errors"]:
        raise RuntimeError("\n".join(parsed["errors"]))
    if parsed["json"] is None:
        raise RuntimeError(
            "No ILA data returned.\n"
            + filter_vivado_output(result.stdout + result.stderr)
        )
    return parsed["json"]


def capture(
    hw_server: str = "localhost:3121",
    ltx_file: str = "none",
    ila_name: str = "auto",
    out_csv: str = "capture.csv",
    trigger_mode: str = "immediate",
    timeout_ms: int = 30000,
) -> str:
    """Arm ILA, wait for capture, export CSV. Returns path to the CSV file."""
    script = _tcl_path(str(TCL_DIR / "arm_and_capture.tcl"))
    ltx_tcl = _tcl_path(ltx_file) if ltx_file != "none" else "none"
    csv_tcl = _tcl_path(str(Path(out_csv).resolve()))

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tcl", delete=False) as f:
        f.write(f'set argv {{"{hw_server}" "{ltx_tcl}" "{ila_name}" "{csv_tcl}" "{trigger_mode}" "{timeout_ms}"}}\n')
        f.write(f'source {{{script}}}\n')
        tmp = f.name

    try:
        result = run_tcl(tmp, timeout=timeout_ms // 1000 + 60)
    finally:
        os.unlink(tmp)

    parsed = _parse_fpga_claude_output(result.stdout + result.stderr)

    if parsed["errors"]:
        raise RuntimeError("\n".join(parsed["errors"]))

    if parsed["result_path"] is None:
        raise RuntimeError(
            "Capture did not produce a CSV file.\n"
            + filter_vivado_output(result.stdout + result.stderr)
        )

    return parsed["result_path"]
