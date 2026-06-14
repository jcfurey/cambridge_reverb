# kicad/

KiCad project files.

## Present now
- `cambridge_reverb.kicad_pro` — project with reconciled design rules and **three
  net classes** from the consistency pass: Default 0.5 mm / Power 1.5 mm /
  HighCurrent 2.5 mm (errata #11–13). `+33V5`/`SPKR±`/`PA_OUT` are pre-assigned
  to HighCurrent by net-name pattern.
- `symbols/cambridge_reverb.kicad_sym` — custom symbols: `VTL5C1`,
  `Reverb_Tank_4FB2A1C`, `Footswitch_DIN6`.
- `footprints/cambridge_reverb.pretty/` — `VTL5C1`, `Inductor_MRB_1H_Toroid`
  (2-pad, 25 mm), `Wiring_Edge_Array_35` (35 pads, 3 mm / 1.5 mm drill, labeled).
- `sym-lib-table` / `fp-lib-table` — register the project libraries (`${KIPRJMOD}`).
- `netlist-notes.txt` — recovered per-sheet connections (power amp, reverb,
  tremolo, MRB).
- `SCHEMATIC-BUILD.md` — step-by-step to build the 8 hierarchical sheets.

## Generated schematic (now present)
- `cambridge_reverb.kicad_sch` (root) + 8 hierarchical sheets — `power_supply`,
  `preamp`, `tone_stack`, `reverb`, `tremolo`, `mrb`, `power_amp`, `switching`.
  They open in KiCad 7 and netlist cleanly (94 components, 0 unconnected pins).
- `symbols/cr_primitives.kicad_sym` — self-contained primitive symbols used by
  the generated sheets.
- `gen/gen_kicad.py` — the generator (regenerate: `python3 kicad/gen/gen_kicad.py`).
- `SCHEMATIC-BUILD.md` — how the sheets are wired, what's verified, and the
  known simplifications to finish before a build.

## Still to do in the KiCad GUI
- Run ERC (KiCad 8) and annotate if you want standard refdes for layout.
- `*.kicad_pcb` — board layout (after schematic + ERC).
- `gerbers/` — exported Gerbers (git-ignored; regenerate per Part 4).
