# spice/

LTspice simulations (guitar-optimized). Supersedes the original Part 6.

- `power_amp_lm1875.cir` — LM1875 power amp, single supply, recovered verbatim.

The original set covered six circuit blocks (preamp, tone stack, reverb,
tremolo, MRB, power amp). Only the power-amp netlist was recovered verbatim;
the others can be rebuilt from `../kicad/netlist-notes.txt` and Part 2 values.
Guitar-optimization parameters are documented in `../docs/06b-spice-simulations.md`.
