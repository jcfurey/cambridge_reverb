# Component availability, sockets, current-draw & noise audit

Audit of the active/critical parts for **sourceability**, **socketing**, **power
budget / current draw**, and **noise**. Stock/status reflect the project's
2026-era sourcing pass and **will drift — re-verify live before ordering**
(`docs/08-verified-bom.md` is the live-stock reference).

---
## 1. Availability — by tier

### Tier A — jellybean (multi-source, always in stock)
| Part | Role | Notes |
|------|------|-------|
| **TL072** (IC1, IC2) | op-amps | TI/ST/onsemi + clones. DIP-8 ubiquitous. Drop-ins: TL072**C/I**, and pin-compatible TL082, and for lower noise NE5532/OPA2134 (see §4). |
| **LM317T** (U1) | 17 V regulator | TI/onsemi/ST/Diodes Inc. TO-220, ubiquitous. |
| **1N4007 / 1N4148** (D1/D2, D_lfo) | clamps | jellybean. |
| **KBP410G** (BR1) | bridge | Comchip/Diodes/multiple; or 4×1N4007. |
| Resistors (MF 1%), film/ceramic/electrolytic caps | passives | Yageo/Vishay/Panasonic/KEMET — multi-source. |

### Tier B — single-vendor but reliably stocked (guitar-amp niche)
| Part | Role | Risk / alternative |
|------|------|--------------------|
| **LM1875T** (IC_PA) | power amp | TI, **active** but effectively single-source (no true second source). Stock fluctuates. Pin-similar fallbacks need a redesign: **LM1875 → TDA2030A** (close, ~14 W) or a discrete chip-amp; **not** drop-in for layout. Buy a spare. |
| **Accutronics/Belton 4FB2A1C** (REVPAN) | reverb pan | Belton (KOR); stocked by Amplified Parts / Antique Electronic Supply / Mod. Confirm the **4FB2A1C** code (high-Z in). Niche but dependable. |
| **AnTek AS-0524** (T1, if not reusing) | transformer | AnTek-direct, single source. **Reuse the original** if it tests good (Part 8/9). |
| **Fasel inductor** (L1, if not reusing) | MRB tank | Dunlop/specialty. **Reuse the original** ~1 H if DCR 50–100 Ω. |

