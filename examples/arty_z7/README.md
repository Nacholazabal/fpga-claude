# Arty Z7-20 Example

This example shows how to set up fpga-claude with the Arty Z7-20 (Zynq xc7z020).

## Setup

1. Add ILA cores to your block design (see main README)
2. Program the FPGA with your bitstream
3. Start hw_server (or open Vivado Hardware Manager)
4. Copy skill files into your project:
   ```bash
   mkdir -p .claude/commands
   cp ../../skills/capture.md .claude/commands/capture.md
   cp ../../skills/analyze.md  .claude/commands/analyze.md
   ```
5. Open Claude Code in your project directory

## Typical debug session

```bash
# 1. Check board is connected
fpga-claude connect

# 2. See what ILA cores are in the bitstream
fpga-claude list-ilas --project ./MyProject.xpr

# 3. Capture (firmware should be running on the ARM)
fpga-claude capture --project ./MyProject.xpr

# 4. Or use the Claude Code skill for capture + analysis in one step
#    (in Claude Code terminal):  /capture
```

## Notes for Zynq

- The PS (ARM) and PL (FPGA fabric) are separate — ILA probes PL signals
- hw_server connects via the same USB-JTAG as programming
- Firmware can be running while ILA captures — they don't interfere
- If using Vivado 2018.2 SDK, start hw_server before launching SDK
