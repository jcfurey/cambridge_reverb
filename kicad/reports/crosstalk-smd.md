### Crosstalk screen — `cambridge_reverb_smd.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `R_DRVO` | `TANK_OUT` (tank return (recovery gate)) | 0.02 | 12.6 | 5000 Hz | 18.0 | -61 |  |
| `R_DRVO` | `DRVP` (tank driver +in) | 0.04 | 11.8 | 5000 Hz | 342.6 | -69 |  |
| `R_DRVO` | `QRG` (recovery JFET gate) | 0.01 | 2.8 | 5000 Hz | 6.0 | -70 |  |
| `R_DRVO` | `QRD` (recovery drain) | 0.05 | 4.6 | 5000 Hz | 51.4 | -75 |  |
| `TANK_IN` | `QRG` (recovery JFET gate) | 0.00 | 2.8 | 5000 Hz | 3.3 | -76 |  |
| `R_DRVO` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.03 | 8.6 | 5000 Hz | 124.9 | -78 |  |
| `TANK_IN` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.02 | 7.1 | 5000 Hz | 74.3 | -83 |  |
| `R_DRVO` | `TONE_OUT` (volume wiper) | 0.01 | 11.6 | 5000 Hz | 62.1 | -84 |  |
| `TKDRV` | `QRD` (recovery drain) | 0.01 | 4.1 | 5000 Hz | 9.3 | -90 |  |
| `R_DRVO` | `TREM_OUT` (tremolo shunt node) | 0.03 | 14.2 | 5000 Hz | 23.8 | -92 |  |
| `TANK_IN` | `QRD` (recovery drain) | 0.01 | 0.8 | 5000 Hz | 4.8 | -96 |  |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.01 | 6.0 | 5000 Hz | 3.2 | -102 | -129 |
| `+33V5` | `PA_INV` (PA -in (1k||22k)) | 0.03 | 1.8 | 150 Hz | 0.0 | -156 |  |

Worst feedback loop: `PA_OUT` → `PA_INV`: loop gain **-129 dB** (forward 0 dB + coupling -130 dB); stable with margin if well below 0 dB.
