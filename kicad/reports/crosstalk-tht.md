### Crosstalk screen — `cambridge_reverb.kicad_pcb`

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `TANK_IN` | `TANK_OUT` (tank return (recovery gate)) | 0.07 | 1.9 | 5000 Hz | 62.6 | -50 |  |
| `TANK_IN` | `SUMJ` (summer virtual ground: coupled charge x R_fb -> BLEND (1 V)) | 0.19 | 13.8 | 5000 Hz | 1800.3 | -55 |  |
| `TANK_IN` | `JB` (bass ladder) | 0.51 | 29.2 | 5000 Hz | 2409.9 | -62 |  |
| `TANK_IN` | `DRVP` (tank driver +in) | 0.07 | 5.5 | 5000 Hz | 615.5 | -64 |  |
| `PA_OUT` | `PA_BIAS` (PA +in) | 0.15 | 3.6 | 5000 Hz | 495.1 | -66 | -59 |
| `TANK_IN` | `JTA` (treble ladder) | 0.23 | 29.2 | 5000 Hz | 1079.0 | -69 |  |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.24 | 7.3 | 5000 Hz | 74.6 | -75 | -102 |
| `TANK_IN` | `TONE_OUT` (volume wiper) | 0.03 | 1.3 | 5000 Hz | 147.4 | -77 |  |
| `TANK_IN` | `MID` (mid-cut node) | 0.04 | 1.3 | 5000 Hz | 37.0 | -92 |  |
| `+33V5` | `PA_BIAS` (PA +in) | 0.03 | 2.0 | 150 Hz | 0.1 | -142 |  |

Worst feedback loop: `PA_OUT` → `PA_BIAS`: loop gain **-59 dB** (forward 27 dB + coupling -86 dB); stable with margin if well below 0 dB.
