# Vox Cambridge Reverb — Part 6c: Noise, Hum, Crosstalk and Thermal Models

> Added 2026-09-07. Everything here is reproducible: the netlists live in `../spice/`
> (`spice/run_all.sh` writes the tables to `spice/results/`), the board audit is
> `kicad/gen/crosstalk_audit.py`. Part 6b covers the functional block checks; this part
> asks the questions a bench would ask *after* the amp works: how quiet, how much hum,
> what talks to what on the board, and how hot.

## 1. Noise — `spice/noise_frontend.cir`

Full front end in one `.noise` run: single-coil pickup (6 kΩ + 2.5 H, 470 pF cable) →
JFET preamp → passive James tone stack + TL074 make-up → summer → output buffer →
LM1875 (×23). Op-amps are 18 nV/√Hz voltage-noise sources (`models/opamp_noise.sub`,
every internal resistor declared noiseless), JFETs carry channel + flicker noise, and the
**+17 V rail carries the LM317's own noise** — TI specifies 0.003 % of V_out rms over
10 Hz–10 kHz, i.e. **~510 µV rms**, ~5 µV/√Hz. That matters because a resistor-loaded
common-source JFET stage has essentially **0 dB PSRR**: v_drain/v_rail = r_ds/(r_ds+R_d) ≈ 0.98.

| Supply configuration | Q2 drain noise (rms, 20 Hz–20 kHz) | Input-referred (EIN) | Hiss at the speaker | SNR at 12 W |
|---|---:|---:|---:|---:|
| **As drawn** (no ADJ cap, JFET loads on the raw +17 V) | **10.3 mV** | **37 µV** | 193 mV rms | **34 dB** |
| + `C_adj` 10 µF on the LM317 ADJ pin (~10× less regulator noise) | 1.26 mV | 4.5 µV | 24 mV | 52 dB |
| + `R_pre` 100 Ω / `C_pre` 220 µF decoupled `+17V_PRE` rail for Q1/Q2/Q_rec | 0.75 mV | **2.7 µV** | 14 mV | **57 dB** |
| (reference: rail noise switched off) | 0.75 mV | 2.7 µV | 14 mV | 57 dB |

