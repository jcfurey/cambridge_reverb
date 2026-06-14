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
