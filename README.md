# Deepmind12-mcp

An experiment in letting an AI assistant read and edit patches on a Behringer DeepMind 12 over USB MIDI, through an MCP server.

It rests on a static reverse-engineering pass over the official editor and was checked against a real unit running firmware 1.1.2-619. It is an independent project, not affiliated with Behringer, and it ships none of their software. Use it at your own risk.

## Status: work in progress

The plumbing works. The sound does not, yet.

**What works** (tested end to end on hardware)
- Connecting to the synth and reading the current patch as readable parameters.
- Previewing changes without sending anything.
- Writing to the edit buffer, with an automatic backup, a read-back comparison and a restore.

**What does not work**
Generated patches have never come out clean: harsh, overly electronic or oddly honking. The likely causes:
- The assistant cannot hear anything. It picks values from synthesis theory and has no way to judge the result.
- The real scale of several parameters is unknown (resonance, detune, modulation depth), so a value that looks modest can sound extreme.
- A few parameters are still unnamed, and the label order of some lists (LFO shapes, arpeggiator modes, modulation sources and destinations) is only confirmed for a handful of indexes.
- The factory "Default Program" has VCF Invert switched on, which gives surprising timbres if you do not notice it.

Treat this as a foundation (protocol notes, patch layout, guarded tooling), not as a working preset generator.

## Deliberately not captured

The editor contains other SysEx commands. Their identifiers are listed in `notes/sysex.md`, but no traffic was captured or analysed for them, and the server refuses to send them:

- **Firmware update (DFU):** a bad or interrupted transfer can leave the unit unusable, there is no safe way to test it, and it has nothing to do with presets.
- **Hardware calibration:** these commands change per-unit tuning data.
- **Network and Wi-Fi settings:** this data is personal (credentials, addresses) and should be neither captured nor published, and a wrong value can cut the unit off the network.
- **Globals** (MIDI channels, device ID, clock, keyboard settings): these affect the whole instrument rather than a preset. Sweeping them during the analysis once left the keyboard silent through a key-range setting, so they are excluded.

## Precautions
- Close any other program that holds the synth's MIDI port, including the official editor.
- Changing program from the front panel reloads the edit buffer and discards unsaved edits.
- The server only ever writes to the volatile edit buffer. To keep a patch, press WRITE on the synth.

## Layout
- `dm12_mcp/`: the MCP server (Python, `mcp` SDK 2.x, Windows only because it uses WinMM). See its own README.
- `notes/`: SysEx format, the 242-byte program layout, named parameters, limits, safety notes and hardware checks (written in French).
- `params.json`: extracted tables (effects, bounds, NRPN-to-byte mapping).
- `scripts/`: read-only MIDI helpers, an edit-buffer-only writer, and the Ghidra and extraction scripts used for the analysis.

## Quick start
```
pip install mcp
python scripts/midi_list.py
python scripts/mcp_smoke_test.py
```
The first script should list the synth as both an input and an output. The second reads the patch, previews a change, writes one neutral change and restores the original. To register the server with an MCP client, start from `.mcp.json.example`.
