# KiCad schematic — generated hierarchical sheets

## Status: the wired sheets now exist
The eight hierarchical `.kicad_sch` sheets and the root are **generated and
committed**. They open in KiCad 7, and a full netlist exports cleanly:

```
94 components · 56 nets · 0 unconnected pins   (kicad-cli sch export netlist)
GND spans 55 nodes · +17V 9 nodes · all inter-sheet signals resolve
```

Files: `cambridge_reverb.kicad_sch` (root) + `power_supply / preamp /
tone_stack / reverb / tremolo / mrb / power_amp / switching .kicad_sch`.
Generator: `gen/gen_kicad.py` (regenerate with `python3 kicad/gen/gen_kicad.py`).

## How they're built
- **Self-contained symbols.** `symbols/cr_primitives.kicad_sym` defines the
  primitives (R, C, CP, L, D, LED, JFET, dual op-amp, LM1875, LM317, bridge,
  pot, jack, speaker, transformer, fuse, PWR_FLAG) with known pin geometry, so
  the project has no dependency on the system libraries. The curated parts
  (`VTL5C1`, `Reverb_Tank_4FB2A1C`, `Footswitch_DIN6`) come from
  `symbols/cambridge_reverb.kicad_sym`.
- **Label-based connectivity.** Each pin gets a short wire stub to a net label —
  `global_label` for rails and cross-sheet signals (`+33V5`, `+17V`, `+27V`,
  `GND`, `SPK_P/N`, `GUITAR_IN`, `PREAMP_OUT`, `TONE_OUT`, `DRY`, `WET`,
  `BLEND`, `TREM_OUT`, `MRB_OUT`, `PA_IN`, `FX_RET`, `FS_*`), `label` for
  intra-sheet nets. This yields a correct netlist without fragile point-to-point
  routing.
- **Descriptive references.** Designators match the BOM/docs/SPICE (`R_fb`,
  `C_out`, `IC_PA`, `Q_rec`, …) for traceability. KiCad's auto-annotator will
  flag these as "not numerically annotated" (they have no trailing number) — that
  is expected and **non-blocking**; the netlist is correct and pin-complete. If
  you want standard refdes for board layout, run Tools → Annotate (it will
  renumber; keep a copy if you want to preserve the doc names).

## Verified
- `kicad-cli 7.0.11`: custom symbol library + footprints parse/plot; the
  hierarchy netlists with **0 unconnected pins** and no duplicate references.
- PDF/SVG render of all sheets is correct (title blocks, values, labels).
- KiCad 7's CLI has no `erc` subcommand (added in KiCad 8); the netlist export is
  used as the connectivity check here. Open in the KiCad 8 GUI and run ERC for a
  full rules pass.

## Known simplifications to finish before a build (honest list)
- **Op-amp single-supply biasing is minimal.** IC1/IC2 are shown with `V+ = +17V`,
  `V- = GND`; the recovered notes don't include the mid-rail input-bias network a
  real single-supply TL072 stage needs. Add a mid-rail divider + input bias before
  relying on the reverb/tremolo stages.
- **Tone stack** values are `TBD` (cross-check §4) — the sheet has the pots and a
  placeholder; fill from the original 25-5274-2 top-boost network.
- **Inter-effect routing order** (reverb→tremolo→MRB→power amp) is a documented
  assumption where the recovered notes are silent; see the note on the root sheet.
- **No PCB yet.** After ERC + annotation, assign footprints (the custom ones in
  `footprints/cambridge_reverb.pretty/` plus standard ones) and lay out the board
  per `docs/04-jlcpcb-fabrication.md`.

## Per-sheet contents
Values come from Part 2 + `netlist-notes.txt`; see those and `errata.md` for the
authoritative numbers (e.g. preamp `R_s ≈ 1–1.2 k`, `R_reg2 = 3.09 k`).
Power Supply · Preamp · Tone Stack · Reverb · Tremolo · MRB · Power Amp ·
Switching/I-O — one hierarchical sheet each, in signal-flow order.
