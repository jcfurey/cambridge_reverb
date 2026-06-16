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
