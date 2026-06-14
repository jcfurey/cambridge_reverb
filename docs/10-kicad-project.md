# Vox Cambridge Reverb — Part 10: KiCad Project Files

> Reconstructed document — see `PROVENANCE.md`. The original `.kicad_pro`,
> `.kicad_sch`, and custom libraries were generated as a downloadable zip that
> was not retained. This document records their documented structure so the
> project can be rebuilt; the netlist notes in `../kicad/` carry the recovered
> per-sheet connection detail.
>
> **Update (2026-06-14):** the project file, custom libraries, **and the eight
> hierarchical `.kicad_sch` sheets + root now exist** in `../kicad/`.
> `cambridge_reverb.kicad_pro` carries the corrected three net classes;
> `symbols/cambridge_reverb.kicad_sym` + `symbols/cr_primitives.kicad_sym` hold
> the symbols; `footprints/cambridge_reverb.pretty/` the footprints; and
> `gen/gen_kicad.py` generates the wired schematic. Verified with kicad-cli:
> the hierarchy netlists with **94 components and 0 unconnected pins**. See
> `../kicad/SCHEMATIC-BUILD.md` for connectivity method, the verified results,
> and the known simplifications (op-amp single-supply biasing, TBD tone stack).

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
