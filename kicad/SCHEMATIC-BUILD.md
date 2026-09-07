# KiCad schematic — generated hierarchical sheets

## Status: the wired sheets exist and pass ERC
The eight hierarchical `.kicad_sch` sheets and the root are **generated and
committed**, open in KiCad 7/8, and pass a real Electrical Rules Check:

```
kicad-cli sch erc      ->  0 violations            (KiCad 8.0.9)
kicad-cli sch export netlist ->  174 components (146 + 28 test points) · 83 nets · 0 unconnected pins
GND spans 65 nodes · split mid-rails VBIAS_R / VBIAS_T / VBIAS_3 · all inter-sheet signals resolve
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
  `global_label` for rails and cross-sheet signals (`+33V5`, `+17V`, `VREG_IN`,
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
  prints an "annotation" notice but exports all 174 components correctly.

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

## Effects chain — redesigned 2026-06-16 (roast R3/R6 resolved)
- **Active wet/dry summer** on the spare **IC1-B** half (inverting summer about
  `VBIAS_R`: dry always on, wet via `POT_REV`, unity each). Output `BLEND` is
  low-Z. Replaces the old broken passive `R_dry_tap`/`R_blend*` mixer.
- **Output buffer** on the spare **IC2-B** half drives `PA_IN` from the post-MRB
  node (replaces the unbuffered `R_painput` 1 M).
- **Split bias:** `VBIAS_R` (reverb) and `VBIAS_T` (tremolo) are independent
  100 k/100 k + 47 µF dividers — no shared reference, so no LFO→reverb bleed.
- **Verified rail-aware** (`spice/tran_reverb_mixer.cir`): mid-rail bias 8.50 V,
  unity sum, ±7 V headroom before clipping. ERC 0.

## Still to finish before a build
- **Tone stack** is *designed* (errata #20): the panel's Bass + Treble pots on a
  passive James network with a TL074 buffer / make-up (`IC3`), a switchable
  gyrator MID CUT (`SW_MID`, line-reverse hole) and the 470 pF chime cap as a
  bright cap — verified in `spice/ac_tonestack.cir` + `sweep_tonestack.cir`. The
  original 25-5274-2 values were never recovered (cross-check §4); if they turn
  up they drop into the same ladder.
- The tremolo's passive LDR shunt + MRB sit *between* the two buffered nodes
  (BLEND→ … →PA_IN); levels there are reasonable but bench-tune the tremolo depth
  and MRB blend.
- **Inter-effect routing order** (reverb→tremolo→MRB→power amp) is a documented
  assumption where the recovered notes are silent; see the note on the root sheet.
- **PCB:** `cambridge_reverb.kicad_pcb` is generated (floor-plan placement,
  `gen/gen_pcb.py`) and autorouted (`gen/route_board.py`) — status, DRC and the
  remaining hand-review in `PCB-NOTES.md`. After annotation you can *Update PCB
  from schematic* or keep the generated board. Fab per `docs/04-jlcpcb-fabrication.md`.

## Per-sheet contents
Values come from Part 2 + `netlist-notes.txt`; see those and `errata.md` for the
authoritative numbers (e.g. preamp `R_s ≈ 1–1.2 k`, `R_reg2 = 3.09 k`).
Power Supply · Preamp · Tone Stack · Reverb · Tremolo · MRB · Power Amp ·
Switching/I-O — one hierarchical sheet each, in signal-flow order.
