### Crosstalk screen — `cambridge_reverb_smd.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `R_DRVO` | `SUMJ` (summer virtual ground: coupled charge x R_fb -> BLEND (1 V)) | 0.01 | 1.0 | 5000 Hz | 62.3 | -84 |  |
| `R_DRVO` | `QRD` (recovery drain) | 0.02 | 3.3 | 5000 Hz | 16.1 | -85 |  |
| `TANK_IN` | `TANK_OUT` (tank return (recovery gate)) | 0.00 | 1.3 | 5000 Hz | 0.8 | -87 |  |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.03 | 4.8 | 5000 Hz | 10.0 | -92 | -119 |
| `R_DRVO` | `TONE_OUT` (volume wiper) | 0.00 | 1.0 | 5000 Hz | 1.8 | -115 |  |
| `+33V5` | `PA_BIAS` (PA +in) | 0.01 | 6.0 | 150 Hz | 0.0 | -151 |  |

Worst feedback loop: `PA_OUT` → `PA_INV`: loop gain **-119 dB** (forward 0 dB + coupling -120 dB); stable with margin if well below 0 dB.
