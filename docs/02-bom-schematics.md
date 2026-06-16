# Vox Cambridge Reverb V1031/V1032 — Part 2: BOM & Circuit Schematics

> Reconstructed document — see `PROVENANCE.md`. The power-supply BOM table, the
> tremolo/effects-loop/power-amp ASCII schematics, the gain/bandwidth math, and
> the biasing procedure are recovered substantially verbatim. The preamp,
> tone-stack, and reverb BOM rows marked `[RECONSTRUCTED]` were not fully
> recovered — verify their values against the SPICE netlist and Part 8 before ordering.
>
> **For orderable, availability-checked part numbers, Part 8 is authoritative.**
> Where this part and Part 8 differ, Part 8 wins (e.g. JFET, bridge rectifier).

## Bill of materials

### Power supply

| Ref | Description | Value | Package | Mouser P/N | ~Price |
|-----|-------------|-------|---------|------------|--------|
| BR1 | Bridge rectifier | 4A 1000V | Through-hole | 821-KBU4M (see Part 8: KBP410G preferred) | $0.65 |
| C101–104 | Rectifier snubbing caps | 10nF 100V ceramic | Disc | 594-K104Z15Y5VF5TL2 | $0.10 ea |
| C_main | Main filter cap | 4700µF 50V low-ESR | Radial | 667-EEU-FC1H472 | $3.50 |
| C_filt1 | Secondary filter | 1000µF 50V low-ESR | Radial | 667-EEU-FC1H102 | $1.20 |
| C_filt2 | Secondary filter | 1000µF 50V low-ESR | Radial | 667-EEU-FC1H102 | $1.20 |
| U1 | Voltage regulator (17V rail) | LM317T | TO-220 | 926-LM317T/NOPB | $1.50 |
| R_reg1 | Regulator set resistor | 240Ω 1% 1/4W metal film | Axial | 603-MFR-25FBF52-240R | $0.10 |
| R_reg2 | Regulator set resistor | 3.0kΩ 1% 1/4W metal film | Axial | 603-MFR-25FBF52-3K | $0.10 |

> **Errata Issue 10:** 240 Ω + 3.0 kΩ gives Vout = 1.25 × (1 + 3000/240) =
> **16.88 V**, ~0.13 V below the 17.0–17.5 V band quoted in the setup/troubleshooting
> tables. For 17.0–17.5 V use **R_reg2 = 3.09 kΩ (E96)** (→ 17.34 V); the BOM uses
> this value. Alternatively accept ~16.9 V and read the band as 16.8–17.5 V.
| C_reg_in | Regulator input cap | 10µF 50V tantalum | Radial | 581-TAP106K050SCS | $0.80 |
| C_reg_out1 | Regulator output cap | 10µF 25V tantalum | Radial | 581-TAP106K025SCS | $0.60 |
| C_reg_out2 | Regulator output bypass | 100nF 50V MLCC | Disc/radial | 594-K104K15X7RF5TL2 | $0.10 |
| R_27V | LM317-input pre-filter / power-amp decoupling (net `VREG_IN`, ~32 V) | 100Ω 1W metal oxide | Axial | — | $0.20 |
| F1 | Secondary fuse | 1A 250V slow-blow | PCB mount | 576-0273001.H | $0.40 |
| F1_holder | Fuse holder | PCB mount 5×20mm | — | 534-3557 | $0.60 |

### Preamp (JFET) `[RECONSTRUCTED rows — verify vs SPICE/Part 8]`

| Ref | Description | Value | Notes |
|-----|-------------|-------|-------|
| Q1, Q2 | N-ch JFET | MMBF5457 (SOT-23 + adapter) or J113 | See Part 8. Bias targets 2N5457 specs |
| R_g | Gate bias to GND | 1MΩ | High-Z input |
| R_d | Drain load | ~10kΩ | Set Vd ≈ 8–9V |
| R_s | Source self-bias | ~2.2kΩ | With bypass cap |
| C_s | Source bypass | 10µF/25V | |
| C_in | Input coupling | ~47nF film | |
| C_pres | Presence rolloff at Q2 drain | 100pF | Guitar-frequency optimization |
| C_treble | Vox "chime" treble cap | 470pF | |

### Power amplifier (LM1875) — recovered verbatim

| Ref | Description | Value | Notes |
|-----|-------------|-------|-------|
| IC_PA | Power amplifier, TO-220 | LM1875T/NOPB | |
| R_bias1 | Input bias high | 22K 1% | V+ to input |
| R_bias2 | Input bias low | 22K 1% | input to GND |
| R_fb | Feedback resistor | 22K 1% | |
| C_fb_hf | Feedback HF rolloff (across R_fb) | 1nF | 7.2 kHz bandwidth limit |
| R_gain | Gain-setting resistor | 1K 1% | |
| C_gain | Gain cap (LF rolloff) | 22µF/25V | |
| C_in | Input coupling (film) | 1µF/50V | |
| C_out | Output coupling | 2200µF/35V | **Required** for single-supply (Errata Issue 7) |
| R_zobel | Zobel network R | 10R 1W | |
| C_zobel | Zobel network C (film) | 100nF/100V | |
| C_byp1 | V+ bypass MLCC | 100nF/50V | |
| C_byp2 | V+ bypass electrolytic | 10µF/50V | |
| D1 | Output clamp to V+ | 1N4007 | |
| D2 | Output clamp to GND | 1N4007 | |

