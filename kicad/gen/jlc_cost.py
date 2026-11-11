#!/usr/bin/env python3
"""JLCPCB economic-assembly cost model for the mixed SMD/THT board, from the generated
assembly BOM (production/smd/bom-jlcpcb.csv: every line carries its JLCPCB library class,
looked up live -- see jlc_parts.py). Fees are JLCPCB's PUBLISHED rates as of 2026 (verify
on a live quote -- they change): PCBA setup $8.00, stencil $1.50, $0.0016 per solder
joint, $3.00 per EXTENDED part type per order; basic and "preferred" extended parts carry
no loading fee. Part prices are small next to the fees and are left to the quote.

The point is not the exact dollars but WHICH knobs move them: the number of extended
part TYPES, not the part count and not the board area.

    python3 kicad/gen/jlc_cost.py [--boards 5]
"""
import csv, argparse, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BOM = os.path.join(ROOT, "production", "smd", "bom-jlcpcb.csv")
JOINTS = {"0805": 2, "1206": 2, "SMA": 2, "SOT-23": 3}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--boards", type=int, default=5); a = ap.parse_args()
    rows = list(csv.DictReader(open(BOM)))
    parts = joints = 0; by = {"basic": [], "preferred": [], "extended": []}
    for r in rows:
        n = len([x for x in r["Designator"].split(",") if x])
        parts += n; joints += n * JOINTS[r["Footprint"]]
        by[r["JLCPCB class"]].append((r["Comment"], r["LCSC Part #"], n))
    n = a.boards; setup, stencil, per_joint, ext_fee = 8.0, 1.5, 0.0016, 3.0
    ext = by["extended"]
    asm = setup + stencil + per_joint * joints * n + ext_fee * len(ext)
    print(f"SMD parts {parts} in {len(rows)} lines -> {joints} solder joints per board, {n} boards")
    print(f"  basic lines: {len(by['basic'])}   preferred-extended (no fee): {len(by['preferred'])}   extended: {len(ext)} (${ext_fee:.0f} each per order)")
    for c, l, q in ext: print(f"    extended: {c:28s} {l:9s} x{q}")
    print(f"  assembly fees: setup ${setup:.2f} + stencil ${stencil:.2f} + joints {joints}x{n}x${per_joint} = ${per_joint*joints*n:.2f}"
          f" + extended {len(ext)}x${ext_fee:.0f} = ${ext_fee*len(ext):.2f}  ->  ${asm:.2f} for {n} boards (${asm/n:.2f} each), parts extra")
    print(f"  where the fee goes: {len(ext) - 2} of the {len(ext)} extended lines are capacitors -- C0G in the signal path and 100 V X7R on the rail"
          f" (none of the C0G values this board needs above 100 pF is a basic part; 0603, 0805 and 1206 were checked). Swapping them for basic X7R would save ~${ext_fee * (len(ext) - 4):.0f} per"
          f" order and put microphonic, voltage-dependent capacitors on the high-impedance nodes of a combo amplifier.")
    print("  PCB (4-layer JLC04161H-7628, 1.6 mm, 1 oz outer / 0.5 oz inner, HASL lead-free): 170 x 105 mm is area-priced above the"
          " 100 x 100 mm tier -- expect roughly $35-60 for five; get a live quote. Smallest track 0.3 mm, vias 0.8 / 0.4 mm: no surcharges.")
if __name__ == "__main__":
    main()
