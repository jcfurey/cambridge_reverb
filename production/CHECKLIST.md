# Pre-order checklist — mixed SMD/THT board

Order settings and file-by-file instructions: `smd/README.md`. Background and the
JLCPCB design limits: `../docs/04-jlcpcb-fabrication.md`.

## Checked by the tools (run `kicad/gen/build.sh smd`, or `kicad/gen/verify.py smd` on an existing build)

`kicad/reports/verify-smd.txt` is the last result — 64 of 64 on the committed board.

- [x] ERC: 0 violations
- [x] DRC with JLCPCB's limits and the project rules: 0 errors, 0 warnings, **0 open
      connections**
- [x] Schematic and board agree pin for pin; same footprint on every reference
- [x] Every polarised pad is what its datasheet says (diodes, LEDs, electrolytics,
      JFETs, BJT, regulator, power amp, bridge, op-amps, vactrol)
- [x] Clamp diodes reverse-biased; electrolytics the right way round at the DC
      operating point; rectifier not shorted; supply pins; pot directions; footswitch
- [x] Every part labelled on the silkscreen at a legal size; wiring pads labelled
- [x] Project constraints at or above JLCPCB's published limits (re-read 2026-11-11)
- [x] Ground system: signal / ground / signal / ground with nothing routed on a plane,
      no slot along a pin row, copper 0.5 mm off the edge, via fence and stitching,
      a via for every SMD ground pad, through vias only, no stray capacitance in the
      audio band (`kicad/reports/rf-smd.md`)
- [x] BOM = pick-and-place file = placed SMD footprints; an LCSC number on every line
- [x] Gerber zip complete (4 copper layers); drill count = pads + vias
- [x] SPICE suite runs; schematic values = netlist values

## Yours to check

- [ ] **Chassis measured** — the board is 170 × 105 mm with M3 holes 5 mm in from each
      corner (errata #9)
- [ ] **Transformer identified** — centre-tapped (leave `JP_BR` open, CT to the `CT`
      pad) or single winding (fit `JP_BR`, `CT` pad empty). Never both (errata #26)
- [ ] `python3 kicad/gen/jlc_parts.py --check` — parts still in stock
- [ ] JLCPCB's Gerber viewer matches `smd/cambridge_reverb_smd-top.svg`, every layer
- [ ] JLCPCB's placement preview: D1 / D2 cathodes, Q1 / Q2 / Q_rec / Q_trem orientation
- [ ] Mains side: fused IEC inlet (T800 mA at 120 V), earth bonded to the chassis —
      not on this board, and not optional (roast R1)
- [ ] Footswitch pedal: each button shorts its line to the common (errata #27)
