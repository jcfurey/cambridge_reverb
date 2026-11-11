#!/usr/bin/env python3
"""Build the JLCPCB order package for the mixed SMD/THT board from the ROUTED board:

    production/smd/cambridge_reverb_smd-gerbers.zip   Gerbers (4 copper layers, mask, paste,
                                                      silk, outline) + Excellon drill files
    production/smd/cambridge_reverb_smd-cpl.csv       pick-and-place file in JLCPCB's format
                                                      (Designator, Mid X, Mid Y, Layer, Rotation)
    production/smd/bom-jlcpcb.csv                     assembly BOM with LCSC part numbers (gen_bom.py)
    production/smd/cambridge_reverb_smd-assembly.pdf  assembly drawing (fab outlines + references)
    production/smd/cambridge_reverb_smd-top.svg       top-side preview (copper, mask, silk)

    python3 kicad/gen/fab_jlcpcb.py            # refuses a board that is not DRC-clean and fully routed

Rotation: KiCad's position file gives each footprint's own angle; JLCPCB's library draws
some packages rotated against KiCad's zero. The corrections below are the widely used
ones (same table as the kicad-jlcpcb-tools plugin): SOT-23 +180 deg, two-pin chips and
SMA / SOD diodes 0. JLCPCB shows every placement with its pin-1 / cathode mark before
you pay -- look at D1, D2, Q1, Q2, Q_rec and Q_trem there.
"""
import sys, os, csv, re, json, zipfile, subprocess, shutil, tempfile, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PCB = os.path.join(ROOT, "kicad", "smd", "cambridge_reverb_smd.kicad_pcb")
OUT = os.path.join(ROOT, "production", "smd")
NAME = "cambridge_reverb_smd"
LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu", "F.Paste", "B.Paste", "F.SilkS", "B.SilkS", "F.Mask", "B.Mask", "Edge.Cuts"]
# package-name pattern -> degrees added to KiCad's rotation for JLCPCB's CPL
ROTATION_FIX = [(r"^SOT-23", 180), (r"^(R|C)_\d{4}_", 0), (r"^D_SMA", 0), (r"^D_SOD-123", 0)]

def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        sys.exit("FAILED: " + " ".join(cmd) + "\n" + r.stdout[-2000:])
    return r.stdout

def drc_gate(pcb):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f: tmp = f.name
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", tmp, pcb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(tmp)); os.remove(tmp)
    errs = [v for v in d.get("violations", []) if v["severity"] == "error"]
    return len(d.get("unconnected_items", [])), len(errs), len(d.get("violations", [])) - len(errs)

def rotation_fix(package):
    for pat, deg in ROTATION_FIX:
        if re.search(pat, package):
            return deg
    raise SystemExit(f"no JLCPCB rotation rule for package {package!r}: add it to ROTATION_FIX after checking JLCPCB's library")

