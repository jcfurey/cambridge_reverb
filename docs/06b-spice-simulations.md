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

## ngspice companion set + verified results (2026-06-14)
The original `.cir` is LTspice-flavored (`UniversalOpamp2`, `opamp.sub`). An
**ngspice-runnable** set was added so the design can be re-verified with an
open-source tool — `apt install ngspice`, then `cd ../spice && ./run_all.sh`.
Measured vs. documented:

| Block | Measured (ngspice-42) | Documented |
|-------|-----------------------|------------|
| Power-amp gain | 27.21 dB (23.0×) | 23× / 27.2 dB ✅ |
| Power-amp HF −3 dB | 6.83 kHz (with `C_fb_hf`) | ~7.2 kHz ✅ |
| Power-amp LF −3 dB | 17.2 Hz | "7.2 Hz" — see below ⚠️ |
| Reverb-driver gain | 20.83 dB (11.0×) | 11× ✅ |
| MRB peak | 577 Hz | ~610 Hz ✅ |
| Tremolo LFO | 15.9 Hz = 1/(2πRC) | RC-set ✅ |
| Preamp drain | 12.1 V (Rs 2.2 k) | 8–9 V — see below ⚠️ |

Two corrections fell out of running it: the power-amp LF corner is ~17 Hz (the
input pole adds to `C_gain`; fine for guitar), and the preamp wants Rs ≈ 1–1.2 kΩ
(not 2.2 kΩ) to hit the 8–9 V drain target. Both are in `errata.md` and
`../spice/README.md`.
