# Changelog

All notable design work on this project. Parts correspond to the structured
deliverables produced during the design phase.

## Design deliverables

- **Part 1 — Modernization Guide:** all circuit sections, safety.
- **Part 2 — Full BOM:** Mouser/Digikey part numbers, ASCII schematics.
- **Part 3 — Wiring harness:** color codes, star grounding, footswitch DIN pinout, troubleshooting tables.
- **Part 4 — JLCPCB fabrication guide:** KiCad design rules, Gerber export, silkscreen layout.
- **Part 5 — Thermal & placement:** thermal calcs, component placement floor plan, assembly drawings (LM1875 requires ≤2.5 °C/W heatsink; original bracket suitable).
- **Part 6B — SPICE simulations:** guitar-optimized LTspice sims for all six circuit blocks (supersedes original Part 6).
- **Part 7 — Chassis measurement:** measurement procedure and PCB sizing strategy.
- **Part 8 — Verified BOM:** in-stock status, alternatives for discontinued parts.
- **Part 9 — Transformers & magnetics:** T1 testing, AnTek AS-0524 toroidal T1 option, reverb pan impedance matching, MRB inductor substitution (Fasel wah inductors).
- **Part 10 — KiCad project files:** .kicad_pro, .kicad_sch with 8 hierarchical sheets, custom symbol library (VTL5C1/reverb tank/6-pin DIN), custom footprint library (VTL5C1/1H toroid/35-pad wiring edge array).

## Errata
Identified and resolved 17 cross-document inconsistencies. Three high-priority
issues flagged: discontinued JFET part numbers, output coupling cap, and related items.

## Unreleased
- Initial git repository structure created.
- Reconstructed Parts 1-10 + errata into docs/ from recovered conversation
  content (see docs/PROVENANCE.md for method and verification notes).
- Added bom/bom.csv, spice/power_amp_lm1875.cir, kicad/netlist-notes.txt.

### Consistency pass & build-out (2026-06-14)
- **Errata Issues 9–17 resolved** (docs/errata.md): board-dimension decision
  point, LM317 17 V set-resistor correction (R_reg2 3.0k→3.09k for 17.0–17.5 V),
  missing HighCurrent net class, via-drill/trace-width reconciliation, reverb-pan
  and JFET-bias consistency confirmations, filter-cap and bypass wording.
- **BOM cross-check** (bom/cross-check.md): added the missing preamp, reverb,
  tremolo, MRB, panel-pot, FX-loop, and mechanical/safety rows to bom/bom.csv
  (values from Part 2 + netlist-notes); flagged SPICE simplifications and the
  unrecovered tone-stack values.
- **KiCad project re-authored** (kicad/): cambridge_reverb.kicad_pro (3 net
  classes), custom symbol library (VTL5C1, reverb tank, DIN-6), custom
  footprints (VTL5C1, 1H toroid, 35-pad wiring edge array), library tables, and
  SCHEMATIC-BUILD.md.
- **Reference content** added to empty dirs: datasheets/SOURCES.md,
  photos/CAPTURE-CHECKLIST.md, production/CHECKLIST.md.

### SPICE verification + validated EDA files (2026-06-14)
- **KiCad files validated** with kicad-cli 7.0.11: custom symbol library and
  footprints parse and plot cleanly; .kicad_pro is valid JSON.
- **ngspice block sims added** (spice/): ac_power_amp_lm1875.cir (with C_fb_hf +
  10" speaker model), ac_reverb_driver.cir, ac_mrb.cir, dc_preamp_jfet.cir,
  tran_tremolo_lfo.cir, shared models/ (opamp1p.sub, jfet_2n5457.lib), run_all.sh.
  All run under ngspice-42 and reproduce the documented gains/frequencies.
- **Two findings from running the sims** (folded into errata #15 + cross-check):
  power-amp LF −3 dB is ~17 Hz (input pole, not just C_gain); preamp Rs 2.2 kΩ
  biases the drain cold at ~12 V — Rs ≈ 1–1.2 kΩ hits the 8–9 V target.

### Generated hierarchical schematic (2026-06-14)
- **Wired KiCad schematic generated** (kicad/): root + 8 hierarchical sheets
  (power_supply, preamp, tone_stack, reverb, tremolo, mrb, power_amp, switching)
  via kicad/gen/gen_kicad.py, plus a self-contained primitive symbol library
  (symbols/cr_primitives.kicad_sym).
- **Verified with kicad-cli 7.0.11:** the hierarchy netlists to 94 components,
  56 nets, **0 unconnected pins**, no duplicate references; GND spans 55 nodes;
  all inter-sheet signals resolve. PDF/SVG of all sheets render correctly.
- Connectivity uses global labels (rails/cross-sheet) + local labels; references
  are descriptive to match the BOM/docs.

### Schematic passes ERC (2026-06-14)
- Installed KiCad 8.0.9 (PPA) and ran a real `kicad-cli sch erc`: **0 violations**.
  Fixes: snapped all pins/wires to the 1.27 mm connection grid (was 338 off-grid),
  and gave the footswitch lines (FS_REV/TREM/MRB) a real second endpoint via
  100 k control pulldowns on the effect sheets.
- Added a mid-rail **VBIAS** network (divider on the Power Supply sheet) and
  referenced the TL072 reverb/tremolo stages to it, so the single-supply op-amp
  stages are electrically real (design addition, flagged in the sheets).
- Schematic now 102 components, 58 nets, 0 unconnected, VBIAS spans 10 nodes.
  Remaining to-finish: tone-stack values (TBD) and inter-effect routing order.

### Auto-placed PCB (2026-06-14)
- **Board generated** (kicad/cambridge_reverb.kicad_pcb) via kicad/gen/gen_pcb.py
  using the KiCad 8 pcbnew API: all 102 footprints assigned + placed, 58 nets
  with pads assigned (ratsnest matches schematic), 190×115 mm Edge.Cuts outline,
  bottom-layer GND pour. Footprints carry into the schematic (Footprint field).
- **Placed, not routed.** kicad-cli pcb drc: the report is dominated by 130
  unconnected (unrouted signal nets — GND is poured) plus cosmetic silk/courtyard
  overlaps from dense auto-placement; the netlist itself is correct. See
  kicad/PCB-NOTES.md for the DRC breakdown and remaining hand-work (placement,
  routing, DRC-to-zero, Gerbers).
- Switched the schematic resistor footprint to the compact vertical variant.

### Power-section routing demo + chassis-fit check (2026-06-14)
- **Routed power demo** (kicad/power_section_demo.kicad_pcb): the +33V5 (2.5 mm
  HighCurrent) and +17V (1.5 mm Power) rails + LM317 ADJ node routed over a GND
  pour. kicad-cli pcb drc -> 0 violations. +27V/VRAW left as ratsnest (the +27V
  cross-row link needs a via — documented).
- **Chassis-fit packing-density check** in gen_pcb.py: ~51% on 190×115 (original
  PCB size, feasible-but-tight) vs ~88% on the Part 7 155×90 safe-bet — i.e. the
  102-part through-hole design does NOT fit the smaller chassis comfortably.
  Recorded in kicad/PCB-NOTES.md (ties to errata #9): measure the real chassis,
  or move passives to SMD, before committing to a board size.
