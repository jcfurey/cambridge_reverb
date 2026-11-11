### Crosstalk screen — `cambridge_reverb.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `R_DRVO` | `DRVP` (tank driver +in) | 0.02 | 7.1 | 5000 Hz | 173.2 | -75 |  |
| `R_DRVO` | `TONE_OUT` (volume wiper) | 0.02 | 6.3 | 5000 Hz | 111.7 | -79 |  |
| `TANK_IN` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.02 | 8.2 | 5000 Hz | 106.6 | -79 |  |
| `R_DRVO` | `SUMJ` (summer virtual ground: coupled charge x R_fb -> BLEND (1 V)) | 0.01 | 6.7 | 5000 Hz | 93.2 | -81 |  |
| `R_DRVO` | `QRG` (recovery JFET gate) | 0.00 | 2.5 | 5000 Hz | 1.8 | -81 |  |
| `TANK_IN` | `TANK_OUT` (tank return (recovery gate)) | 0.00 | 1.6 | 5000 Hz | 1.7 | -81 |  |
| `R_DRVO` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.02 | 1.7 | 5000 Hz | 81.8 | -82 |  |
| `R_DRVO` | `TANK_OUT` (tank return (recovery gate)) | 0.00 | 2.1 | 5000 Hz | 0.8 | -88 |  |
| `R_DRVO` | `JA` (bass ladder) | 0.01 | 1.9 | 5000 Hz | 46.6 | -96 |  |
| `R_DRVO` | `JWB` (bass wiper) | 0.00 | 1.9 | 5000 Hz | 20.2 | -97 |  |
| `R_DRVO` | `JTA` (treble ladder) | 0.00 | 1.7 | 5000 Hz | 21.4 | -103 |  |
| `R_DRVO` | `JB` (bass ladder) | 0.00 | 1.9 | 5000 Hz | 8.6 | -111 |  |
| `ZOB` | `PA_INV` (PA -in (1k||22k)) | 0.00 | 2.2 | 5000 Hz | 1.1 | -111 | -139 |
| `TKDRV` | `QRD` (recovery drain) | 0.00 | 1.2 | 5000 Hz | 0.5 | -116 |  |

Worst feedback loop: `ZOB` → `PA_INV`: loop gain **-139 dB** (forward 0 dB + coupling -139 dB); stable with margin if well below 0 dB.
