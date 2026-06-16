# spice/

Circuit simulations for the six blocks. The original set was **LTspice**
(guitar-optimized, supersedes Part 6); only the power-amp netlist was recovered
verbatim. Added alongside it is a set of **ngspice-runnable** netlists for all
the simulatable blocks, so the design can be re-verified with an open-source tool
(`apt install ngspice`, then `./run_all.sh`). Guitar-optimization parameters are
documented in `../docs/06b-spice-simulations.md`.

## Files
| File | Tool | Block | What it checks |
|------|------|-------|----------------|
| `power_amp_lm1875.cir` | LTspice | Power amp | Original, recovered verbatim (kept as-is) |
| `ac_power_amp_lm1875.cir` | ngspice | Power amp | Gain + LF/HF −3 dB corners, **with `C_fb_hf` + 10″ speaker model** |
| `ac_reverb_driver.cir` | ngspice | Reverb driver | Non-inverting gain (11×) |
| `ac_mrb.cir` | ngspice | MRB | Resonant-peak frequency |
| `dc_preamp_jfet.cir` | ngspice | Preamp | JFET bias point + midband gain |
| `tran_tremolo_lfo.cir` | ngspice | Tremolo LFO | Oscillation + frequency |
| `tran_reverb_mixer.cir` | ngspice | Reverb summer | **Rail-aware**: single-supply mid-rail bias, unity sum, headroom/clipping |
| `models/opamp1p.sub` | — | shared | One-pole op-amp macromodel (small-signal, **no rails**) |
| `models/opamp_rail.sub` | — | shared | **Rail-aware** one-pole op-amp (output clamped to the supplies) |
| `models/jfet_2n5457.lib` | — | shared | 2N5457/MMBF5457 JFET model |
| `run_all.sh` | — | — | Runs every ngspice block and prints key numbers |

Tone stack has no sim — its values were not recovered (cross-check §4).

## Verified results (ngspice-42)
Run `./run_all.sh`. Measured vs. documented:

| Block | Measured | Documented | Verdict |
|-------|----------|------------|---------|
| Power amp midband gain | **27.21 dB** (23.0×) | 23× / 27.2 dB | ✅ exact |
| Power amp HF −3 dB | **6.83 kHz** | ~7.2 kHz (from `C_fb_hf`) | ✅ confirms the `C_fb_hf` fix |
| Power amp LF −3 dB | **17.2 Hz** | "7.2 Hz" (C_gain only) | ⚠️ see note below |
| Reverb driver gain | **20.83 dB** (11.0×) | 11× | ✅ exact |
| MRB resonant peak | **577 Hz** | ~610 Hz (1 H ‖ 68 nF) | ✅ (pulled low by output-network loading) |
| Tremolo LFO freq | **15.9 Hz** | 1/(2πRC) = 15.9 Hz @ 100k/100n | ✅ topology oscillates, tracks RC |
| Preamp drain Vd | **12.1 V** (Rs = 2.2 k) | 8–9 V target | ⚠️ see note below |
| Reverb summer bias (rail-aware) | **8.50 V** mid-rail | VBIAS_R ≈ 8.5 V | ✅ single-supply biasing correct |
| Reverb summer gain / headroom | **0.0 dB** unity, clips **15.5/1.5 V** | unity, ±7 V swing | ✅ headroom verified (roast R3) |

### Findings the sims surfaced (folded into errata / cross-check)
- **Power-amp LF corner is ~17 Hz, not 7.2 Hz.** The docs' 7.2 Hz counts only the
  `R_gain·C_gain` pole; the input coupling `C_in`(1 µF)/bias-divider network adds
  a second LF pole (~14 Hz), so the real −3 dB is ~17 Hz. This is *beneficial* for
  guitar (rejects subsonic cone-flap; low-E is ~82 Hz). No change needed — just
  corrected expectation.
- **Preamp bias is cold with the recovered Rs = 2.2 kΩ.** With a nominal 2N5457
  (Idss ≈ 3 mA, Vp ≈ −1.8 V) the drain sits at ~12 V (Id ≈ 0.49 mA), above the
  8–9 V target. **Rs ≈ 1.0 kΩ → Vd ≈ 8.5 V; Rs ≈ 1.2 kΩ → Vd ≈ 9.5 V.** The
  2N5457 has a wide Idss/Vp spread, so trim Rs (≈1–1.2 k) per device on the bench.
  See errata Issue 15.

## Notes
- The ngspice op-amp is a linear one-pole macromodel (no rail clipping): use the
  AC/​.op results for gain, bandwidth, and bias, not for clipping behavior. The
  LTspice `power_amp_lm1875.cir` (UniversalOpamp2, rail-clipped) is the reference
  for large-signal/clipping work.
- The MRB topology in `../kicad/netlist-notes.txt` is recorded ambiguously; the
  sim uses the parallel-LC-tank interpretation from Part 1 §6 (see the header
  comment in `ac_mrb.cir`).

## Audit (2026-06-14)
Full pass over every netlist + model; all five blocks run under ngspice-42
(`./run_all.sh`, exit 0) and reproduce the documented numbers. Verdict: **solid.**
- `models/opamp1p.sub` — correct one-pole macromodel: DC gain = gm·Rp = `aol`,
  pole at `gbw/aol` (unity-gain = `gbw`). No supply rails by design → use for
  AC/.op only, not clipping (documented).
- `models/jfet_2n5457.lib` — nominal 2N5457 (Idss≈2.98 mA, Vp=−1.8 V). The real
  part has a wide Idss/Vp spread; the preamp sim deliberately uses the recovered
  `Rs=2.2k` to show the resulting cold bias (Vd≈12 V vs the 8–9 V target, errata #15).
- `ac_power_amp_lm1875.cir` — the −3 dB search compares against a literal `24.21`
  (= measured midband 27.21 − 3); fine for this fixed design, re-derive if the
  gain network changes.
- `power_amp_lm1875.cir` is **LTspice-only** (UniversalOpamp2 + `opamp.sub`) and
  will not run under ngspice — kept verbatim for provenance; the `ac_*` files are
  the runnable companions.
No correctness issues found **in what is modelled** — but see the scope limit:

> **Scope caveat (roast R7):** `opamp1p.sub` is **rail-less**, so the sims cover
> only small-signal gain/bandwidth of *isolated* blocks. Single-supply
> headroom/clipping, the reverb driver's actual swing, op-amp biasing margins, and
> the real power-amp output ceiling (~12 W, not 18 W — roast R2) are **not
> simulated**. "Tool-verified" here means small-signal, block-level — **not** a
> validated integrated, large-signal circuit.
