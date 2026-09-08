### Crosstalk screen — `cambridge_reverb_smd.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `TANK_IN` | `TANK_OUT` (tank return (recovery gate)) | 0.00 | 5.7 | 5000 Hz | 4.0 | -74 |  |
| `TANK_IN` | `QRD` (recovery drain) | 0.01 | 4.8 | 5000 Hz | 13.9 | -87 |  |
| `PA_OUT` | `PA_IN` (PA input (22k||22k)) | 0.01 | 7.1 | 5000 Hz | 32.9 | -90 | -82 |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.00 | 6.0 | 5000 Hz | 1.3 | -110 | -137 |

Worst feedback loop: `PA_OUT` → `PA_IN`: loop gain **-82 dB** (forward 27 dB + coupling -109 dB); stable with margin if well below 0 dB.
