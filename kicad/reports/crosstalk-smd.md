### Crosstalk screen — `cambridge_reverb_smd.kicad_pcb`

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `TANK_IN` | `TANK_OUT` (tank return (recovery gate)) | 0.18 | 4.6 | 5000 Hz | 166.1 | -42 |  |
| `TANK_IN` | `WET` (reverb level wiper) | 0.21 | 6.5 | 5000 Hz | 966.5 | -50 |  |
| `TANK_IN` | `SUMJ` (summer virtual ground: coupled charge x R_fb -> BLEND (1 V)) | 0.06 | 4.0 | 5000 Hz | 555.2 | -65 |  |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.43 | 7.7 | 5000 Hz | 131.8 | -70 | -97 |
| `PA_OUT` | `PA_BIAS` (PA +in) | 0.05 | 2.6 | 5000 Hz | 165.0 | -76 | -68 |
| `AC1` | `PA_IN` (PA input (22k||22k)) | 0.46 | 26.1 | 150 Hz | 115.5 | -79 |  |
| `TANK_IN` | `QRD` (recovery drain) | 0.02 | 1.7 | 5000 Hz | 20.7 | -83 |  |

Worst feedback loop: `PA_OUT` → `PA_BIAS`: loop gain **-68 dB** (forward 27 dB + coupling -95 dB); stable with margin if well below 0 dB.
