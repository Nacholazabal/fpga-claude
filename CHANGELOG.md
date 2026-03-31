# Changelog

All notable changes to this project are documented here.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [0.1.0] - 2026-03-30

### Added

- CLI commands:
- `fpga-claude connect` for `hw_server` and JTAG device checks.
- `fpga-claude list-ilas` for ILA/probe enumeration.
- `fpga-claude capture` for arm/wait/export CSV workflow.
- `fpga-claude which-vivado` for Vivado path inspection.
- Vivado path auto-discovery using env vars and common install locations.
- `.ltx` auto-discovery from Vivado project outputs.
- CSV parsing and signal summary utilities for Claude analysis.
- TCL scripts for connect/list/capture flows in batch Vivado mode.
- Claude Code skills (`skills/capture.md`, `skills/analyze.md`).
- GitHub project polish:
- CI workflow (Python 3.9/3.11/3.12, ruff, pytest).
- Issue templates and PR template.
- Contribution guide and improved README.
