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

## To be built in the KiCad GUI
- `*.kicad_sch` — 8 hierarchical sheets (Power Supply → Preamp → Tone Stack →
  Reverb → Tremolo → MRB → Power Amp → Switching). Follow `SCHEMATIC-BUILD.md`;
  values come from Part 2 + `netlist-notes.txt`. The wired sheets are built
  interactively rather than committed pre-wired (see `SCHEMATIC-BUILD.md` for why).
- `*.kicad_pcb` — board layout (after schematic + ERC).
- `gerbers/` — exported Gerbers (git-ignored; regenerate per Part 4).