def cpl(pcb, out_csv):
    """kicad-cli position file (top, SMD, DNP excluded) -> JLCPCB CPL."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f: tmp = f.name
    run(["kicad-cli", "pcb", "export", "pos", "--side", "front", "--format", "csv", "--units", "mm",
         "--smd-only", "--exclude-dnp", "-o", tmp, pcb])
    rows = list(csv.DictReader(open(tmp))); os.remove(tmp)
    out = []
    for r in rows:
        if r["Ref"].startswith("FID"):                 # fiducials are copper, not parts
            continue
        rot = (float(r["Rot"]) + rotation_fix(r["Package"])) % 360
        out.append([r["Ref"], f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", "Top", f"{rot:g}"])
    out.sort(key=lambda r: r[0])
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]); w.writerows(out)
    return out

def gerbers(pcb, zip_path):
    tmp = tempfile.mkdtemp(prefix="gerb_")
    run(["kicad-cli", "pcb", "export", "gerbers", "-o", tmp + "/", "--layers", ",".join(LAYERS),
         "--no-x2", "--no-netlist", "--subtract-soldermask", pcb])
    run(["kicad-cli", "pcb", "export", "drill", "-o", tmp + "/", "--format", "excellon", "--drill-origin", "absolute",
         "--excellon-separate-th", "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
         "--excellon-oval-format", "alternate", pcb])
    files = sorted(f for f in os.listdir(tmp) if not f.endswith(".gbrjob"))
    if os.path.exists(zip_path): os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(tmp, f), f)
    info = {}
    for f in files:
        txt = open(os.path.join(tmp, f), errors="replace").read()
        if f.endswith(".drl"):
            info[f] = len(re.findall(r"^X-?[\d.]+Y-?[\d.]+", txt, re.M))           # drill hits (slots count once per end)
        else:
            info[f] = len(re.findall(r"D0[123]\*", txt))                            # draw / move / flash operations
    shutil.rmtree(tmp)
    return files, info

def board_facts(pcb):
    import pcbnew
    b = pcbnew.LoadBoard(pcb)
    bb = b.GetBoardEdgesBoundingBox()
    pth = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)
    npth = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH)
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    return dict(w=pcbnew.ToMM(bb.GetWidth()), h=pcbnew.ToMM(bb.GetHeight()), x0=pcbnew.ToMM(bb.GetLeft()), y0=pcbnew.ToMM(bb.GetTop()),
                layers=b.GetCopperLayerCount(), pth=pth, npth=npth, vias=len(vias),
                min_via_drill=min(pcbnew.ToMM(v.GetDrill()) for v in vias), min_via_dia=min(pcbnew.ToMM(v.GetWidth()) for v in vias),
                min_track=min(pcbnew.ToMM(t.GetWidth()) for t in segs),
                min_hole=min(pcbnew.ToMM(min(p.GetDrillSize().x, p.GetDrillSize().y)) for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0))

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--allow-dirty", action="store_true", help="export even if the board has open connections / DRC errors (NOT orderable)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    unconn, errs, warns = drc_gate(PCB)
    print(f"DRC gate: {unconn} unconnected, {errs} errors, {warns} warnings")
    if (unconn or errs) and not a.allow_dirty:
        sys.exit("board is not orderable: route it (route_board.py + finish_routes.py) and clear the DRC first")
    facts = board_facts(PCB)
    files, info = gerbers(PCB, os.path.join(OUT, NAME + "-gerbers.zip"))
    rows = cpl(PCB, os.path.join(OUT, NAME + "-cpl.csv"))
    run(["kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(OUT, NAME + "-assembly.pdf"),
         "--layers", "F.Fab,F.SilkS,Edge.Cuts", "--black-and-white", PCB])
    run(["kicad-cli", "pcb", "export", "svg", "-o", os.path.join(OUT, NAME + "-top.svg"),
         "--layers", "F.Cu,F.Mask,F.SilkS,Edge.Cuts", "--exclude-drawing-sheet", "--page-size-mode", "2", PCB])
    # ---- consistency: BOM <-> CPL, positions on the board, drill counts
    bom = list(csv.DictReader(open(os.path.join(OUT, "bom-jlcpcb.csv"))))
    bom_refs = {r for row in bom for r in row["Designator"].split(",")}
    cpl_refs = {r[0] for r in rows}
    problems = []
    if bom_refs != cpl_refs:
        problems.append(f"BOM / CPL mismatch: only in BOM {sorted(bom_refs - cpl_refs)}, only in CPL {sorted(cpl_refs - bom_refs)}")
    if any(not row["LCSC Part #"].startswith("C") for row in bom):
        problems.append("BOM line without an LCSC part number")
    for ref, x, y, _, _ in rows:
        xx, yy = float(x[:-2]), -float(y[:-2])
        if not (facts["x0"] + 2 <= xx <= facts["x0"] + facts["w"] - 2 and facts["y0"] + 2 <= yy <= facts["y0"] + facts["h"] - 2):
            problems.append(f"{ref} at ({xx:.1f}, {yy:.1f}) is outside the board or within 2 mm of its edge")
    pth = next(n for f, n in info.items() if f.endswith("-PTH.drl")); npth = next(n for f, n in info.items() if f.endswith("-NPTH.drl"))
    if pth != facts["pth"] + facts["vias"]:
        problems.append(f"PTH drill file has {pth} hits, board has {facts['pth']} plated pads + {facts['vias']} vias")
    if npth != facts["npth"]:
        problems.append(f"NPTH drill file has {npth} hits, board has {facts['npth']} unplated holes")
    need = {"-F_Cu.gtl", "-In1_Cu.g2", "-In2_Cu.g3", "-B_Cu.gbl", "-F_Paste.gtp", "-B_Paste.gbp", "-F_Silkscreen.gto",
            "-B_Silkscreen.gbo", "-F_Mask.gts", "-B_Mask.gbs", "-Edge_Cuts.gm1", "-PTH.drl", "-NPTH.drl"}
    have = {f[len(NAME):] for f in files}
    if need - have:
        problems.append(f"package is missing {sorted(need - have)} (has {sorted(have)})")
    extra = sorted(f for f in files if f.endswith(".drl") and not f.endswith(("-PTH.drl", "-NPTH.drl")))
    if extra:
        problems.append(f"blind / buried vias on the board: extra drill file(s) {extra} -- the standard process drills through holes only")
    print(f"board {facts['w']:.0f} x {facts['h']:.0f} mm, {facts['layers']} copper layers; smallest track {facts['min_track']:.2f} mm, "
          f"via {facts['min_via_dia']:.2f}/{facts['min_via_drill']:.2f} mm, hole {facts['min_hole']:.2f} mm")
    print(f"gerber zip: {len(files)} files; drill: {pth} plated ({facts['pth']} pads + {facts['vias']} vias), {npth} unplated")
    print(f"CPL: {len(rows)} placements; BOM: {len(bom)} lines / {len(bom_refs)} parts")
    json.dump(dict(facts, gerber_files=files, placements=len(rows), bom_lines=len(bom), unconnected=unconn, drc_errors=errs),
              open(os.path.join(OUT, NAME + "-fab-summary.json"), "w"), indent=1, sort_keys=True)
    if problems:
        for p in problems: print("  PROBLEM:", p)
        sys.exit(1)
    print("package consistent -> production/smd/")

if __name__ == "__main__":
    main()
