# JLCPCB assembly inputs — mixed SMD/THT variant (`kicad/smd/`)

Generated; do not hand-edit. Regenerate after any schematic/placement change:

```
python3 kicad/gen/gen_bom.py --profile smd --jlc
kicad-cli pcb export pos --side front --format csv --units mm --smd-only --exclude-dnp \
    -o production/smd/cambridge_reverb_smd-top-pos.csv kicad/smd/cambridge_reverb_smd.kicad_pcb
```

| File | What |
|------|------|
| `bom-jlcpcb.csv` | JLCPCB BOM format (Comment, Designator, Footprint, LCSC Part #) for the **90 SMD parts only**. The LCSC column is empty on purpose: pick "basic" parts in the JLC parts picker (0805 1 % resistors, 1206/1210 X7R/C0G, S1M, 1N4148W, MMBF5457) — no part numbers were invented here. |
| `cambridge_reverb_smd-top-pos.csv` | kicad-cli position (CPL) file, top side, SMD only, mm. JLC expects the header names `Designator,Mid X,Mid Y,Layer,Rotation`; rename the columns (Ref→Designator, PosX→Mid X, PosY→Mid Y, Side→Layer, Rot→Rotation) when uploading, or use the "KiCad" template in their uploader. Check SOT-23 / diode rotations in their preview — KiCad's 0° and JLC's 0° differ for some packages. |

The ~76 through-hole parts (power devices, electrolytics, socketed op-amps, the
trimmed JFET source resistors, connectors, test points, vactrol, toroid, fuse
clip) are hand-soldered afterwards; see `bom/bom-smd.csv` for the full list.
