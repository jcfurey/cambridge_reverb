#!/usr/bin/env python3
"""JLCPCB economic-assembly cost model for the mixed SMD/THT board, from the generated
assembly BOM (production/smd/bom-jlcpcb.csv: every line carries its JLCPCB library class,
looked up live -- see jlc_parts.py).

Fees: JLCPCB's price page as last updated 2026-10-22 (jlcpcb.com/help/article/pcb-assembly-price,
read 2026-11-12): Economic PCBA setup $8.18, stencil $1.53, $0.0016 per SMT joint, feeder
loading $3.07 per EXTENDED part type per order. Basic parts carry no loading fee; JLCPCB's
assembly pages say the same for "preferred" extended parts on Economic PCBA -- the price
table itself does not list them, so the worst case (preferred charged as extended) is
printed too. Part prices: jlc_parts.PRICE (1-piece tier on the snapshot date).

The point is not the exact dollars but WHICH knobs move them: the number of extended
part TYPES, not the part count and not the board area.

    python3 kicad/gen/jlc_cost.py [--boards 5]
"""
import csv, argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jlc_parts
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BOM = os.path.join(ROOT, "production", "smd", "bom-jlcpcb.csv")
JOINTS = {"0805": 2, "1206": 2, "SMA": 2, "SOT-23": 3}
SETUP, STENCIL, PER_JOINT, EXT_FEE = 8.18, 1.53, 0.0016, 3.07

def model(boards=5, bom=BOM):
    rows = list(csv.DictReader(open(bom)))
    parts = joints = 0; cost = 0.0; by = {"basic": [], "preferred": [], "extended": []}
    for r in rows:
        n = len([x for x in r["Designator"].split(",") if x])
        parts += n; joints += n * JOINTS[r["Footprint"]]
        cost += n * jlc_parts.PRICE.get(r["LCSC Part #"], 0.0)
        by[r["JLCPCB class"]].append((r["Comment"], r["LCSC Part #"], n))
    ext = by["extended"]
    fees = SETUP + STENCIL + PER_JOINT * joints * boards + EXT_FEE * len(ext)
    return dict(lines=len(rows), parts=parts, joints=joints, by=by, fees=fees, parts_per_board=cost,
                total=fees + cost * boards, worst=fees + cost * boards + EXT_FEE * len(by["preferred"]))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--boards", type=int, default=5); a = ap.parse_args()
    m = model(a.boards); n = a.boards; by = m["by"]; ext = by["extended"]
    print(f"SMD parts {m['parts']} in {m['lines']} lines -> {m['joints']} solder joints per board, {n} boards")
    print(f"  basic lines: {len(by['basic'])}   preferred-extended (no fee): {len(by['preferred'])}   extended: {len(ext)} (${EXT_FEE:.2f} each per order)")
    for c, l, q in ext: print(f"    extended: {c:28s} {l:9s} x{q}")
    print(f"  assembly fees: setup ${SETUP:.2f} + stencil ${STENCIL:.2f} + joints {m['joints']}x{n}x${PER_JOINT} = ${PER_JOINT * m['joints'] * n:.2f}"
          f" + extended {len(ext)}x${EXT_FEE:.2f} = ${EXT_FEE * len(ext):.2f}  ->  ${m['fees']:.2f} for {n} boards")
    print(f"  parts: ${m['parts_per_board']:.2f} per board (${m['parts_per_board'] * n:.2f} for {n})")
    print(f"  assembly + parts: ${m['total']:.2f} for {n} boards (${m['total'] / n:.2f} each); if the {len(by['preferred'])} preferred lines were charged as extended: ${m['worst']:.2f}")
    print(f"  what is left as extended has no basic equivalent in any package: the 22 nF and 100 nF C0G (signal-path"
          f" coupling, tone stack, MRB tank, PA input filter) and the JFET. Replacing the two C0G lines with basic X7R would"
          f" save ${2 * EXT_FEE:.2f} per order and put microphonic, voltage-dependent capacitors on the high-impedance nodes of a combo amplifier.")
    print("  PCB (4-layer JLC04161H-7628, 1.6 mm, 1 oz outer / 0.5 oz inner, HASL lead-free): 170 x 105 mm is area-priced above the"
          " 100 x 100 mm tier -- expect roughly $35-60 for five; get a live quote. Smallest track 0.3 mm, vias 0.8 / 0.4 mm: no surcharges.")
if __name__ == "__main__":
    main()
