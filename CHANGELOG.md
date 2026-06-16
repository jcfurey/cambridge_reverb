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
  56 nets (grew to 102/58 with the VBIAS + footswitch-pulldown additions below),
  **0 unconnected pins**, no duplicate references; GND spans 55 nodes;
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
  pour. kicad-cli pcb drc -> 0 violations. VREG_IN/VRAW left as ratsnest (the VREG_IN
  cross-row link needs a via — documented).
- **Chassis-fit packing-density check** in gen_pcb.py: ~51% on 190×115 (original
  PCB size, feasible-but-tight) vs ~88% on the Part 7 155×90 safe-bet — i.e. the
  102-part through-hole design does NOT fit the smaller chassis comfortably.
  Recorded in kicad/PCB-NOTES.md (ties to errata #9): measure the real chassis,
  or move passives to SMD, before committing to a board size.

### Audit, sockets, schematic centering & VREG_IN pass (2026-06-15)
- **Availability / sockets / current / noise audit** (docs/component-availability-
  audit.md): parts tiered by sourceability (JFETs + LM1875 are the single-points-
  of-failure); DIP op-amp sockets made REQUIRED (machined-pin); per-rail current
  budget; noise review. (Power-budget numbers were later corrected — see roast R2.)
- **+27V → VREG_IN:** kept the R_27V/C_filt1 element as an LM317-input RC pre-filter
  + power-amp decoupler (a noise feature), bumped 47Ω→100Ω/2W→1W, renamed the net
  and corrected the "27V rail" misnomer (~32V) across schematic/PCB/docs.
- **Schematic pages centered**; **PCB layout audit** (kicad/PCB-AUDIT.md) with the
  off-board-pot footprint fix + grid centering; **SPICE audit** (block-level).

### Roast pass (2026-06-16) — see docs/roast-2026-06-16.md
- 🔴 **R1 added a MAINS PRIMARY FUSE** (was missing — only a secondary fuse
  existed; a mains-powered amp needs primary fusing). BOM + Part 1 safety/Part 3.
- 🔴 **R2 corrected the power spec:** 18 W is unreachable on the 33.5 V single rail
  (needs 17.0 V peak, only 16.75 V available) → real ceiling ~12 W. Fixed Part 1,
  Part 5 thermal, and the availability audit (which I'd built on the bad 18 W).
- 🟠 **R3** rebalanced the broken reverb mixer (R_dry_tap 1M→220k) and flagged that
  the unbuffered inter-effect chain needs a real summing stage before fab.
- 🟠 **R4** marked the orphaned `Wiring_Edge_Array_35` footprint as unused.
- 🟡 **R5–R8:** F1 inrush-path placement, shared-VBIAS tremolo bleed, the rail-less
  SPICE scope caveat, and this CHANGELOG cleanup — all documented.

### Schematic completion + generated BOM (2026-06-16)
- **Completed the schematic** — added parts that were in Part 2/the BOM but never
  placed: the four rectifier snubbers (C101–C104), the 2nd pre-filter cap
  (C_filt2), and the tremolo **speed/depth pots** (POT_SPD as a rheostat in the
  Wien arm, POT_DPT scaling the LFO into the LED). 117 components, ERC 0.
- **BOM is now GENERATED from the schematic** (`kicad/gen/gen_bom.py`): every
  reference is 1:1 with the netlist (no more drift — the hand BOM had ~20 missing
  and ~20 stale rows), merged with curated P/Ns + notes and an explicit
  off-board/mechanical section. Added `bom/bom-grouped.csv` (by value, for
  ordering). Density rose to 53 % / 90 % (190×115 / 155×90) — reinforces the
  chassis-fit finding.

### Effects-chain redesign (2026-06-16) — resolves roast R3 + R6
- **Active reverb wet/dry summer** on the spare IC1-B half (inverting summer about
  VBIAS_R: dry always on, wet via POT_REV, unity each). Removed the broken passive
  R_dry_tap/R_blend1/R_blend2 mixer.
- **Output buffer** on the spare IC2-B half drives PA_IN from the post-MRB node
  (removed the unbuffered R_painput 1 M and the dead C_trem_out/R_trem_pass branch).
- **Split bias:** VBIAS → independent **VBIAS_R / VBIAS_T** dividers (100k/100k +
  47 µF each) so the LFO can't modulate the reverb reference.
- **Rail-aware verification:** new `models/opamp_rail.sub` (output clamped to the
  supplies) + `spice/tran_reverb_mixer.cir` confirm single-supply mid-rail bias
  (8.50 V), unity sum, and ±7 V headroom before clipping — the kind of large-signal
  check the rail-less model couldn't do (roast R7).
- ERC 0; full board regenerated (106 footprints); demo DRC 0; BOM updated.
