---
description: Analyze a previously captured ILA waveform CSV file
---

Analyze a previously captured ILA waveform CSV file.

## Steps

1. Determine the CSV file to analyze:
   - If a path is given in $ARGUMENTS, use that
   - Otherwise, look for the most recent `*.csv` in the current directory and subdirectories
   - If none found, tell the user to run `/capture` first

2. Read the CSV file using the Read tool.

3. Parse the structure:
   - Row 0: signal names (col 0 = "Sample in Buffer", col 1 = "TRIGGER", col 2+ = signal names)
   - Row 1: radix/format for each signal (Hex, Binary, Unsigned, etc.)
   - Rows 2+: one row per sample

4. Deep analysis — go beyond the basic summary:

   **AXI Protocol Analysis** (if AXI signals present):
   - Find all VALID/READY pairs and compute stall cycles (VALID=1, READY=0)
   - Check for protocol violations: VALID going low without READY (not allowed in AXI4)
   - Measure burst lengths and compare to expected (e.g. VDMA burst size)
   - Check AWADDR / ARADDR alignment to burst size
   - Verify BRESP / RRESP are OKAY (2'b00)

   **Video/Streaming Analysis** (if video signals present):
   - Look for `tvalid`/`tready`/`tlast` — count frames and lines
   - Check for dropped frames (missing `tlast`)
   - Verify `tuser` (start-of-frame) occurs at expected intervals

   **State Machine Analysis** (if state signals present):
   - List all observed states
   - Identify any states that are never visited (unreachable) or stuck

   **Clock/Reset Analysis**:
   - If reset signals present, note how long reset is asserted
   - Look for glitches on signals that should only change on clock edges

   **Timing Analysis**:
   - Measure time from trigger to any notable event
   - If clock signal is captured, estimate frequency from transitions

5. Provide actionable conclusions:
   - State the most likely root cause of any anomaly
   - Suggest a specific follow-up capture with a targeted trigger condition
   - If the data looks normal, say so clearly — "No anomalies found in this capture"

6. If the user asks to compare two captures, read both CSVs and diff the signal behavior.

## Tips for reading Vivado ILA CSVs

- Values in Hex columns are shown without 0x prefix
- Binary columns show MSB first
- The trigger sample row has "1" in the TRIGGER column; all others have "0"
- Sample numbers in col 0 may not start at 0 (depends on trigger position setting)
- Vivado writes one CSV per ILA core; if multiple ILAs were captured, there will be multiple files
