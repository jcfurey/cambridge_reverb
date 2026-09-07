# spice/

ngspice simulations for the design blocks: **8 fixed-point block checks** and
**6 parameter sweeps**. `./run_all.sh` runs everything and writes each result
table to **`results/<name>.txt`** — those files are committed as the evidence for
the numbers below (re-run and diff after any value change). The original set was
LTspice (only the power-amp netlist was recovered verbatim; kept as
`power_amp_lm1875.cir` for provenance, it does not run under ngspice).

Requires ngspice (`apt install ngspice`; verified with ngspice-42).

## Files
| File | Block | What it checks |
|------|-------|----------------|
| `dc_preamp_jfet.cir` | Preamp | JFET bias point + midband gain (recovered R_s = 2.2 k) |
| `ac_reverb_driver.cir` | Reverb driver | Non-inverting gain (11×) |
| `ac_mrb.cir` | MRB | Resonant-peak frequency |
| `tran_tremolo_lfo.cir` | Tremolo LFO | Oscillation + rate at the fast end of the **errata #19** network |
| `ac_power_amp_lm1875.cir` | Power amp | Gain + LF/HF −3 dB with `C_fb_hf` + a 10″ speaker model |
| `tran_reverb_mixer.cir` | Reverb summer | **Rail-aware**: mid-rail bias, unity sum, headroom / clipping |
| `ac_tonestack.cir` | Tone | Vox treble-cut, bright vs full-cut |
| `tran_classa_output.cir` | Class-A stage | AB vs A: idle current and crossover THD |
| **`sweep_preamp_bias.cir`** | Preamp | **Vd vs R_s for LO / TYP / HI JFET corners** (datasheet Idss 1–5 mA) |
| **`sweep_tonestack.cir`** | Tone | Response over the whole pot travel |
| **`sweep_lfo_speed.cir`** | Tremolo LFO | Rate and amplitude vs the speed pot (built network) |
| **`sweep_lfo_speed_recovered.cir`** | Tremolo LFO | The recovered single-arm network — evidence for errata #19 |
| **`sweep_classa_bias.cir`** | Class-A stage | Standing current, heat and THD vs the bias spreader |
| **`sweep_pa_headroom.cir`** | Power amp | Clean output ceiling vs the rail (mains −10 % … +10 %) |
| `models/opamp1p.sub` | shared | One-pole op-amp macromodel (small-signal, **no rails**) |
| `models/opamp_rail.sub` | shared | **Rail-aware** one-pole op-amp (output clamped to the supplies) |
| `models/jfet_2n5457.lib` | shared | 2N5457/MMBF5457 nominal model (Idss ≈ 3 mA, Vp = −1.8 V) |
| `run_all.sh` | — | Runs everything, saves `results/`, exit ≠ 0 if ngspice fails |

