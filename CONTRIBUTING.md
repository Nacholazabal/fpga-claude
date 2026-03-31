# Contributing to fpga-claude

Thanks for contributing. This guide covers development setup, testing, and extension points for CLI and TCL scripts.

## Development Setup

```bash
git clone https://github.com/Nacholazabal/fpga-claude.git
cd fpga-claude
pip install -e ".[dev]"
fpga-claude --version
```

## Run Tests and Lint

```bash
pytest -v
ruff check .
```

## Test TCL Scripts Directly In Vivado

For FPGA work, this is the fastest feedback loop.

```tcl
# Launch Vivado in Tcl mode
vivado -mode tcl

# Basic hardware connect script
source tcl/connect_hw.tcl

# List ILAs
set hw_server_url "localhost:3121"
set ltx_file "none"
source tcl/list_ilas.tcl

# Arm + capture
set hw_server_url "localhost:3121"
set ltx_file "path/to/your/debug_nets.ltx"
set ila_name "auto"
set trigger_mode "immediate"
set timeout_ms 30000
set out_csv "test_capture.csv"
source tcl/arm_and_capture.tcl
```

## Add A New CLI Command

1. Add a new command in `fpga_claude/cli.py` using Click.
2. Reuse helpers in `fpga_claude/ila.py` whenever possible.
3. Keep output protocol compatible with skills and automation:
- `FPGA_CLAUDE_JSON:{...}` for structured results
- `FPGA_CLAUDE_CSV:<path>` for exported captures
- human-readable status lines for terminal users
- errors on stderr
4. Add/adjust tests and run `pytest` + `ruff check .`.

## Add A New TCL Script

1. Add the script under `tcl/`.
2. Emit tagged lines that Python can parse:

```tcl
puts "FPGA_CLAUDE:INFO:Connecting..."
puts "FPGA_CLAUDE:JSON:{\"ok\": true}"
puts "FPGA_CLAUDE:ERROR:Something failed"
puts "FPGA_CLAUDE:RESULT:/path/to/file.csv"
```

3. Wire the script into `fpga_claude/ila.py`.
4. Validate in Vivado Tcl first, then through the CLI.

## Pull Requests

- Keep PRs focused (one feature/fix per PR).
- Include board + Vivado version when hardware behavior is involved.
- Update docs/changelog when user-visible behavior changes.
