# Ground-return audit -- kicad/smd/cambridge_reverb_smd.kicad_pcb

Board 170.2 x 105.2 mm; signal-ground copper on F.Cu, In1.Cu, B.Cu, joined by 340 ground vias; solved on a 0.25 mm grid (733159 nodes).

Ground system: GND, PGND, SPK_N, TANK_G -- 4 nets, joined only by R_gnd (SPK_N - GND) and R_spk_rtn (SPK_N - PGND) and R_tg (TANK_G - GND). The planes carry signal ground only.

Rectifier at idle (100 mA): charging pulses peak 0.69 A (2.98 A at full power); AC content 213 mA rms, 72.1 mA A-weighted. First harmonics (mA peak): 100 Hz 190.9, 200 Hz 165.4, 300 Hz 128.3, 400 Hz 86.4, 500 Hz 46.5, 600 Hz 14.4. Reservoir ripple 51.2 mV rms, which drives 0.512 mA rms through the 100 R pre-filter into C_filt1 / C_filt2.

## charge-CT: reservoir charging pulses, centre-tapped transformer (default build)

C_main.2 -> T1.2: 50.2 mm apart in the copper, 24.309 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | 0.00 | 210 | 0.0 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | 0.00 | 63 | 0.0 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | 0.00 | 19 | 0.0 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 0.00 | 23 | 0.0 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | 0.00 | 46 | 0.0 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -0.00 | 575 | -0.0 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 0.00 | 23 | 0.0 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | -0.00 | 23 | -0.0 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | -0.00 | 1.7 | -0.0 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | 0.00 | 1 | 0.0 |

**Hum at the speaker, idle, standard build:** 12.54 uV rms (-117.7 dB re full power) = 0.0 uV from the charging pulses + 12.54 uV from the pre-filter's ripple current returning through the planes; 2.329 uV A-weighted = far below 0 dBA SPL; largest share: PA feedback ground -> speaker return (pre-filter ripple current).

**Same with C_s1 / C_s2 fitted (25x more preamp gain):** 21.37 uV rms (-113.1 dB re full power) = 0.0 uV from the charging pulses + 21.37 uV from the pre-filter's ripple current returning through the planes; 3.969 uV A-weighted = far below 0 dBA SPL; largest share: PA feedback ground -> speaker return (pre-filter ripple current).

## charge-BR: reservoir charging pulses, single winding + JP_BR fitted

C_main.2 -> JP_BR.2: 54.7 mm apart in the copper, 36.684 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | 0.00 | 210 | 0.0 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | 0.00 | 63 | 0.0 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | 0.00 | 19 | 0.0 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 0.00 | 23 | 0.0 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | 0.00 | 46 | 0.0 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -0.00 | 575 | -0.0 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 0.00 | 23 | 0.0 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | -0.00 | 23 | -0.0 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | -0.00 | 1.7 | -0.0 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | 0.00 | 1 | 0.0 |

**Hum at the speaker, idle, standard build:** 12.54 uV rms (-117.7 dB re full power) = 0.0 uV from the charging pulses + 12.54 uV from the pre-filter's ripple current returning through the planes; 2.329 uV A-weighted = far below 0 dBA SPL; largest share: PA feedback ground -> speaker return (pre-filter ripple current).

**Same with C_s1 / C_s2 fitted (25x more preamp gain):** 21.37 uV rms (-113.1 dB re full power) = 0.0 uV from the charging pulses + 21.37 uV from the pre-filter's ripple current returning through the planes; 3.969 uV A-weighted = far below 0 dBA SPL; largest share: PA feedback ground -> speaker return (pre-filter ripple current).

## speaker: loudspeaker return, positive half-cycle (supply -> IC -> speaker -> reservoir)

LS1.2 -> C_main.2: 51.1 mm apart in the copper, 75.538 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | 0.00 | 210 | 0.0 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | 0.00 | 63 | 0.0 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | 0.00 | 19 | 0.0 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 0.00 | 23 | 0.0 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | 0.00 | 46 | 0.0 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -0.00 | 575 | -0.0 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 0.00 | 23 | 0.0 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | -0.00 | 23 | -0.0 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | -0.00 | 1.7 | -0.0 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | -8436.84 | 1 | -8436.8 |

**Loop gain closed through the ground copper, standard build:** none -- this current does not enter the planes.

**Same with C_s1 / C_s2 fitted:** none -- this current does not enter the planes.

Series resistance this return adds to the speaker circuit: 8.44 mohm.

## speaker-IC: loudspeaker return, negative half-cycle (C_out -> IC ground pin -> speaker)

LS1.2 -> IC_PA.3: 86.8 mm apart in the copper, 89.353 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | 0.00 | 210 | 0.0 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | 0.00 | 63 | 0.0 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | 0.00 | 19 | 0.0 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 0.00 | 23 | 0.0 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | 0.00 | 46 | 0.0 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -0.00 | 575 | -0.0 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 0.00 | 23 | 0.0 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | -0.00 | 23 | -0.0 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | -0.00 | 1.7 | -0.0 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | -8436.84 | 1 | -8436.8 |

**Loop gain closed through the ground copper, standard build:** none -- this current does not enter the planes.

**Same with C_s1 / C_s2 fitted:** none -- this current does not enter the planes.

Series resistance this return adds to the speaker circuit: 8.44 mohm.

## prefilter: ripple current of the 100 R / 2000 uF pre-filter

C_filt1.2 -> C_main.2: 16.3 mm apart in the copper, 92.488 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | 3.24 | 210 | 679.8 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | 3.76 | 63 | 236.9 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | 8.62 | 19 | 163.9 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 20.18 | 23 | 464.3 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | 13.01 | 46 | 598.2 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -3.08 | 575 | -1773.3 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 106.34 | 23 | 2445.8 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | -98.00 | 23 | -2253.9 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | -75.51 | 1.7 | -128.4 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | 24065.07 | 1 | 24065.1 |

## LM1875 support parts: distance from the IC pins (mm)

The data sheet: keep the output compensation and the 0.1 uF supply decoupling as close as possible to the LM1875.

- C_byp1 (100 nF) to pin 5: 19.7
- C_byp1 ground to pin 3: 16.3
- C_byp2 (10 uF) to pin 5: 20.8
- R_zobel to pin 4: 14.6
- C_zobel ground to pin 3: 14.3
- C_lp to pin 1: 20.4
- R_fb to pin 2: 19.0
- R_gain to pin 2: 19.1
