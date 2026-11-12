### Crosstalk screen — `cambridge_reverb_smd.kicad_pcb` (4-layer, h = 0.21 mm)

| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |
|---|---|---:|---:|---:|---:|---:|---:|
| `TANK_IN` | `TANK_OUT` (tank return (recovery gate)) | 0.00 | 7.9 | 5000 Hz | 3.8 | -75 |  |
| `TANK_IN` | `OBUF_IN` (output buffer +in) | 0.01 | 1.6 | 5000 Hz | 70.8 | -83 |  |
| `TANK_IN` | `WET` (reverb level wiper) | 0.00 | 4.4 | 5000 Hz | 14.6 | -86 |  |
| `TANK_IN` | `MRB_T` (MRB tank node) | 0.01 | 1.7 | 5000 Hz | 32.8 | -90 |  |
| `R_DRVO` | `TONE_OUT` (volume wiper) | 0.01 | 7.6 | 5000 Hz | 30.9 | -90 |  |
| `R_DRVO` | `QRD` (recovery drain) | 0.01 | 4.7 | 5000 Hz | 9.1 | -90 |  |
| `TANK_IN` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.00 | 2.2 | 5000 Hz | 17.9 | -95 |  |
| `TKDRV` | `FS_MRB` (MRB tank return (footswitch line; floats on the tank when open)) | 0.00 | 2.3 | 5000 Hz | 17.4 | -95 |  |
| `TANK_IN` | `FS_REV` (recovery output / top of the reverb pot (footswitch line)) | 0.01 | 4.4 | 5000 Hz | 4.8 | -96 |  |
| `ZOB` | `PA_INV` (PA -in (1k||22k)) | 0.01 | 2.3 | 5000 Hz | 1.9 | -107 | -134 |
| `TANK_IN` | `TREM_S` (LDR node) | 0.00 | 2.1 | 5000 Hz | 4.1 | -108 |  |
| `TANK_IN` | `TREM_OUT` (tremolo shunt node) | 0.00 | 2.6 | 5000 Hz | 3.7 | -109 |  |
| `PA_OUT` | `PA_INV` (PA -in (1k||22k)) | 0.00 | 1.1 | 5000 Hz | 0.3 | -124 | -151 |

Worst feedback loop: `ZOB` → `PA_INV`: loop gain **-134 dB** (forward 0 dB + coupling -134 dB); stable with margin if well below 0 dB.