## Fixed-point results (`results/*.txt`, ngspice-42)
| Block | Measured | Documented | Verdict |
|-------|----------|------------|---------|
| Power amp midband gain | **27.21 dB** (23.0×) | 23× / 27.2 dB | ✅ |
| Power amp HF −3 dB | **6.83 kHz** | ~7.2 kHz (`C_fb_hf`) | ✅ |
| Power amp LF −3 dB | **17.2 Hz** | "7.2 Hz" (C_gain only) | ⚠️ input pole adds a second LF corner — fine for guitar |
| Reverb driver gain | **20.83 dB** (11.0×) | 11× | ✅ |
| MRB resonant peak | **577 Hz** | ~610 Hz (1 H ‖ 68 nF) | ✅ (pulled low by the output network) |
| Tremolo LFO, pot at min | **10.59 Hz**, 0.48 V amplitude | 10.6 Hz = 1/(2π·15 k·1 µF) | ✅ (errata #19 network) |
| Preamp drain Vd (R_s = 2.2 k, nominal JFET) | **12.1 V** | 8–9 V target | ⚠️ see the sweep below |
| Reverb summer bias / gain / clip | **8.50 V**, **0.0 dB**, clips 15.5 / 1.5 V | mid-rail, unity, ±7 V | ✅ |
| Tone bright / full-cut | −1.6 dB flat / −9 dB @ 5 kHz, −14 dB @ 10 kHz | flat / progressive cut | ✅ |
| Class-A stage AB → A | THD 1.05 % → 0.0025 %, idle 0.11 → 0.49 A | crossover removed | ✅ |

## Sweeps
### JFET bias vs R_s across the device spread (`sweep_preamp_bias`, errata #15)
Drain voltage (V) on the +17 V rail with R_d = 10 k. Corners: LO = Idss 1 mA / Vp −0.8 V,
TYP = 3 mA / −1.8 V, HI = 5 mA / −3.0 V (2N5457 & MMBF5457 limits, datasheets committed).

| R_s (Ω) | Vd LO | Vd TYP | Vd HI |
|--------:|------:|-------:|------:|
| 470 | 11.9 | 3.9 | 1.5 |
| 680 | 12.8 | 6.3 | 1.9 |
| **1000** | 13.6 | **8.5** | 2.9 |
| 1200 | 14.0 | 9.5 | 4.5 |
| 1800 | 14.7 | 11.3 | 7.5 |
| **2200** | 15.0 | 12.1 | **8.8** |
| 2700 | 15.3 | 12.8 | 10.0 |

Reading: the recovered **2.2 k is right for a high-Idss part**; a typical part wants
**~1.0 k**; a low-Idss part (1 mA) cannot reach 8–9 V with any R_s — it needs a
larger R_d or should be rejected. Hence "trim per device": measure Idss once
(drain to +17 V via 10 k, gate/source grounded) and pick R_s from the row above.
This is why `R_s1`, `R_s2`, `R_rec2` stay through-hole even on the SMD variant.

### Tone pot travel (`sweep_tonestack`)
| Pot (Ω) | 1 kHz | 3 kHz | 5 kHz | 10 kHz |
|--------:|------:|------:|------:|-------:|
| 100 k (bright) | −1.6 | −1.6 | −1.6 | −1.6 |
| 20 k | −3.1 | −3.9 | −4.0 | −4.1 |
| 10 k | −3.3 | −5.7 | −6.1 | −6.4 |
| 5 k | −2.9 | −7.1 | −8.6 | −9.5 |
| 1 k (full cut) | −2.3 | −7.3 | −10.9 | −15.5 |

The 1 kHz level barely moves (−1.6 … −3.3 dB) while 10 kHz falls 14 dB: a treble
cut, not a volume drop — the Vox character intended.

### Tremolo LFO vs the speed pot (`sweep_lfo_speed` — the built network)
Symmetric Wien, 15 k + one gang of a dual 250 k pot per arm, 1 µF, gain 3.13 + diode limiter.

| Pot (Ω) | f theory | f measured | Vpp |
|--------:|---------:|-----------:|----:|
| 0 | 10.61 Hz | **10.58 Hz** | 0.96 |
| 50 k | 2.45 Hz | 2.44 Hz | 0.96 |
| 100 k | 1.38 Hz | 1.38 Hz | 0.96 |
| 250 k | 0.60 Hz | **0.60 Hz** | 0.96 |

### …and the recovered network (`sweep_lfo_speed_recovered` — why it was changed)
Single-arm pot: series 10 k + 0–500 k, shunt 33 k, 100 nF.

| Pot (Ω) | Series R | f theory | Result |
|--------:|---------:|---------:|--------|
| 0 | 10 k | 87.6 Hz | oscillates, **79.6 Hz**, 1.6 Vpp |
| 20 k | 30 k | 50.6 Hz | oscillates, 50.2 Hz, 1.1 Vpp |
| 27 k | 37 k | 45.5 Hz | marginal, 0.4 Vpp |
| 35 k … 500 k | 45 k … 510 k | 41 … 12 Hz | **no oscillation** |

The Wien start condition is gain > 2 + R1/R2; with a fixed gain of 3.13 the series
arm must stay under ~37 k, so the recovered LFO ran only over ~5 % of the pot and
never below 45 Hz. Errata #19.

### Class-A bias (`sweep_classa_bias`) — the heat/distortion trade
Single +33.5 V rail, ~0.7 W into 8 Ω (0.38 A peak load).

| Bias per base (V) | Standing current | Standing heat | THD |
|--:|--:|--:|--:|
| 0.60 | 0.111 A | 3.7 W | 1.41 % |
| 0.66 | 0.119 A | 4.0 W | 0.40 % |
| 0.70 | 0.173 A | 5.8 W | 0.049 % |
| 0.72 | 0.276 A | 9.2 W | 0.0084 % |
| **0.74** | **0.488 A** | **16.3 W** | **0.0025 %** |
| 0.76 | 0.845 A | 28.3 W | 0.0022 % |

Crossover distortion is gone once the idle current exceeds the peak load current
(≈ 0.4 A); beyond that only the heat grows. 0.74 V ≙ the 0.5 A CCS in the Class-A
variant (`docs/classA-power-amp.md`).

### Power-amp headroom vs mains (`sweep_pa_headroom`, roast R2)
Rail-aware LM1875 model (vsat 3 V), gain 23, 8 Ω, driven into clipping.

| Rail | Output DC | Clean peak swing | Sine power into 8 Ω |
|--:|--:|--:|--:|
| 30.0 V (mains −10 %) | 15.0 V | 11.9 V | **8.9 W** |
| 33.5 V (nominal) | 16.75 V | 13.7 V | **11.7 W** |
| 37.0 V (mains +10 %) | 18.5 V | 15.4 V | **14.8 W** |

Confirms the ~12 W ceiling (not 18 W) and shows it is a mains-voltage lottery of
±3 W. The output DC tracks V+/2 exactly, which is what `TP_PA_OUT` should read.

## Scope caveat (roast R7)
`opamp1p.sub` is rail-less: gain/bandwidth of isolated blocks only. Large-signal
behaviour is covered only where `opamp_rail.sub` is used (reverb summer, headroom
sweep) and in the transistor-level Class-A stage. The LM1875 is a behavioural
model (Aol, GBW, saturation), not TI's — the headroom numbers are a model of the
ceiling, not a measurement. Component tolerances are covered only where swept.