### MRB — recovered verbatim

| Ref | Description | Value | Notes |
|-----|-------------|-------|-------|
| L1 | MRB inductor | 1H toroid | Reuse original or 2× 0.5H wah (Fasel) |
| C_mrb2 | 600 Hz position (default) | 68nF/50V film | f = 1/(2π√(LC)) ≈ 610 Hz |
| C_mrb1 | 450 Hz position (optional) | 120nF/50V film | ≈ 460 Hz |
| C_mrb3 | 750 Hz position (optional) | 47nF/50V film | ≈ 734 Hz |
| C_mrb_in | Input coupling | 100nF/50V film | |
| C_mrb_out | Output coupling | 100nF/50V film | |

## ASCII schematics

### Power amplifier (LM1875, single supply) — recovered verbatim
```
# LM1875 pin assignments:
#   Pin 1: Non-inverting input (+)
#   Pin 2: Inverting input (-)
#   Pin 3: V- (GND for single-supply)
#   Pin 4: Output
#   Pin 5: V+ (+33.5V)
#
# Connections:
#   AUDIO_IN -> C_in(1uF) -> node_A
#   +33.5V   -> R_bias1(22K) -> node_A
#   node_A   -> R_bias2(22K) -> GND
#   node_A   -> IC_PA pin1 (+)
#   IC_PA pin2 (-) -> R_fb(22K)   -> IC_PA pin4 (output)
#   IC_PA pin2 (-) -> R_gain(1K)  -> C_gain(22uF) -> GND
#   IC_PA pin3 -> GND
#   IC_PA pin5 -> +33.5V
#   C_byp1, C_byp2: pin5 to GND (close to IC)
#   IC_PA pin4 -> C_out(2200uF) -> SPEAKER(+)
#   SPEAKER(-) -> GND (star ground point)
#   R_zobel(10R) + C_zobel(100nF) in series: pin4 to GND
#   D1: pin4(cathode) -> +33.5V(anode)   [clamp to V+]
#   D2: GND(cathode)  -> pin4(anode)      [clamp to GND]
#
# GAIN: Av = 1 + (R_fb / R_gain) = 1 + 22000/1000 = 23 (27.2 dB)
#   Adjustable: R_gain = 2.2K -> Av = 11;  R_gain = 470R -> Av = 48 (max rec.)
# BANDWIDTH:
#   Low -3dB:  f_L = 1/(2π × R_gain × C_gain) = 7.2 Hz
#   High -3dB: set by C_fb_hf(1nF) across R_fb -> ~7.2 kHz (guitar limit)
```

### Tremolo (Wien-bridge LFO + LED/LDR) — recovered verbatim
```
#   IC_TREM   TL072CP    LFO oscillator (uses half)
#   VTL1      VTL5C1     LED/LDR optocoupler
#   R_lfo1/2  33K 1%     Wien bridge R (fixed)
#   R_led     1K         LED current limiter
#   R_led2    1K         Panel/diagnostic LED limiter
#   R_trem1   10K 1%     Signal series resistor
#   C_lfo1/2  100nF/50V  Wien bridge timing C (film)
#   D_lfo1/2  1N4148     Amplitude clamp (back-to-back)
#   LED_rate  3mm red    Diagnostic rate indicator
#   POT_SPD   500K lin   Tremolo speed
#   POT_DPT   100K lin   Tremolo depth
#
#   Output: Pin1 -> POT_DPT(wiper) -> R_led(1K) -> VTL1(LED anode)
#           VTL1(LED cathode) -> GND
#           Pin1 -> R_led2(1K) -> LED_rate -> GND
#   Signal: Audio_in -> R_trem1(10K) -> Audio_out
#                              |
#                          VTL1(LDR)
#                              |
#                             GND
#   When LED bright -> LDR low -> signal shunted; LED dim -> signal passes.
#   LFO freq: f = 1/(2π R C), ~1 Hz (R=500k+33k) to ~10 Hz (R≈33k)
```

### Effects loop (internal) — recovered verbatim
```
    FROM VOLUME POT WIPER
         |
         +---- FX SEND JACK (tip)   (switching: normals to return when no plug)
         |          |
         |      R_fx_pad (10kΩ)
         |          |
         +---- FX RETURN JACK (tip)
         |          |
         +---- TO POWER AMP INPUT
```

## Biasing & setup procedure — recovered verbatim

### Step 1: Power-supply verification (no signal)
1. Apply power through a 60 W incandescent bulb in series with AC mains (current limiter).
2. Main rail: 33–35 VDC.
3. LM317 input (`VREG_IN`, after the R_27V/C_filt1 pre-filter): ~31–33 VDC (this
   node is *not* a regulated 27 V — it tracks the main rail minus ~1 V).
4. Regulated 17 V rail: 17.0–17.5 VDC.
5. Confirm before proceeding to signal stages.
