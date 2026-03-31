"""fpga-claude CLI — entry point for all subcommands."""

import json
import sys

import click

from . import __version__
from .hw_server import check_hw_server
from . import ila as ila_mod
from .probe_discovery import find_ltx
from .vivado import find_vivado
from .waveform import parse_csv, summarize


@click.group()
@click.version_option(__version__)
def cli():
    """fpga-claude: Claude Code integration for Vivado FPGA debugging.

    Drive Vivado's TCL API from the command line — arm ILA triggers,
    capture waveforms, export CSV, and let Claude analyze the results.
    """


# ---------------------------------------------------------------------------
# connect
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--server", default="localhost:3121", show_default=True,
              help="hw_server URL (host:port)")
def connect(server):
    """Verify hw_server is running and show connected JTAG devices."""
    click.echo(f"Checking hw_server at {server}...")
    try:
        check_hw_server(server)
    except RuntimeError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)

    click.echo("hw_server reachable. Querying JTAG chain via Vivado...")
    try:
        info = ila_mod.connect(server)
    except RuntimeError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)

    devices = info.get("devices", [])
    if not devices:
        click.echo("No JTAG devices found.")
        sys.exit(1)

    click.echo(f"\nFound {len(devices)} device(s) on {server}:")
    for d in devices:
        click.echo(f"  {d['name']}  part={d['part']}  IR_length={d['ir_length']}")

    # Machine-readable output on stdout for skill consumption
    click.echo("\nFPGA_CLAUDE_JSON:" + json.dumps(info))


# ---------------------------------------------------------------------------
# list-ilas
# ---------------------------------------------------------------------------

@cli.command("list-ilas")
@click.option("--server", default="localhost:3121", show_default=True)
@click.option("--project", default=None,
              help="Path to .xpr file or project directory (used to auto-find .ltx)")
@click.option("--ltx", default=None,
              help="Explicit path to .ltx probe file (overrides --project auto-discovery)")
def list_ilas(server, project, ltx):
    """List ILA cores and their probe signals on the connected device."""
    try:
        check_hw_server(server)
    except RuntimeError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)

    ltx_path = "none"
    if ltx:
        ltx_path = ltx
    elif project:
        try:
            ltx_path = find_ltx(project)
            click.echo(f"Found probe file: {ltx_path}")
        except FileNotFoundError as e:
            click.echo(f"WARNING: {e}", err=True)
            click.echo("Continuing without probe file — signal names may not be available.", err=True)

    try:
        info = ila_mod.list_ilas(server, ltx_path)
    except RuntimeError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)

    ilas = info.get("ilas", [])
    if not ilas:
        click.echo(f"No ILA cores found on {info.get('device', 'unknown device')}.")
        click.echo("Make sure your bitstream includes ILA debug cores.")
        sys.exit(0)

    click.echo(f"\nDevice: {info.get('device')}")
    click.echo(f"ILA cores: {len(ilas)}")
    for ila in ilas:
        click.echo(f"\n  [{ila['name']}]  depth={ila['depth']}")
        for probe in ila.get("probes", []):
            click.echo(f"    {probe['name']}  width={probe['width']}")

    click.echo("\nFPGA_CLAUDE_JSON:" + json.dumps(info))


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--server", default="localhost:3121", show_default=True)
@click.option("--project", default=None,
              help="Path to .xpr or project directory for .ltx auto-discovery")
@click.option("--ltx", default=None,
              help="Explicit path to .ltx probe file")
@click.option("--ila", "ila_name", default="auto", show_default=True,
              help="ILA core name (e.g. hw_ila_1) or 'auto' for first found")
@click.option("--out", "out_csv", default="captures/capture.csv", show_default=True,
              help="Output CSV file path")
@click.option("--trigger", "trigger_mode",
              type=click.Choice(["immediate", "basic"], case_sensitive=False),
              default="immediate", show_default=True,
              help="immediate=capture now, basic=use trigger conditions set on ILA")
@click.option("--timeout", "timeout_ms", default=30000, show_default=True,
              help="Milliseconds to wait for trigger before giving up")
def capture(server, project, ltx, ila_name, out_csv, trigger_mode, timeout_ms):
    """Arm an ILA, wait for capture, and export waveform to CSV.

    After capturing, prints the CSV path and a signal summary for Claude to read.

    Examples:\n
      fpga-claude capture --project ./MyProject.xpr\n
      fpga-claude capture --ltx ./impl_1/debug.ltx --ila hw_ila_1 --trigger basic --timeout 60000\n
      fpga-claude capture --out /tmp/wave.csv
    """
    try:
        check_hw_server(server)
    except RuntimeError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)

    # Resolve .ltx
    ltx_path = "none"
    if ltx:
        ltx_path = ltx
    elif project:
        try:
            ltx_path = find_ltx(project)
            click.echo(f"Probe file: {ltx_path}")
        except FileNotFoundError as e:
            click.echo(f"WARNING: {e}", err=True)

    click.echo(f"Capturing: ILA={ila_name}, trigger={trigger_mode}, timeout={timeout_ms}ms")

    try:
        csv_path = ila_mod.capture(
            hw_server=server,
            ltx_file=ltx_path,
            ila_name=ila_name,
            out_csv=out_csv,
            trigger_mode=trigger_mode,
            timeout_ms=timeout_ms,
        )
    except RuntimeError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)

    # Parse and summarize for Claude
    try:
        waveform = parse_csv(csv_path)
        summary = summarize(waveform)
    except Exception as e:
        click.echo(f"WARNING: Could not parse CSV for summary: {e}", err=True)
        summary = "(parse failed)"

    click.echo(f"\nCapture complete: {csv_path}")
    click.echo("\n--- Waveform Summary ---")
    click.echo(summary)
    click.echo("FPGA_CLAUDE_CSV:" + csv_path)


# ---------------------------------------------------------------------------
# which-vivado (diagnostic helper)
# ---------------------------------------------------------------------------

@cli.command("which-vivado")
def which_vivado():
    """Show which Vivado executable will be used."""
    try:
        path = find_vivado()
        click.echo(f"Vivado: {path}")
    except RuntimeError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
