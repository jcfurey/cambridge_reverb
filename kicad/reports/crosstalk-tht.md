### Crosstalk screen — `cambridge_reverb.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `TANK_IN` | `SUMJ` (summer virtual ground: coupled charge x R_fb -> BLEND (1 V)) | 0.06 | 15.6 | 5000 Hz | 604.7 | -64 |  |
| `TANK_IN` | `FS_REV` (recovery output / top of the reverb pot (footswitch line)) | 0.04 | 26.1 | 5000 Hz | 33.8 | -79 |  |
| `TANK_IN` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.02 | 17.3 | 5000 Hz | 93.3 | -81 |  |
| `PA_OUT` | `PA_BIAS` (PA +in) | 0.02 | 7.5 | 5000 Hz | 61.0 | -84 | -77 |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.02 | 7.5 | 5000 Hz | 7.1 | -95 | -123 |

Worst feedback loop: `PA_OUT` → `PA_BIAS`: loop gain **-77 dB** (forward 27 dB + coupling -104 dB); stable with margin if well below 0 dB.
