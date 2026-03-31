"""Parse Vivado ILA CSV exports into structured data for Claude to analyze."""

import csv
from pathlib import Path


def parse_csv(csv_path: str) -> dict:
    """Parse a Vivado ILA CSV export.

    Vivado ILA CSVs have this structure:
      - Row 0: signal names  (e.g. "Sample in Buffer", "TRIGGER", "probe0[7:0]", ...)
      - Row 1: radix info    (e.g. "", "", "Hex", "Binary", ...)
      - Row 2+: data rows    (sample index, trigger marker, hex/bin values, ...)

    Returns a dict:
      {
        "sample_count": int,
        "trigger_sample": int | None,
        "signals": [
          {
            "name": str,
            "radix": str,      # "Hex", "Binary", "Unsigned", etc.
            "values": [str],   # one per sample
          }
        ]
      }
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) < 3:
        raise ValueError(f"CSV too short ({len(rows)} rows) — may be empty or corrupt: {csv_path}")

    header_row = rows[0]
    radix_row  = rows[1]
    data_rows  = rows[2:]

    # Vivado always puts "Sample in Buffer" in col 0 and "TRIGGER" in col 1
    # Signal data starts at col 2
    signal_names = header_row[2:]
    signal_radix = radix_row[2:] if len(radix_row) > 2 else [""] * len(signal_names)

    signals = [
        {"name": name.strip(), "radix": (signal_radix[i].strip() if i < len(signal_radix) else ""), "values": []}
        for i, name in enumerate(signal_names)
        if name.strip()
    ]

    trigger_sample = None
    sample_count = 0

    for row in data_rows:
        if len(row) < 2:
            continue
        sample_count += 1

        # Column 1 is the TRIGGER marker — "1" means this is the trigger sample
        trigger_marker = row[1].strip() if len(row) > 1 else ""
        if trigger_marker == "1" and trigger_sample is None:
            trigger_sample = sample_count - 1  # 0-indexed

        # Signal values start at col 2
        for i, sig in enumerate(signals):
            col_idx = i + 2
            val = row[col_idx].strip() if col_idx < len(row) else ""
            sig["values"].append(val)

    return {
        "sample_count": sample_count,
        "trigger_sample": trigger_sample,
        "signals": signals,
    }


def summarize(waveform: dict) -> str:
    """Generate a compact text summary suitable for pasting into a Claude prompt."""
    lines = []
    sc = waveform["sample_count"]
    ts = waveform["trigger_sample"]
    lines.append(f"Samples: {sc}")
    lines.append(f"Trigger at sample: {ts if ts is not None else 'N/A'}")
    lines.append(f"Signals ({len(waveform['signals'])}):")

    for sig in waveform["signals"]:
        vals = sig["values"]
        unique = list(dict.fromkeys(vals))  # deduplicated, order preserved
        if len(unique) == 1:
            lines.append(f"  {sig['name']}: CONSTANT {unique[0]}")
        elif len(unique) <= 5:
            lines.append(f"  {sig['name']}: {unique} ({len(vals)} samples)")
        else:
            lines.append(f"  {sig['name']}: {unique[:3]}... ({len(unique)} unique values, {len(vals)} samples)")

    return "\n".join(lines)
