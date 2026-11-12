# Offset audit -- kicad/smd/cambridge_reverb_smd.kicad_pcb

## 1. Track ends

| lands on | ends | off-centre | largest offset | touching with the end cap only |
|---|---:|---:|---:|---:|
| a pad | 593 | **0** | 0.0 mm | 0 |
| a via | 389 | **0** | 0.0 mm | 0 |
| another track | 2044 | **0** | 0.0 mm | 0 |

Free ends (land on nothing): 0.

## 2. Placement file

107 SMD footprints: largest distance between a footprint's origin (what the pick-and-place file reports) and the centre of its pads **0.0 mm**; off-centre: none; parts not at a multiple of 90 degrees: none.

Rotation added to KiCad's angle for JLCPCB's library, per package: C_0805_2012Metric +0 deg (15), C_1206_3216Metric +0 deg (25), D_SMA +0 deg (2), R_0805_2012Metric +0 deg (61), SOT-23 +180 deg (3), SOT-23_MMBT3904_as_EBC +180 deg (1). These are the commonly used offsets, not a guarantee: JLCPCB's placement preview is the check.

## 3. DC paths

89 nets. Without a DC path on the board: **none**.


Defined only while the reverb tank is plugged in (through its coils): `TANK_IN`, `TANK_OUT`, `TKDRV`.


## 4. Voltage drop along the supply traces (DC operating point)

| rail | from | to | load | trace resistance | drop with every load on |
|---|---|---|---:|---:|---:|
| `+33V5` | C_main.1 | IC_PA.5 (LM1875 at full sine power (70 mA idle, 2 A peaks)) | 640 mA | 24.6 mohm | 15.73 mV |
| `+33V5` | C_main.1 | R_27V.1 (regulator pre-filter) | 32 mA | 17.9 mohm | 0.61 mV |
| `+33V5` | C_main.1 | R_bleed.1 (bleeder) | 3.4 mA | 12.5 mohm | 0.44 mV |
| `+33V5` | C_main.1 | R_bias1.1 (PA bias divider) | 0.8 mA | 58.9 mohm | 10.41 mV |
| `PGND` | C_main.2 | IC_PA.3 (LM1875 return) | -640 mA | 29.7 mohm | -19.22 mV |
| `PGND` | C_main.2 | R_spk_rtn.2 (signal-ground return through the star) | -32 mA | 59.6 mohm | -6.82 mV |
| `VREG_IN` | R_27V.2 | U1.3 (LM317 input) | 32 mA | 196.0 mohm | 6.27 mV |
| `+17V` | U1.2 | IC1.8 (reverb driver / mixer TL072) | 3 mA | 199.4 mohm | 3.07 mV |
| `+17V` | U1.2 | IC2.8 (LFO / output buffer TL072) | 3 mA | 83.8 mohm | 1.62 mV |
| `+17V` | U1.2 | IC3.4 (tone TL074) | 5.6 mA | 231.2 mohm | 3.22 mV |
| `+17V` | U1.2 | R_c.1 (vactrol LED (average with the tremolo on)) | 4 mA | 208.3 mohm | 3.12 mV |
| `+17V` | U1.2 | R_pre.1 (JFET rail) | 2.4 mA | 145.6 mohm | 2.56 mV |
| `+17V` | U1.2 | R_reg1.1 (LM317 divider) | 5.2 mA | 33.5 mohm | 0.79 mV |
| `+17V` | U1.2 | R_vbr1.1 (VBIAS_R divider) | 0.09 mA | 252.1 mohm | 3.12 mV |
| `+17V` | U1.2 | R_vbt1.1 (VBIAS_T divider) | 0.09 mA | 167.8 mohm | 2.86 mV |
| `+17V` | U1.2 | R_vb31.1 (VBIAS_3 divider) | 0.09 mA | 184.4 mohm | 2.89 mV |
| `+17V` | U1.2 | R_b1.1 (LED driver bias) | 0.09 mA | 230.9 mohm | 3.12 mV |
| `+17V_PRE` | R_pre.2 | R_d1.1 (Q1) | 0.8 mA | 49.4 mohm | 0.06 mV |
| `+17V_PRE` | R_pre.2 | R_d2.1 (Q2) | 0.8 mA | 16.6 mohm | 0.04 mV |
| `+17V_PRE` | R_pre.2 | R_rec1.1 (Q_rec (reverb recovery)) | 0.8 mA | 128.0 mohm | 0.13 mV |
