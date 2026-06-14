# Vox Cambridge Reverb — Part 10: KiCad Project Files

> Reconstructed document — see `PROVENANCE.md`. The original `.kicad_pro`,
> `.kicad_sch`, and custom libraries were generated as a downloadable zip that
> was not retained. This document records their documented structure so the
> project can be rebuilt; the netlist notes in `../kicad/` carry the recovered
> per-sheet connection detail.
>
> **Update (2026-06-14):** the project file and custom libraries have been
> re-authored and now exist in `../kicad/` — `cambridge_reverb.kicad_pro`
> (with the corrected three net classes from the errata consistency pass),
> `symbols/cambridge_reverb.kicad_sym`, `footprints/cambridge_reverb.pretty/`,
> and the `*-lib-table` files. The eight hierarchical `.kicad_sch` sheets are
> built in the GUI following `../kicad/SCHEMATIC-BUILD.md`.

## Project structure (as documented)
- `.kicad_pro` — JLCPCB-compatible design rules; two net classes (Default 0.3 mm
  signals, Power 1.5 mm rails); hierarchical sheet structure for 8 blocks.
- `.kicad_sch` — 8 hierarchical sheets following signal flow:
  Power Supply → Preamp → Tone Stack → Reverb → Tremolo → MRB → Power Amp → Switching.
- Custom symbol library: VTL5C1 optocoupler (4-pin), Accutronics reverb tank
  (4-pin), 6-pin DIN footswitch connector.
- Custom footprint library: VTL5C1 (4-pin inline), MRB 1H toroid (2-pad, 25 mm
  spacing), 35-pad wiring edge array (3 mm pads, 1.5 mm drill, silkscreen-labeled).

## Rebuilding
Recreate the project in KiCad using Part 2 (schematic values), Part 4 (design
rules/Gerber export), and the netlist notes in `../kicad/netlist-notes.txt`
(recovered per-sheet connections for the power amp, reverb, tremolo, and MRB).
