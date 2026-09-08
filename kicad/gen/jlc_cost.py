#!/usr/bin/env python3
"""JLCPCB fab + economic-assembly cost model for the mixed SMD/THT board, from the
generated BOM / position files. Prices are JLCPCB's PUBLISHED rates as of 2026 (verify
on a live quote -- they change): PCBA setup $8.00, stencil $1.50, $0.0016 per solder
joint (5 boards), "extended" (non-basic-library) part types $3.00 each per order;
2-layer 1 oz HASL PCB at 155x90 mm ~ $2 + area surcharge (the 100x100 mm $2 tier is not
reachable at 54 % packing). The point is not the exact dollars but WHICH knobs move them:
part-TYPE count (extended fees) and joint count (linear), not board area.

    python3 kicad/gen/jlc_cost.py [--boards 5]
"""
import csv, argparse, os, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BOM = os.path.join(ROOT, "production", "smd", "bom-jlcpcb.csv")
JOINTS = {"R_0805": 2, "R_1206": 2, "C_1206": 2, "C_1210": 2, "D_SMA": 2, "D_SOD-123": 2, "SOT-23": 3}
# footprints whose typical JLC library part is BASIC (no $3 loading fee): 0805 1 % resistors
# of E24 values, 1206 X7R/C0G caps of common values, SOD-123 1N4148W, SMA S1M. Everything
# else (1210 caps, E96 resistor values, SOT-23 JFETs, odd cap values) is EXTENDED.
BASIC_R_E24 = {"10R","100R","180R","240R","470R","1k","1.5k","2.2k","3.3k","4.7k","5.1k","6.8k","10k","15k","22k","33k","47k","68k",
               "100k","150k","180k","220k","330k","470k","1M"}
BASIC_C = {"100pF","470pF","1nF","2.2nF","4.7nF","10nF","22nF","47nF","100nF","1uF"}
def joints_for(fp):
    for k, n in JOINTS.items():
        if fp.startswith(k): return n
    return 2
def is_basic(comment, fp):
    if fp.startswith("R_0805"): return comment in BASIC_R_E24
    if fp.startswith("C_1206"): return comment.split("/")[0].split(" ")[0] in BASIC_C
    if fp.startswith("D_SOD-123") and "4148" in comment: return True
    if fp.startswith("D_SMA") and ("4007" in comment or "S1M" in comment): return True
    if fp.startswith("SOT-23") and "3904" in comment: return True      # MMBT3904: basic
    return False
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--boards", type=int, default=5); a = ap.parse_args()
    rows = list(csv.DictReader(open(BOM)))
    parts = joints = 0; ext = []; basic = []
    for r in rows:
        refs = [x for x in r["Designator"].split(",") if x]
        parts += len(refs); joints += len(refs) * joints_for(r["Footprint"])
        (basic if is_basic(r["Comment"], r["Footprint"]) else ext).append((r["Comment"], r["Footprint"], len(refs)))
    n = a.boards
    setup, stencil, per_joint, ext_fee = 8.0, 1.5, 0.0016, 3.0
    asm = setup + stencil + per_joint * joints * n + ext_fee * len(ext)
    print(f"SMD parts {parts} in {len(rows)} lines -> {joints} solder joints per board, {n} boards")
    print(f"  basic-library lines: {len(basic)}   extended lines: {len(ext)} (${ext_fee:.0f} each per order)")
    for c, f, q in ext: print(f"    extended: {c:14s} {f:22s} x{q}")
    print(f"  assembly estimate: setup ${setup:.2f} + stencil ${stencil:.2f} + joints {joints}x{n}x${per_joint} = ${per_joint*joints*n:.2f}"
          f" + extended {len(ext)}x${ext_fee:.0f} = ${ext_fee*len(ext):.2f}  ->  ${asm:.2f} for {n} boards (${asm/n:.2f} each)")
    print(f"  per-board sensitivity: one more part TYPE (extended) = ${ext_fee/n:.2f}/board; one more 2-pad part = ${2*per_joint:.4f}/board")
    print("  PCB (4-layer JLC04161H-7628, 1 oz outer / 0.5 oz inner, HASL LF, green, 1.6 mm): the 100x100 mm 4-layer tier is ~$7/5 pcs;"
          " 155x90 and 190x115 are area-priced above it (expect roughly $30-60 per five, get a live quote)."
          " Both boards use >= 0.3/0.45 mm vias and >= 0.25 mm tracks -> no via/track surcharges; inner-layer clearances are >= 0.2 mm.")
if __name__ == "__main__":
    main()
