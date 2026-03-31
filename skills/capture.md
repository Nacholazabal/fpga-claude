---
description: Capture an ILA waveform from the FPGA and analyze the results
---

Capture an ILA waveform from the FPGA and analyze the results.

## Steps

1. Run the capture command:
   ```bash
   python -m fpga_claude capture --project $ARGUMENTS --trigger immediate
   ```
   If no argument is provided, use `--project .` to search the current directory for a `.xpr` file.
   If the user specifies a trigger condition or ILA name, add `--ila <name>` or `--trigger basic`.
   If `python -m fpga_claude` fails because the module is missing, fall back to:
   ```bash
   fpga-claude capture --project $ARGUMENTS --trigger immediate
   ```

2. Check for errors. Common issues and how to guide the user:
   - "hw_server not reachable" → board not connected or hw_server not started; tell user to connect board and open Hardware Manager in Vivado (or run `hw_server.exe` from Vivado bin dir)
   - "No .ltx file found" → implementation hasn't been run yet; tell user to run Generate Bitstream first
   - "No ILA cores found" → bitstream has no debug probes; ILA needs to be added to the design
   - "Timeout waiting for trigger" → trigger condition never occurred; suggest `--trigger immediate` or check that firmware is running

3. Read the captured CSV file (the path is printed as `FPGA_CLAUDE_CSV:<path>`):
   Use the Read tool to load the CSV contents.

4. Analyze the waveform:
   - Identify all signal names and their bit widths
   - Find the trigger sample and describe what was happening at that moment
   - Look for stuck signals (constant value throughout): flag these — a signal that never changes may indicate a bug
   - Look for AXI handshake patterns: check `*_valid` / `*_ready` pairs for backpressure stalls (valid HIGH, ready LOW for many consecutive cycles)
   - Look for unexpected values: address misalignment, wrong data width, unexpected state machine states
   - Count transitions and note any periodic patterns or one-time glitches
   - Report the total capture depth and how many samples were captured before/after trigger

5. Provide a structured analysis:
   **Signal overview**: list each signal, its range of values, and whether it looks normal
   **Key observations**: what stands out in the data
   **Likely issue** (if any): your best diagnosis based on the signals
   **Suggested next step**: e.g. "add a trigger condition on `axi_bvalid` to catch the response", or "check the firmware AXI write sequence"

## Context about this project

This is a Xilinx Vivado project targeting the Arty Z7-20 (Zynq xc7z020).
The design is an HDMI overlay pipeline with:
- AXI VDMA (dual-channel: S2MM for capture, MM2S for display)
- DVI2RGB / RGB2DVI HDMI transceivers
- Custom AXI4-Lite overlay control IP (`axis_video_overlay_rect`)
- Subtitle BRAM IP (`subtitle_mask_mem`)
- Firmware runs on ARM Cortex-A9 PS (bare-metal, no OS)

Common signals to watch:
- `m_axi_s2mm_*` / `m_axi_mm2s_*` — VDMA AXI master buses
- `s_axis_s2mm_*` — VDMA write stream from HDMI input
- `m_axis_mm2s_*` — VDMA read stream to display output
- `locked` — pixel clock lock from DVI2RGB
- `overflow` / `underflow` — VDMA error flags
