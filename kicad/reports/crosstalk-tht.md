### Crosstalk screen — `cambridge_reverb.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `TANK_IN` | `TANK_OUT` (tank return (recovery gate)) | 0.01 | 3.6 | 5000 Hz | 9.6 | -66 |  |
| `PA_OUT` | `PA_BIAS` (PA +in) | 0.02 | 7.5 | 5000 Hz | 61.0 | -84 | -77 |
| `ZOB` | `PA_INV` (PA -in (1k||22k)) | 0.00 | 2.2 | 5000 Hz | 1.1 | -111 | -139 |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.00 | 1.9 | 5000 Hz | 0.7 | -115 | -143 |

Worst feedback loop: `PA_OUT` → `PA_BIAS`: loop gain **-77 dB** (forward 27 dB + coupling -104 dB); stable with margin if well below 0 dB.
