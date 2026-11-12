### Crosstalk screen — `cambridge_reverb.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `TKDRV` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.03 | 10.0 | 5000 Hz | 130.3 | -78 |  |
| `TANK_IN` | `WET` (reverb level wiper) | 0.01 | 8.7 | 5000 Hz | 24.3 | -82 |  |
| `TKDRV` | `SUMJ` (summer virtual ground: coupled charge x R_fb -> BLEND (1 V)) | 0.01 | 10.0 | 5000 Hz | 67.2 | -83 |  |
| `SPK_P` | `PA_IN` (PA input (22k||22k)) | 0.01 | 9.3 | 5000 Hz | 44.6 | -87 | -80 |
| `PA_OUT` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.00 | 2.5 | 5000 Hz | 39.8 | -88 | -81 |
| `TANK_IN` | `SUMJ` (summer virtual ground: coupled charge x R_fb -> BLEND (1 V)) | 0.00 | 2.1 | 5000 Hz | 35.1 | -89 |  |
| `TKDRV` | `TANK_OUT` (tank return (recovery gate)) | 0.00 | 0.6 | 5000 Hz | 0.3 | -96 |  |
| `PA_OUT` | `PA_BIAS` (PA +in) | 0.00 | 1.2 | 5000 Hz | 14.6 | -97 | -89 |
| `R_DRVO` | `QRD` (recovery drain) | 0.00 | 1.9 | 5000 Hz | 2.9 | -100 |  |
| `TKDRV` | `TONE_OUT` (volume wiper) | 0.00 | 0.9 | 5000 Hz | 3.8 | -108 |  |
| `ZOB` | `PA_INV` (PA -in (1k||22k)) | 0.00 | 1.7 | 5000 Hz | 1.2 | -111 | -138 |
| `R_DRVO` | `JA` (bass ladder) | 0.00 | 0.6 | 5000 Hz | 2.2 | -123 |  |
| `+33V5` | `PA_BIAS` (PA +in) | 0.00 | 2.1 | 150 Hz | 0.0 | -163 |  |

Worst feedback loop: `SPK_P` → `PA_IN`: loop gain **-80 dB** (forward 27 dB + coupling -107 dB); stable with margin if well below 0 dB.
