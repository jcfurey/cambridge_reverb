# Offset audit -- kicad/cambridge_reverb.kicad_pcb

## 1. Track ends

| lands on | ends | off-centre | largest offset | touching with the end cap only |
|---|---:|---:|---:|---:|
| a pad | 591 | **0** | 0.0 mm | 0 |
| a via | 235 | **0** | 0.0 mm | 0 |
| another track | 2402 | **0** | 0.0 mm | 0 |

Free ends (land on nothing): 0.

## 2. Placement file

0 SMD footprints: largest distance between a footprint's origin (what the pick-and-place file reports) and the centre of its pads **0.0 mm**; off-centre: none; parts not at a multiple of 90 degrees: none.

Rotation added to KiCad's angle for JLCPCB's library, per package: . These are the commonly used offsets, not a guarantee: JLCPCB's placement preview is the check.

## 3. DC paths

87 nets. Without a DC path on the board: `GUITAR_IN`, `MIDSW`, `MRB_OUT`.

- `GUITAR_IN`: 10 M across the lugs of input jack 1
- `MIDSW`: 1 M across the mid-cut switch
- `MRB_OUT`: none: do not rest a meter on TP MRB with the amplifier turned up

Defined only while the reverb tank is plugged in (through its coils): `TANK_IN`, `TANK_OUT`, `TKDRV`.


## 4. Voltage drop along the supply traces (DC operating point)

| rail | from | to | load | trace resistance | drop with every load on |
|---|---|---|---:|---:|---:|
| `+33V5` | C_main.1 | IC_PA.5 (LM1875 at full sine power (70 mA idle, 2 A peaks)) | 640 mA | 20.1 mohm | 12.87 mV |
| `+33V5` | C_main.1 | R_27V.1 (regulator pre-filter) | 32 mA | 32.5 mohm | 1.13 mV |
| `+33V5` | C_main.1 | R_bleed.1 (bleeder) | 3.4 mA | 20.5 mohm | 0.74 mV |
| `+33V5` | C_main.1 | R_bias1.1 (PA bias divider) | 0.8 mA | 57.7 mohm | 0.77 mV |
| `PGND` | C_main.2 | IC_PA.3 (LM1875 return) | -640 mA | 27.6 mohm | -17.68 mV |
| `PGND` | C_main.2 | R_spk_rtn.2 (signal-ground return through the star) | -32 mA | 24.9 mohm | -0.8 mV |
| `VREG_IN` | R_27V.2 | U1.3 (LM317 input) | 32 mA | 72.6 mohm | 2.32 mV |
| `+17V` | U1.2 | IC1.8 (reverb driver / mixer TL072) | 3 mA | 181.4 mohm | 2.88 mV |
| `+17V` | U1.2 | IC2.8 (LFO / output buffer TL072) | 3 mA | 174.0 mohm | 2.72 mV |
| `+17V` | U1.2 | IC3.4 (tone TL074) | 5.6 mA | 198.8 mohm | 3.04 mV |
| `+17V` | U1.2 | R_c.1 (vactrol LED (average with the tremolo on)) | 4 mA | 127.0 mohm | 2.49 mV |
| `+17V` | U1.2 | R_pre.1 (JFET rail) | 2.4 mA | 72.5 mohm | 1.65 mV |
| `+17V` | U1.2 | R_reg1.1 (LM317 divider) | 5.2 mA | 62.1 mohm | 1.46 mV |
| `+17V` | U1.2 | R_vbr1.1 (VBIAS_R divider) | 0.09 mA | 149.7 mohm | 2.49 mV |
| `+17V` | U1.2 | R_vbt1.1 (VBIAS_T divider) | 0.09 mA | 139.1 mohm | 2.61 mV |
| `+17V` | U1.2 | R_vb31.1 (VBIAS_3 divider) | 0.09 mA | 188.5 mohm | 2.93 mV |
| `+17V` | U1.2 | R_b1.1 (LED driver bias) | 0.09 mA | 107.6 mohm | 2.15 mV |
| `+17V_PRE` | R_pre.2 | R_d1.1 (Q1) | 0.8 mA | 230.1 mohm | 0.43 mV |
| `+17V_PRE` | R_pre.2 | R_d2.1 (Q2) | 0.8 mA | 217.5 mohm | 0.42 mV |
| `+17V_PRE` | R_pre.2 | R_rec1.1 (Q_rec (reverb recovery)) | 0.8 mA | 84.7 mohm | 0.2 mV |
