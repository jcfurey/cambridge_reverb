### Crosstalk screen — `cambridge_reverb_smd.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `PA_OUT` | `PA_BIAS` (PA +in) | 0.01 | 2.4 | 5000 Hz | 32.1 | -90 | -82 |
| `TANK_IN` | `WET` (reverb level wiper) | 0.00 | 2.5 | 5000 Hz | 5.2 | -95 |  |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.01 | 6.0 | 5000 Hz | 3.2 | -102 | -129 |
| `PA_OUT` | `PA_IN` (PA input (22k||22k)) | 0.00 | 2.4 | 5000 Hz | 5.6 | -105 | -98 |
| `+33V5` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.01 | 11.4 | 150 Hz | 0.1 | -141 |  |
| `+33V5` | `PA_BIAS` (PA +in) | 0.01 | 3.4 | 150 Hz | 0.0 | -154 |  |
| `+33V5` | `PA_INV` (PA -in (1k||22k)) | 0.00 | 0.9 | 150 Hz | 0.0 | -186 |  |

Worst feedback loop: `PA_OUT` → `PA_BIAS`: loop gain **-82 dB** (forward 27 dB + coupling -110 dB); stable with margin if well below 0 dB.
