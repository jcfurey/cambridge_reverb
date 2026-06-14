# Vox Cambridge Reverb — Part 6B: Guitar-Optimized SPICE Simulations

> Reconstructed document — see `PROVENANCE.md`. The LM1875 power-amp netlist is
> recovered substantially verbatim. The actual `.cir`/`.asc` source files live
> in `../spice/`. This supersedes the original Part 6.

## Guitar-optimization parameters (recovered verbatim from project)
- 100 pF presence rolloff cap at Q2 drain
- 1 nF feedback cap across LM1875 R_fb → 7.2 kHz bandwidth limit
- 470 pF treble cap for Vox chime character
- Guitar pickup model: 3 H / 6 kΩ / 100 pF, with 300 pF cable capacitance
- 10" speaker model: 105 Hz mechanical resonance + voice-coil inductance

## LM1875 power-amp simulation note
TI provides no official LTspice model for the LM1875, so it is modeled with
`UniversalOpamp2` with parameters matched to LM1875 specs (Aol ≈ 100k, GBW ≈
2.5 MHz, slew ≈ 18 V/µs, Rout ≈ 0.1 Ω), output clipped by the supply rails.
Supply: +33.5 V single rail, 8 Ω load. Closed-loop gain 23× (27 dB).

The full netlist is in `../spice/power_amp_lm1875.cir`. See that folder's README
for the list of the six circuit-block simulations.
