### Crosstalk screen — `cambridge_reverb.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `R_DRVO` | `SUMJ` (summer virtual ground: coupled charge x R_fb -> BLEND (1 V)) | 0.01 | 3.9 | 5000 Hz | 74.2 | -83 |  |
| `TANK_IN` | `TANK_OUT` (tank return (recovery gate)) | 0.00 | 3.5 | 5000 Hz | 1.2 | -84 |  |
| `R_DRVO` | `TANK_OUT` (tank return (recovery gate)) | 0.00 | 1.9 | 5000 Hz | 0.7 | -90 |  |
| `PA_OUT` | `PA_BIAS` (PA +in) | 0.01 | 2.4 | 5000 Hz | 31.8 | -90 | -82 |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.01 | 5.2 | 5000 Hz | 4.2 | -100 | -127 |
| `R_DRVO` | `QRD` (recovery drain) | 0.00 | 1.5 | 5000 Hz | 1.0 | -110 |  |
| `R_DRVO` | `FS_REV` (recovery output / top of the reverb pot (footswitch line)) | 0.00 | 1.9 | 5000 Hz | 1.0 | -110 |  |
| `TKDRV` | `QRD` (recovery drain) | 0.00 | 1.2 | 5000 Hz | 0.5 | -115 |  |
| `+33V5` | `PA_BIAS` (PA +in) | 0.02 | 5.4 | 150 Hz | 0.1 | -144 |  |

Worst feedback loop: `PA_OUT` → `PA_BIAS`: loop gain **-82 dB** (forward 27 dB + coupling -110 dB); stable with margin if well below 0 dB.
