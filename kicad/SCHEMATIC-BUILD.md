# KiCad schematic — generated hierarchical sheets

## Status: the wired sheets exist and pass ERC
The eight hierarchical `.kicad_sch` sheets and the root are **generated and
committed**, open in KiCad 7/8, and pass a real Electrical Rules Check:

```
kicad-cli sch erc      ->  0 violations            (KiCad 8.0.9)
kicad-cli sch export netlist ->  102 components · 58 nets · 0 unconnected pins
GND spans 55 nodes · VBIAS 10 nodes · all inter-sheet signals resolve
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
- `kicad-cli 8.0.9 sch erc`: **0 violations** (errors + warnings). Getting there
  required snapping all pins/wires to the 1.27 mm connection grid and giving the
  footswitch lines a real second endpoint (below).
- `kicad-cli` custom symbol library + footprints parse/plot; the hierarchy
  netlists with **0 unconnected pins** and no duplicate references.
- PDF/SVG render of all sheets is correct (title blocks, values, labels).
- ERC does not check reference *annotation* (that's a separate tool), so the
  descriptive non-numeric refs do not produce ERC violations; `export netlist`
  prints an "annotation" notice but exports all 102 components correctly.

## Design additions beyond the recovered notes (clearly marked)
- **Mid-rail `VBIAS`.** Single-supply TL072 stages need their inputs biased to
  ~Vcc/2; the recovered notes omit this. A `VBIAS` divider (R_vb1/R_vb2 + C_vb on
  the Power Supply sheet) feeds the reverb driver and the tremolo LFO; the
  op-amp `+in`/gain-return nets reference `VBIAS` instead of GND. Flagged in the
  sheet notes as a design addition — verify values for your rail.
- **Footswitch control taps.** `FS_REV/FS_TREM/FS_MRB` leave the DIN connector
  and land on their effect sheet through a 100 k control pulldown (R_fs_*). The
  exact pedal switching topology follows the original footswitch; these nets are
  represented as defined control lines so they aren't single-ended.

## Still to finish before a build
- **Tone stack** values are `TBD` (cross-check §4) — the sheet has the pots and a
  placeholder; fill from the original 25-5274-2 top-boost network.
- **Inter-effect routing order** (reverb→tremolo→MRB→power amp) is a documented
  assumption where the recovered notes are silent; see the note on the root sheet.
- **PCB:** a placed starter board (`cambridge_reverb.kicad_pcb`, all footprints
  assigned + a GND pour) now exists — see `PCB-NOTES.md`. Remaining work is manual
  placement into the floor-plan zones and signal routing; after annotation you can
  *Update PCB from schematic* or keep the generated board. Lay out per
  `docs/04-jlcpcb-fabrication.md`.

## Per-sheet contents
Values come from Part 2 + `netlist-notes.txt`; see those and `errata.md` for the
authoritative numbers (e.g. preamp `R_s ≈ 1–1.2 k`, `R_reg2 = 3.09 k`).
Power Supply · Preamp · Tone Stack · Reverb · Tremolo · MRB · Power Amp ·
Switching/I-O — one hierarchical sheet each, in signal-flow order.
