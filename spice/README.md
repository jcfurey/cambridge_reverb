# spice/

LTspice simulations (guitar-optimized). Supersedes the original Part 6.

- `power_amp_lm1875.cir` — LM1875 power amp, single supply, recovered verbatim.

The original set covered six circuit blocks (preamp, tone stack, reverb,
tremolo, MRB, power amp). Only the power-amp netlist was recovered verbatim;
the others can be rebuilt from `../kicad/netlist-notes.txt` and Part 2 values.
Guitar-optimization parameters are documented in `../docs/06b-spice-simulations.md`.

## Rebuild items for `power_amp_lm1875.cir` (see `../bom/cross-check.md` §3)
The recovered `.cir` is left verbatim, but it is simplified vs. the documented
guitar-optimized model. To reproduce the docs, add:
- `C_fb_hf PA_OUT NODE_FB 1n` — the 1 nF feedback cap for the ~7.2 kHz bandwidth
  limit (present in Part 2 / netlist / BOM, but missing from the netlist).
- A 10" speaker model (105 Hz mechanical resonance + voice-coil inductance) in
  place of the plain 8 Ω `R_speaker`.
- A guitar pickup/cable source model (3 H / 6 kΩ / 100 pF + 300 pF cable) at the
  input for the full guitar-optimized chain.
