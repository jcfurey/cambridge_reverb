# Ground-return audit -- kicad/cambridge_reverb.kicad_pcb

Board 190.2 x 115.2 mm; signal-ground copper on F.Cu, In1.Cu, B.Cu, joined by 376 ground vias; solved on a 0.25 mm grid (887856 nodes).

Ground system: GND, PGND, SPK_N -- 3 nets, joined only by R_spk_rtn (SPK_N - PGND) and R_gnd (SPK_N - GND). The planes carry signal ground only.

Rectifier at idle (100 mA): charging pulses peak 0.69 A (2.98 A at full power); AC content 213 mA rms, 72.1 mA A-weighted. First harmonics (mA peak): 100 Hz 190.9, 200 Hz 165.4, 300 Hz 128.3, 400 Hz 86.4, 500 Hz 46.5, 600 Hz 14.4. Reservoir ripple 51.2 mV rms, which drives 0.512 mA rms through the 100 R pre-filter into C_filt1 / C_filt2.

## charge-CT: reservoir charging pulses, centre-tapped transformer (default build)

C_main.2 -> T1.2: 60.3 mm apart in the copper, 37.751 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | -0.00 | 210 | -0.0 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | -0.00 | 63 | -0.0 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | -0.00 | 19 | -0.0 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 0.00 | 23 | 0.0 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | -0.00 | 46 | -0.0 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -0.00 | 575 | -0.0 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 0.00 | 23 | 0.0 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | 0.00 | 23 | 0.0 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | 0.00 | 1.7 | 0.0 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | 0.00 | 1 | 0.0 |

**Hum at the speaker, idle, standard build:** 27.2 uV rms (-111.0 dB re full power) = 0.0 uV from the charging pulses + 27.2 uV from the pre-filter's ripple current returning through the planes; 5.052 uV A-weighted = -18.0 dBA SPL at 1 m; largest share: tank return -> recovery source (pre-filter ripple current).

**Same with C_s1 / C_s2 fitted (25x more preamp gain):** 76.1 uV rms (-102.1 dB re full power) = 0.0 uV from the charging pulses + 76.1 uV from the pre-filter's ripple current returning through the planes; 14.133 uV A-weighted = -9.0 dBA SPL at 1 m; largest share: input jack sleeve -> Q1 source (pre-filter ripple current).

## charge-BR: reservoir charging pulses, single winding + JP_BR fitted

C_main.2 -> JP_BR.2: 64.8 mm apart in the copper, 39.371 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | -0.00 | 210 | -0.0 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | -0.00 | 63 | -0.0 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | -0.00 | 19 | -0.0 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 0.00 | 23 | 0.0 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | -0.00 | 46 | -0.0 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -0.00 | 575 | -0.0 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 0.00 | 23 | 0.0 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | 0.00 | 23 | 0.0 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | 0.00 | 1.7 | 0.0 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | 0.00 | 1 | 0.0 |

**Hum at the speaker, idle, standard build:** 27.2 uV rms (-111.0 dB re full power) = 0.0 uV from the charging pulses + 27.2 uV from the pre-filter's ripple current returning through the planes; 5.052 uV A-weighted = -18.0 dBA SPL at 1 m; largest share: tank return -> recovery source (pre-filter ripple current).

**Same with C_s1 / C_s2 fitted (25x more preamp gain):** 76.1 uV rms (-102.1 dB re full power) = 0.0 uV from the charging pulses + 76.1 uV from the pre-filter's ripple current returning through the planes; 14.133 uV A-weighted = -9.0 dBA SPL at 1 m; largest share: input jack sleeve -> Q1 source (pre-filter ripple current).

## speaker: loudspeaker return, positive half-cycle (supply -> IC -> speaker -> reservoir)

LS1.2 -> C_main.2: 59.8 mm apart in the copper, 47.748 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | -0.00 | 210 | -0.0 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | -0.00 | 63 | -0.0 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | -0.00 | 19 | -0.0 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 0.00 | 23 | 0.0 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | -0.00 | 46 | -0.0 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -0.00 | 575 | -0.0 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 0.00 | 23 | 0.0 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | 0.00 | 23 | 0.0 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | 0.00 | 1.7 | 0.0 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | -13165.58 | 1 | -13165.6 |

**Loop gain closed through the ground copper, standard build:** none -- this current does not enter the planes.

**Same with C_s1 / C_s2 fitted:** none -- this current does not enter the planes.

Series resistance this return adds to the speaker circuit: 13.17 mohm.

## speaker-IC: loudspeaker return, negative half-cycle (C_out -> IC ground pin -> speaker)

LS1.2 -> IC_PA.3: 91.0 mm apart in the copper, 74.013 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | -0.00 | 210 | -0.0 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | -0.00 | 63 | -0.0 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | -0.00 | 19 | -0.0 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 0.00 | 23 | 0.0 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | -0.00 | 46 | -0.0 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -0.00 | 575 | -0.0 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 0.00 | 23 | 0.0 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | 0.00 | 23 | 0.0 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | 0.00 | 1.7 | 0.0 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | -13165.58 | 1 | -13165.6 |

**Loop gain closed through the ground copper, standard build:** none -- this current does not enter the planes.

**Same with C_s1 / C_s2 fitted:** none -- this current does not enter the planes.

Series resistance this return adds to the speaker circuit: 13.17 mohm.

## prefilter: ripple current of the 100 R / 2000 uF pre-filter

C_filt1.2 -> C_main.2: 16.6 mm apart in the copper, 57.254 mohm between the two pads.

| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |
|---|---|---:|---:|---:|
| input jack sleeve -> Q1 source | J_IN1.2 -> R_s1.2 | -24.66 | 210 | -5178.4 |
| Q1 drain rail reference -> Q2 source | C_pre.2 -> R_s2.2 | 114.36 | 63 | 7204.9 |
| Q2 drain rail reference -> tone ref | C_pre.2 -> C_vb3.2 | 118.65 | 19 | 2254.3 |
| tone reference -> volume pot ground | C_vb3.2 -> POT_VOL.1 | 34.24 | 23 | 787.5 |
| volume pot ground -> mixer reference | POT_VOL.1 -> C_vbr.2 | -21.14 | 46 | -972.5 |
| tank return -> recovery source | REV1.4 -> C_rec_byp.2 | -146.99 | 575 | -84518.1 |
| recovery rail reference -> reverb pot | C_pre.2 -> POT_REV.1 | 332.90 | 23 | 7656.6 |
| mixer reference -> PA feedback ground | C_vbr.2 -> C_gain.2 | -75.11 | 23 | -1727.5 |
| PA bias reference -> feedback ground | C_bref.2 -> C_gain.2 | 15.95 | 1.7 | 27.1 |
| PA feedback ground -> speaker return | C_gain.2 -> LS1.2 | 21315.32 | 1 | 21315.3 |

## LM1875 support parts: distance from the IC pins (mm)

The data sheet: keep the output compensation and the 0.1 uF supply decoupling as close as possible to the LM1875.

- C_byp1 (100 nF) to pin 5: 24.8
- C_byp1 ground to pin 3: 20.9
- C_byp2 (10 uF) to pin 5: 29.6
- R_zobel to pin 4: 25.2
- C_zobel ground to pin 3: 20.0
- C_lp to pin 1: 55.0
- R_fb to pin 2: 59.9
- R_gain to pin 2: 64.5
