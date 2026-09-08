# JLCPCB assembly inputs — mixed SMD/THT variant (`kicad/smd/`)

Generated; do not hand-edit. Regenerate after any schematic/placement change:

```
python3 kicad/gen/gen_bom.py --profile smd --jlc
kicad-cli pcb export pos --side front --format csv --units mm --smd-only --exclude-dnp \
    -o production/smd/cambridge_reverb_smd-top-pos.csv kicad/smd/cambridge_reverb_smd.kicad_pcb
```

| File | What |
|------|------|
| `bom-jlcpcb.csv` | JLCPCB BOM format (Comment, Designator, Footprint, LCSC Part #) for the **91 placed SMD parts** (29 lines; the two "(opt)" MRB caps are DNP and excluded). The LCSC column is empty on purpose: pick "basic" parts in the JLC parts picker (0805 1 % resistors, 1206 X7R/C0G, S1M, MMBT3904) — only the MMBF5457 and the 3.09 k E96 resistor are unavoidably "extended" ($3/type). `kicad/gen/jlc_cost.py` prints the cost model. |
| `cambridge_reverb_smd-top-pos.csv` | kicad-cli position (CPL) file, top side, SMD only, mm, DNP excluded; includes the three fiducials `FID1–3` (1 mm copper / 2 mm mask) for the placement camera. JLC expects the header names `Designator,Mid X,Mid Y,Layer,Rotation`; rename the columns (Ref→Designator, PosX→Mid X, PosY→Mid Y, Side→Layer, Rot→Rotation) when uploading, or use the "KiCad" template in their uploader. Check SOT-23 / diode rotations in their preview — KiCad's 0° and JLC's 0° differ for some packages. |

The board is **4-layer** (errata #24: In1 GND plane, In2 inner signal layer) — order the JLC04161H-7628 stackup and include `In1.Cu` / `In2.Cu` in the Gerbers. The ~80 through-hole parts (power devices, electrolytics, socketed op-amps, the
trimmed JFET source resistors, connectors, test points, vactrol, toroid, fuse
clip) are hand-soldered afterwards; see `bom/bom-smd.csv` for the full list.
