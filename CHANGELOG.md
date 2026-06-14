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