The regulator was the dominant noise source by **23 dB**; the last row shows the two
cheap parts bring the preamp to its own floor (2.7 µV rms ≈ 19 nV/√Hz input-referred —
the pickup's 6 kΩ alone is 10 nV/√Hz). Both fixes are in the schematic (errata #21).
Remaining floor by contributor at 1 kHz: JFET channel noise + R_d, then the tone stack's
68 k / 10 k network and the ×2 make-up (~4 dB of the total), then the 100 k summer.

## 2. Hum — `spice/ac_hum_psrr.cir`

1 V of 100/120 Hz ripple on +33V5 (real: ~0.25 Vrms at full drive across 4700 µF),
two paths to the speaker:

| Path | As drawn | Fixed |
|---|---:|---:|
| **(A)** LM1875 input bias divider `R_bias1/R_bias2` 22k/22k from +33V5 — no bypass, the divider feeds the + input directly | **+4.3 dB** (ripple → speaker, i.e. ×1.6) → **408 mV rms of hum, −28 dB re 12 W** | divider node bypassed (`C_bref` 100 µF) and fed to the + input through `R_bias3` 22 k: **−58 dB**, 0.3 mV |
| **(B)** +33V5 → 100 Ω/2000 µF → LM317 (65 dB) → +17 V → JFET drains (0 dB PSRR) → ×13 → ×23 | −57 dB, 0.36 mV | with `C_adj` (80 dB): −72 dB; with the `+17V_PRE` RC too: −95 dB |

Path A was the design's loudest defect: an idle amp humming at −28 dB below full power.
The textbook single-supply input network (bypassed divider + series resistor) is now on
the power-amp sheet; the LM1875's own 52 dB PSRR handles the supply pin. Total hum after
the fixes: **0.3 mV rms at the speaker, −90 dB re 12 W**.

## 3. Tremolo depth — `spice/tran_tremolo_depth.cir`

Errata #19 fixed the LFO; this model follows the modulation to the audio, with a
behavioural VTL5C1 (datasheet LDR-vs-LED-current curve: 20 k @ 1 mA, 600 Ω @ 10 mA,
200 Ω @ 40 mA, 50 MΩ dark; ~5 ms response) shunting the 10 k series resistor.

| | LFO swing | Vactrol LED current | LDR | Insertion loss | **Depth** |
|---|---:|---:|---:|---:|---:|
| As drawn (LED from the depth-pot wiper via 1 k to GND) | 0.50 V pk | 6.4–7.4 mA **DC** | 960–1200 Ω | **−19.5 dB** | **1.7 dB** |
| Redesign | 2.1 V pk | 0–4.7 mA | 1.9 k–50 MΩ | −0.8 dB | **15 dB** |

The LFO sits at the 8.5 V mid-rail, so wiring its LED to ground gave 7 mA of DC with a
±0.5 mA wiggle: the vactrol was a fixed −20 dB pad, not a tremolo. Redesign (errata #22):
the 1N4148 limiter pair becomes two antiparallel **red LEDs** across `R_lfo_fb1` (knee
~1.6 V → 2 V swing; one of them *is* the rate indicator, so `LED_rate`/`R_led_diag` go
away), and an NPN emitter follower (`Q_trem`, 2N3904/MMBT3904), AC-coupled from the depth
pot (`C_drv` 100 µF, base biased at ~0.9 V by 180 k/10 k, `R_e` 470 Ω) drives the vactrol
LED from +17 V through `R_c` 100 Ω: 0…6 mA at the LFO rate, 15 dB of depth at maximum,
0.8 dB insertion loss. The half-wave drive plus the LDR's 35 ms decay give a smooth,
slightly asymmetric pulse — the classic optical-tremolo feel.

## 4. Crosstalk on the routed boards — `kicad/gen/crosstalk_audit.py`

A geometric screen, not a field solver: every pair of parallel track runs (within 20°,
< 4 mm apart, ≥ 0.5 mm overlap) between an *aggressor* net (PA_OUT / SPK / ZOB 9.8 Vrms,
AC1/AC2 24 Vrms, VRAW, +33V5 ripple, TANK_IN 3 Vrms) and a *sensitive* net gets a mutual
capacitance (Howard-Johnson coupled-microstrip estimate over the 1.5 mm ground pour), and
the coupled voltage is `V_aggr · |Z_victim| · 2πf · C_m` against an assumed signal level.
Loop gain = forward gain (node → PA_OUT) + coupling.

Worst pairs on the routing *before* the clearance rules:

| Board | Aggressor → victim | C_m | Coupled vs signal | Loop gain |
|---|---|---:|---:|---:|
| THT | `TANK_IN` → `TANK_OUT` (11 mm parallel run) | 0.30 pF | **−37 dB** | — |
| THT | `TANK_IN` → `QRG` / `WET` | 0.13 / 0.32 pF | −44 / −46 dB | — |
| THT | `PA_OUT` → `PA_INV` | 0.42 pF | −70 dB | −97 dB |
| SMD | `PA_OUT` → `TANK_OUT` (0.25 mm apart!) | 0.09 pF | **−37 dB** | **−44 dB** |
| SMD | `TANK_IN` → `TONE_OUT` (14 mm) | 0.46 pF | −53 dB | — |
| both | AC1 / AC2 / +33V5 → anything | — | < −100 dB | — |

Nothing oscillates (worst loop −44 dB), but the reverb *drive* running beside the reverb
*return* at −37 dB adds an un-reverbed leak to the wet signal, and the power-amp output
0.25 mm from the recovery-JFET gate is not how a hand layout would look. Two rules now
carry this into every routing (`kicad/cambridge_reverb.kicad_dru`, and the same numbers
as per-class clearances in the DSN the router sees): **HighCurrent tracks/vias ≥ 0.6 mm
from signal copper**, **tank-drive tracks ≥ 1.2 mm from the return path** (1.0 / 2.0 mm
were tried first: the router then left 14–27 links open, because a class clearance also
binds the traces entering pads that sit 0.8 mm from a neighbour; the 155 × 90 SMD board
takes 0.4 / 0.8 mm). After re-routing: THT worst pair `TANK_IN` → `TANK_OUT` **−50 dB**
(was −37), `PA_OUT` → `PA_BIAS` −66 dB with loop gain −59 dB; SMD `TANK_IN` → `TANK_OUT`
−42 dB (the two nets share adjacent pads on the tank connector), `PA_OUT` → `TANK_OUT` no
longer in the table, worst loop −68 dB. Full tables: `kicad/reports/crosstalk-{tht,smd}.md`,
routing consequences in `kicad/PCB-NOTES.md`.

## 5. Thermal — `spice/tran_thermal_lm1875.cir`

Electro-thermal RC ladder: junction —2 K/W— case —1.6 K/W (greased mica) or 1.0 (bolted
to a grounded sink; the tab is at V− = GND on a single supply)— heatsink (m·0.9 J/K) —
Rth_SA— ambient. Dissipation on the 33.5 V rail into 8 Ω (class B + 2.3 W quiescent):
idle 2.3 W, **worst-case sine 9.4 W** (at 7 W out, V_pk = V_cc/π), 12 W clip point 8.8 W,
loud music ~4 W average.

Steady-state junction temperature, greased mica (Tj limit 150 °C, shutdown ~170 °C):

| Rth_SA (K/W) | idle, Ta 25/40/55 | **worst-case sine**, Ta 25/40/55 | music, Ta 25/40/55 |
|---:|---|---|---|
| 1.5 | 37 / 52 / 67 | 73 / 88 / 103 | 45 / 60 / 75 |
| **2.5** (Part 5 spec) | 39 / 54 / 69 | **82 / 97 / 112** | 49 / 64 / 79 |
| 4 | 42 / 57 / 72 | 96 / 111 / 126 | 55 / 70 / 85 |
| 6 | 47 / 62 / 77 | 115 / 130 / **145** | 63 / 78 / 93 |
| 8 | 52 / 67 / 82 | 134 / **149** / 164 | 71 / 86 / 101 |
| 10 | 56 / 71 / 86 | **153** / 168 / 183 | 79 / 94 / 109 |

So: the **≤ 2.5 K/W** sink Part 5 asks for keeps the junction under 115 °C even in a
55 °C combo cabinet with a continuous sine — comfortable. A 4 K/W sink is fine to 55 °C
ambient; 6 K/W survives a sine test only in a cool room; 8–10 K/W (a small clip-on) is a
music-only sink that *will* hit thermal shutdown on a long sustained note at high volume.
Bolting the tab straight to a grounded sink saves ~6 K at full dissipation. Time to
saturate: a 40 g sink at 4 K/W has τ ≈ 145 s — the heatsink reaches steady state in
about five minutes, and the transient run (60 s worst-case sine / 60 s music, from cold)
peaks at 113 °C, so a set of loud songs is equivalent to the steady-state sine column for
sizing purposes. The junction itself follows in under a second (τ_jc ≈ 0.7 s).

Other dissipators: **LM317** (32 V → 17 V) with the new IC3 and the redesigned LED driver
carries ~25 mA average, ≤ 32 mA at the tremolo peak → 0.4–0.5 W → +25 K on a bare TO-220
(Rth_JA ~50 K/W free-standing): no heatsink needed, as Part 5 says, but bolt it to the
chassis if the amp lives in a hot cabinet. **KBP410G bridge** at 12 W out: I_dc ≈ 0.64 A,
2 × 0.94 V → 1.2 W, +20–30 K on its leads: fine (rated 4 A). **Transformer**: 33.5 V ×
0.64 A ≈ 21 W DC into the amp at full sine drive → ~35 VA continuous for a capacitor-input
bridge; a **25 VA** unit (AnTek AS-0524) is adequate for music (average draw ≈ ¼ of peak)
and will sag a few volts on a sustained full-power sine — acceptable for a 12 W combo,
but do not size smaller. **MRB toroid** (1 H, 600 Hz at ~0.5 V): 0.13 mA of signal current
— core saturation is not a concern.

## 6. What changed in the design because of this part
- errata #21: `C_adj` 10 µF, `R_pre` 100 Ω + `C_pre` 220 µF (`+17V_PRE`), `C_bref` 100 µF +
  `R_bias3` 22 k.
- errata #22: tremolo LED limiter + `Q_trem` driver; `LED_rate` becomes one limiter LED.
- Routing: `.kicad_dru` clearance rules + DSN class clearances (crosstalk).
- Fab: JLCPCB design-rule limits in both projects, fiducials on the SMD board, wide
  TO-92 and 1.5 mm LM1875 pads for the annular-ring minimum, 1206-only SMD capacitors and
  E24 gyrator values for the basic-parts library (Part 4 update).
