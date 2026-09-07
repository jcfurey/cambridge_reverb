# bom/

- `bom.csv` — **generated from the schematic** by `kicad/gen/gen_bom.py`
  (regenerate after any schematic change). Electrical rows are 1:1 with the KiCad
  netlist; off-board/mechanical items (sockets, heatsink, mica, standoffs, fuses)
  follow. Do not hand-edit — edit `gen_bom.py` (curated P/Ns + notes) or the
  generator (values/refs).
- `bom-grouped.csv` — consolidated by value+footprint, for ordering.
- `cross-check.md` — the original BOM-vs-docs cross-check notes.

**Re-verify live stock and pricing before ordering** (Part 8 carries the sourcing
notes and discontinued-part alternatives; see also
`../docs/component-availability-audit.md`).

## Build profiles
- `bom.csv` / `bom-grouped.csv` — the **THT** board (`kicad/cambridge_reverb.kicad_pcb`).
- `bom-smd.csv` / `bom-smd-grouped.csv` — the **mixed SMD/THT variant**
  (`kicad/smd/cambridge_reverb_smd.kicad_pcb`): same schematic, 70 small parts on
  0805/1206/1210/SMA/SOD-123/SOT-23 footprints (spec notes instead of the THT part
  numbers — pick JLCPCB "basic" parts or equivalents), everything else identical.
  `production/smd/bom-jlcpcb.csv` + the position file are the JLCPCB assembly
  inputs for the SMD side (LCSC column left for the parts picker).
  Regenerate: `python3 kicad/gen/gen_bom.py --profile smd --jlc`.
