# fpga-claude

[![CI](https://github.com/Nacholazabal/fpga-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/Nacholazabal/fpga-claude/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)](#requirements)
[![PyPI](https://img.shields.io/badge/PyPI-coming%20soon-lightgrey)](https://pypi.org/)

Capture Vivado ILA waveforms from your terminal and let Claude analyze them in seconds.

`fpga-claude` is for FPGA engineers who want faster debug loops without clicking through Hardware Manager every time.

## Demo

TODO: add demo GIF here

Suggested path once recorded:

```text
docs/demo.gif
```

## How It Works

```text
+------------------------+         +------------------------+
| Claude Code            |         | fpga-claude CLI        |
| /capture or /analyze   +-------->+ Python + Click         |
+------------------------+         | - finds Vivado         |
                                   | - selects TCL script   |
                                   | - parses tagged output |
                                   +-----------+------------+
                                               |
                                               v
                                   +------------------------+
                                   | Vivado (TCL batch)     |
                                   | open_hw/connect_hw     |
                                   | arm ILA/export CSV     |
                                   +-----------+------------+
                                               |
                                               v
                                   +------------------------+
                                   | FPGA via hw_server/JTAG|
                                   | ILA buffer -> capture  |
                                   +-----------+------------+
                                               |
                                               v
                                   +------------------------+
                                   | CSV + Claude analysis  |
                                   +------------------------+
```

## Quick Start

1. Clone and install:
```bash
git clone https://github.com/Nacholazabal/fpga-claude.git
cd fpga-claude
pip install -e .
```
2. Verify Vivado path:
```bash
fpga-claude which-vivado
```
3. Start `hw_server` (Vivado Hardware Manager -> Open Target -> Auto Connect), then close the target so the CLI can connect.
4. Check board connection:
```bash
fpga-claude connect
```
5. Capture waveform:
```bash
fpga-claude capture --project /path/to/project.xpr
```

If auto-detection fails:

```bash
# Windows
set VIVADO_PATH=C:\Xilinx\Vivado\2018.2\bin\vivado.bat

# Linux
export VIVADO_PATH=/opt/Xilinx/Vivado/2018.2/bin/vivado
```

## Commands

| Command | Purpose | Typical Use |
| --- | --- | --- |
| `fpga-claude connect` | Verify `hw_server` and enumerate JTAG devices | Validate cable/board connection |
| `fpga-claude list-ilas` | List ILA cores and probe signals | Inspect available debug nets |
| `fpga-claude capture` | Arm trigger, wait, export CSV | Run captures for analysis |
| `fpga-claude which-vivado` | Show resolved Vivado executable | Confirm toolchain setup |

### `capture` options

| Flag | Default | Description |
| --- | --- | --- |
| `--server` | `localhost:3121` | `hw_server` address |
| `--project` | none | Vivado `.xpr` path (auto-discovers `.ltx`) |
| `--ltx` | none | Explicit `.ltx` probe file |
| `--ila` | `auto` | ILA core name or first detected |
| `--out` | `captures/capture.csv` | Output CSV path |
| `--trigger` | `immediate` | `immediate` or `basic` |
| `--timeout` | `30000` | Timeout in milliseconds |

## Adding To Your Vivado Project

This repo includes Claude Code skills in `skills/`:

- `capture.md` for one-shot capture + analysis
- `analyze.md` for deep CSV protocol/state analysis

Copy them into your project:

```bash
mkdir -p /path/to/vivado-project/.claude/commands
cp skills/capture.md /path/to/vivado-project/.claude/commands/capture.md
cp skills/analyze.md /path/to/vivado-project/.claude/commands/analyze.md
```

Then edit the project context section in `capture.md` so Claude knows your signal names, expected behavior, and subsystem details.

## What Needs A New Bitstream?

> [!IMPORTANT]
> Most ILA confusion comes from this distinction.
>
> | Change | New Bitstream? |
> | --- | --- |
> | Trigger condition | No |
> | Trigger position | No |
> | Capture window (within existing depth) | No |
> | Add/remove probed signal | Yes |
> | Add/remove ILA core | Yes |
> | Change ILA depth | Yes |
> | Change probe width | Yes |
>
> Rule: changing *what hardware is instrumented* needs resynthesis. Changing *runtime trigger behavior* does not.

## Requirements

- Vivado 2018.2+
- Python 3.9+
- Running `hw_server` (default `localhost:3121`)
- Programmed bitstream with ILA cores
- Claude Code CLI (for `skills/` workflows)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
