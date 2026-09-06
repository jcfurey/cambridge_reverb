# Changelog

All notable design work on this project. Parts correspond to the structured
deliverables produced during the design phase.

### Footprint fixes, floor-plan placement, headless autoroute (2026-09-06)
- **PCB-AUDIT §1 defects fixed with datasheet-derived project footprints:**
  `TO-220-5_Vertical_P1.70mm_LM1875` (TI NDH0005D inline TO-220-5; 1.1 mm drill,
  **1.45 mm pads → 0.175 mm annular**, was 0.0875 → the 5 `annular_width` DRC
  errors are gone) and `Bridge_KBP_P3.81mm` (Diodes DS39310 KBP404G–KBP410G:
  3.81 mm pitch, 1.2 mm drill, pins **+ ~ ~ −**; replaces the `PinHeader_1x04`
  placeholder). The schematic bridge symbol is renumbered to the KBP physical
  order (1=+ 2=~ 3=~ 4=−). One footprint cannot also take a KBU (5.08 mm pitch) —
  errata #3 updated with the swap procedure.
- **Value-aware footprint sizing** (`gen_kicad.footprint_for`): 4700 µF → D18 P7.5,
  2200 µF → D16 P7.5, 1000 µF → D12.5 P5, 47 µF → D6.3, ≤22 µF → D5 (tantalums on
  2.5 mm); 5 W `R_bleed` → 20 mm power axial, 1 W `R_27V` → DIN0414; the 0 Ω
  speaker-return link `R_spk_rtn` gets 1 W-size pads (it carries the speaker
  current). The old board had every can as D8 and every resistor as ¼ W.
- **`gen_pcb.py` now places to the Part 5 floor plan**: five zones left→right
  (Input/Preamp | Tone | Reverb/Trem+MRB | Power Amp | PSU), widths auto-balanced
  so the columns pack to equal height, signal-chain order inside each zone;
  LM1875/LM317 on the top edge with the 10 mm keep-out; every off-board connector
  on the bottom wiring edge under its zone, `T1` far right; 4 × M3 mounting holes.
  **DRC before routing: 0 errors, 0 warnings** (was 9 errors + ~155 silk warnings).
- **Chassis-fit figure corrected:** the earlier 48–53 % / 82–90 % packing densities
  summed bounding boxes *including hidden text*. Text-less: **~33 % on 190×115,
  ~56 % on 155×90** — the "safe-bet" board is dense but no longer "not buildable"
  (errata #9 still says measure first). Old `unconnected` counts (131) were also
  from the 102-part board; the board is 113 parts / 145 connections now.
- **Wiring edge per Part 4:** the off-board connectors are now project *wire pad*
  footprints (`WirePad_1x0N_P2.54mm_D1.2mm`: 2.0 mm pads / 1.2 mm drill for jacks,
  pots, tank, DIN; `WirePad_1x0N_P5.08mm_D1.5mm`: 3.0 mm pads / 1.5 mm drill for
  the speaker and transformer) instead of 2.54 mm pin headers.
- **Net classes:** `VRAW`, `AC1`, `AC2` (bridge/transformer, full supply current)
  moved from Default 0.5 mm to **HighCurrent** (errata #11 updated).
- **Headless autoroute** — `kicad/gen/route_board.py`: pcbnew DSN export → Freerouting
  → SES import → pour refill. Findings: Freerouting **2.1.0** ignores every pass /
  timeout limit in CLI mode and only writes output at 0 unrouted (and its
  multi-threaded router crashed), so the script drives **1.9.0** under `xvfb-run`
  (honours `-mp`, always writes the SES). The script injects Freerouting's
  `autoroute_settings` into the DSN to make the bottom layer 6× more expensive
  than the top, because a free two-layer run put ~2.4 m of copper on the bottom
  and sliced the GND pour into islands (10–11 GND pads unconnected). The
  LM1875's 1.70 mm pin pitch cannot take a 1.5/2.5 mm trace past its neighbours,
  so `gen_pcb.py` pre-routes two **locked 0.9 mm escape stubs** (pins 4/5) that
  export as fixed wires. Placement was tuned for
  routability along the way (Tone stacked under Preamp, reverb block at the bottom
  of its column next to the tank pads, VBIAS dividers and footswitch pull-downs
  next to their loads, serpentine shelf rows so wrapped rows stay adjacent, a
  wider power-amp column). **Committed board: 144/145 connections routed, 0 DRC
  violations (`--severity-all`), 26 vias**; the one open `PA_OUT` link (blocked by
  `R_bias1`) is documented in `PCB-NOTES.md` as a GUI finish.

### Class-A power-amp variant (2026-06-16)
- Explored running the power amp in **Class A** (AC15-style). Sim
  (`spice/tran_classa_output.cir`): Class A drops crossover THD from ~1.05% to
  ~0.0025% -- the cost is ~16W continuous heat for ~1W of pure Class A (slides to
  AB beyond), documented in `docs/classA-power-amp.md`.
- Built it as a **variant alongside the AB amp** (user choice): standalone
  ERC-clean `kicad/power_amp_classa.kicad_sch` (gen_classa.py) = the LM1875 stage
  + an LM317 constant-current sink (R_set 2.5R -> 0.5A from output to GND) =>
  single-ended Class A up to ~1W. Main board stays Class AB. Adds a 2nd LM317 +
  R_set + bigger heatsinks; ERC 0.

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

### BOM value normalization + README refresh (2026-06-16)
- Generator now normalizes value strings (2K2→2.2k, 4K7→4.7k, drop " film") so the
  grouped BOM consolidates cleanly. ERC/DRC/SPICE unaffected.
- Rewrote the top-level **README** to match the current state: the generated +
  tool-verified KiCad/BOM/SPICE flow, the ~12 W power ceiling, the mains-fuse
  safety note, the 190×115 board / chassis-fit caveat, and the honesty/provenance
  framing. (Was still describing the original reconstructed-docs state.)

### Tone stack designed + verified (2026-06-16)
- The `TONE_STACK` placeholder (TBD) is replaced by a **working passive Vox-style
  tone**: Volume pot + a treble "cut" (C_cut 10 nF + POT_TONE 100 k to ground),
  since the original 25-5274-2 values were never recovered. Response simulated in
  `spice/ac_tonestack.cir`: flat at bright (−1.6 dB), musical treble cut at the
  dark end (−9 dB @ 5 kHz, −14 dB @ 10 kHz). Flagged as a designed substitute
  (the original panel may have had separate Treble/Bass). ERC 0; BOM regenerated.

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