### Tier C — **watch list** (volatile / specialty)
| Part | Role | Why it's a risk | Action |
|------|------|-----------------|--------|
| **MMBF5457 / J113** (Q1, Q2, Q_rec) | JFET preamp/recovery | Small-signal **JFETs are being discontinued industry-wide**; the TH 2N5457 is already gone (errata #4). MMBF5457 (SOT-23) and J113 (TO-92) are still active at onsemi but treat as **at-risk**. | Buy lifetime stock. Documented alternatives: J113/J112 (adjust Rs), **LSK170** (audio-grade, pricier, different Idss → re-bias), BF245, or 2N5457 if genuine NOS. The 3 JFETs share one type — qualify one substitute for all. |
| **VTL5C1** (VTL1) | tremolo vactrol | Original PerkinElmer is **EOL (RoHS Cd)**; Xvive clone is the only current source (Amplified Parts / Banzai / Xvive). Single-source. | Alternative already designed in: **DIY LED+LDR** vactrol (matched). Stock a couple of VTL5C1. |

**Bottom line:** the design is dominated by jellybeans. The **two real
single-points-of-failure are the JFETs (Tier C) and the LM1875 (Tier B)** — buy
spares of both. Everything else is either multi-source or reuse-from-original.

---
## 2. Sockets — **all DIP chips socketed**
- **IC1, IC2 (TL072, DIP-8): socket — REQUIRED.** Use **machined / turned-pin**
  (precision) sockets, not stamped dual-wipe: better contact reliability, lower
  contact resistance/noise, and they survive re-seating. The PCB DIP-8 footprint
  already accepts a socket (same pad pattern), so no layout change. BOM updated:
  `SOCKET_IC` ×2, machined-pin (e.g. Mill-Max 110-series / Digikey ED3008-5-ND).
- **LM1875 (IC_PA) and LM317 (U1) are TO-220 power devices — not socketed.**
  The LM1875 must bolt to the heatsink with a mica insulator for its thermal path;
  a socket would break that path and the mechanical mount. The LM317 is low-power
  but conventionally soldered. *If* field-swap is wanted, a TO-220 socket/clip can
  be used on the LM317 only (added as an optional BOM line); the LM1875 should stay
  soldered+bolted. So: **every DIP IC is socketed; the power devices are
  heatsink-mounted by design.**

---
## 3. Current draw & power budget
Estimated operating currents per rail (verify on the bench):

### +17 V regulated rail (preamp + effects)
| Load | Current |
|------|--------:|
| Q1, Q2 preamp JFETs (Id) | ~1–2 mA |
| Q_rec recovery JFET | ~0.5 mA |
| IC1 TL072 (Iq) | ~1.4 mA |
| IC2 TL072 (Iq) | ~1.4 mA |
| VBIAS divider (100k+100k) | ~0.09 mA |
| VTL1 LED + LED_rate (avg, LFO-pulsed) | ~3–6 mA |
| **Total +17 V** | **~10–15 mA** |

- **LM317 dissipation:** (Vin − 17.3 V) × ~15 mA. From 27 V that's 0.15 W; even
  direct from 33.5 V it's ~0.24 W → **no heatsink** (matches Part 5).
- **LM317 minimum-load caveat:** the LM317 needs ≥ ~3.5–10 mA load to regulate.
  ~15 mA satisfies it — but if effects are depopulated during bring-up, add a
  small bleed (or the existing load suffices). Worth a bench check.

### `VREG_IN` (LM317 input) — RESOLVED: keep it as a pre-filter, not a "27 V rail"
- In this rebuild the only thing on this node is the **LM317 input** (the op-amps
  run off +17 V, the power amp off +33.5 V) — only ~15 mA. The original `R_27V`
  (47 Ω) drops just **0.7 V** at that current, so the node sits at ~32.8 V, **not
  27 V**: the "27 V rail / 26–28 V" naming was a leftover misnomer.
- **But the resistor is not useless — it's a feature.** `R_27V` + `C_filt1`
  (1000 µF) is an **RC pre-filter on the LM317 input**, and the series R
  **decouples the preamp supply from the power amp's transient current draw** on
  the +33.5 V rail (the LM317's PSRR alone falls off at higher frequency).
  Deleting it would *hurt* noise.
- **Done:** kept the element, **bumped 47 Ω → 100 Ω** (≈6 dB more 120 Hz ripple
  attenuation; only ~1.5 V drop at 15 mA, LM317 in-out diff 14.7 V ≪ 40 V max,
  dissipation 0.02 W), **right-sized 2 W → 1 W**, and **renamed the net `+27V` →
  `VREG_IN`** with the docs/troubleshooting voltage corrected to ~31–33 V. (If you
  ever want a true lower-voltage pre-reg point to cut LM317 dissipation, ~390–470 Ω
  gives ~27 V — but it isn't needed here.)

### +33.5 V main rail (power amp) — corrected (roast R2)
> Earlier this section used 18 W; that's unreachable on a 33.5 V single rail
> (needs 17.0 V peak, only 16.75 V available). The real ceiling is **~12 W clean**.
- LM1875 quiescent ~50 mA; at the real **~12 W into 8 Ω**, peak output current
  ≈ √(2·12/8) = **1.7 A**, average supply current at full sine ≈ peak/π ≈ **0.5 A**
  (guitar program is far lower on average — transient peaks).
- **LM1875 worst-case dissipation** (≈ Vcc²/(2π²·RL) for the single-supply output)
  is **lower than the earlier 15–20 W estimate** at this rail/power, so the
  **≤ 2.5 °C/W heatsink + mica is comfortable** (over-spec'd = safe); thermal
  shutdown still backstops it. C_out (2200 µF) and C_main (4700 µF) are fine.
- **Transformer:** ~12 W out + losses ⇒ ~20 W draw ⇒ **~30 VA minimum**; the
  AnTek AS-0524 (50 VA, 2×24 V @ 1.04 A) is **comfortable headroom** (1.04 A ≫
  0.5 A avg), not a tight match. Bridge KBP410G (4 A) is ample.

---
## 4. Noise
### Already done well (keep)
- **LM317-regulated +17 V preamp rail** — the single biggest hum/noise reduction
  over the original (Part 1).
- **Continuous bottom-layer ground plane** + **star ground** at C_main (Part 3/4).
- **Metal-film 1 % resistors** (low excess/current noise vs carbon).
- **Low-ESR filter caps + rectifier snubbers** (C101–104) — cut diode-switching
  hash and 120 Hz buzz.
- **Signal-left / power-right wire separation**, no signal traces near the
  transformer, none under the LFO timing parts (Part 3/5).
- **JFET preamp** (low-noise, high-Z for the pickup) and **shielded reverb-pan
  cable** (Part 3).

### Recommendations / watch
1. **LED_rate ripple injection (tremolo "tick").** The diagnostic LED draws
   LFO-pulsed current; if it shares the +17 V rail with the preamp it can inject
   LFO-rate ripple → audible ticking. Decouple the LED branch (small series R + the
   rail cap, or a local RC) or drive it from a less sensitive node. Cheap insurance.
2. **VBIAS divider impedance.** 100k+100k = 50k source feeding the op-amp +inputs;
   thermal noise ~28 nV/√Hz. It's bypassed by C_vb (10 µF, corner ~0.3 Hz) so it's
   AC-grounded — fine — but for the reverb driver consider **47k/47k + 47 µF** (or a
   buffer) to drop the source impedance a touch. Minor.
3. **Op-amp choice for the reverb recovery/mix.** TL072 (~18 nV/√Hz) is the
   period-correct, available default. If the reverb path is hissy, **NE5532**
   (~5 nV/√Hz) or **OPA2134** are pin-compatible drop-ins (sockets make this a
   tweak, not a rework) — at slightly higher Iq.
4. **High-Z input.** The 1 MΩ JFET gate is hum-prone; keep input wiring short and
   shielded, grounded at the jack (already noted in Part 3).
5. **Mains safety = mains quiet.** 3-wire ground bonded to chassis; the snubbers
   and a properly grounded transformer frame keep 50/60 Hz down.

---
## Action items
- **Sockets:** done in BOM (machined-pin DIP for IC1/IC2; power devices stay
  heatsink-mounted).
- **+27 V dropper → `VREG_IN` pre-filter (DONE):** kept the element (it's a noise
  feature), bumped 47 Ω→100 Ω / 2 W→1 W, renamed the net, corrected the docs &
  troubleshooting voltage (~32 V, not 27 V). Schematic/PCB regenerated.
- **Stock risk:** buy spare **JFETs** and a spare **LM1875**; qualify one JFET
  substitute for all three positions.
- **LED_rate decoupling:** add a local RC on the indicator branch.
