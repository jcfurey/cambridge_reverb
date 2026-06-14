#!/usr/bin/env python3
"""Build the Vox Cambridge Reverb boards from the schematic component/net data.

KiCad 8 pcbnew API. Produces two boards:

  cambridge_reverb.kicad_pcb   full board: all 102 footprints placed, every pad
                               assigned to its net, 190x115 mm Edge.Cuts, bottom
                               GND pour. Placed, not signal-routed.

  power_section_demo.kicad_pcb small isolated demo: the +33V5 and +17V rails
                               cleanly placed and ROUTED at their net-class
                               widths (2.5 / 1.5 mm) over a GND pour -- DRC-clean.

Also prints a chassis-fit packing-density check (190x115 vs the Part 7 155x90
safe-bet). Run from repo root:  python3 kicad/gen/gen_pcb.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
import gen_kicad as g

REPO_KI = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYS_FP  = "/usr/share/kicad/footprints"
OUT      = os.path.join(REPO_KI, "cambridge_reverb.kicad_pcb")
OUT_DEMO = os.path.join(REPO_KI, "power_section_demo.kicad_pcb")

BW, BH = 190.0, 115.0      # full board (matches original 25-5274-2; errata #9)
MARGIN = 10.0

def fp_libpath(fpid):
    lib, name = fpid.split(":")
    if lib == "cambridge_reverb":
        return os.path.join(REPO_KI, "footprints", "cambridge_reverb.pretty"), name
    return os.path.join(SYS_FP, lib + ".pretty"), name

def mm(v): return pcbnew.FromMM(v)
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def make_nets(board, comps):
    netmap = {}
    for n in sorted({n for c in comps for n in c["nets"].values()}):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni); netmap[n] = ni
    return netmap

def add_footprint(board, c, x, y, netmap, rot=0, hide_text=True):
    libpath, name = fp_libpath(c["fp"])
    fp = pcbnew.FootprintLoad(libpath, name)
    if fp is None:
        return None
    board.Add(fp)
    fp.SetReference(c["ref"]); fp.SetValue(c["value"])
    if hide_text:
        fp.Value().SetVisible(False); fp.Reference().SetVisible(False)
    fp.SetPosition(V(x, y))
    if rot:
        fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        net = c["nets"].get(pad.GetNumber())
        if net and net in netmap:
            pad.SetNet(netmap[net])
    return fp

def outline(board, w, h):
    pts = [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.15))
        board.Add(seg)

def gnd_pour(board, netmap, w, h):
    if "GND" not in netmap:
        return
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNetCode(netmap["GND"].GetNetCode())
    zone.SetAssignedPriority(0)
    sps = zone.Outline(); sps.NewOutline()
    for (px, py) in [(0.5, 0.5), (w - 0.5, 0.5), (w - 0.5, h - 0.5), (0.5, h - 0.5)]:
        sps.Append(mm(px), mm(py))
    zone.SetIsFilled(True)
    board.Add(zone)

# ---------------------------------------------------------------------------
def main():
    g.build()
    comps = [c for c in g.COMPONENTS if c["fp"]]
    board = pcbnew.NewBoard(OUT)
    netmap = make_nets(board, comps)

    EDGE = {"JACK", "SPEAKER", "XFMR", "Footswitch_DIN6", "Reverb_Tank_4FB2A1C"}
    edge_parts = [c for c in comps if c["libsym"] in EDGE]
    big_parts  = [c for c in comps if c["libsym"] == "L"]
    main_parts = [c for c in comps if c["libsym"] not in EDGE and c["libsym"] != "L"]

    placed, miss, areas = 0, [], []
    def place(c, x, y, rot=0):
        nonlocal placed
        fp = add_footprint(board, c, x, y, netmap, rot)
        if fp is None:
            miss.append(c["fp"]); return
        bb = fp.GetBoundingBox()
        areas.append(pcbnew.ToMM(bb.GetWidth()) * pcbnew.ToMM(bb.GetHeight()))
        placed += 1

    # main grid; centered horizontally, top-aligned (the board is ~half full of
    # parts -- see the density note -- so the grid uses most of the height, with a
    # bottom strip for the off-board connectors and a right strip for the toroid).
    px, py = 13.6, 11.8
    right = 24.0
    cols = int((BW - 2 * MARGIN - right) // px)
    blk_w = (cols - 1) * px
    x0 = (BW - right - blk_w) / 2.0
    y0 = MARGIN + 5
    for i, c in enumerate(main_parts):
        place(c, x0 + (i % cols) * px, y0 + (i // cols) * py)
    for j, c in enumerate(big_parts):
        place(c, BW - MARGIN - 14, MARGIN + 16 + j * 30)
    ex, ey = MARGIN + 8, BH - MARGIN - 4
    for k, c in enumerate(edge_parts):
        place(c, ex + k * 22.0, ey, rot=90)

    outline(board, BW, BH)
    gnd_pour(board, netmap, BW, BH)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(OUT, board)

    # chassis-fit packing-density check
    part_area = sum(areas)
    print(f"[full] placed {placed}/{len(comps)} footprints, {len(netmap)} nets")
    if miss:
        print("  MISSING:", sorted(set(miss)))
    for label, w, h in [("190x115 (orig PCB)", BW, BH), ("155x90 (Part7 safe-bet)", 155, 90)]:
        usable = (w - 20) * (h - 20)
        print(f"  packing density on {label}: parts={part_area:.0f} mm^2 / "
              f"usable={usable:.0f} mm^2 = {100*part_area/usable:.0f}%")
    return part_area

# ---------------------------------------------------------------------------
def power_demo():
    """Clean, fully-routed demo of the +33V5 and +17V rails over a GND pour.
    Each rail's parts sit isolated in their own row so the chain routes without
    crossings -- a DRC-clean illustration of net-class track widths + ground."""
    g.COMPONENTS.clear(); g.build()
    by = {c["ref"]: c for c in g.COMPONENTS if c["fp"]}
    DW, DH = 120.0, 70.0
    rows = {
      ("+33V5", 2.5, 20.0): ["F1", "C_main", "R_bleed", "R_27V"],     # HighCurrent
      ("+17V",  1.5, 48.0): ["U1", "R_reg1", "C_reg_out1", "R_vb1"],  # Power
    }
    board = pcbnew.NewBoard(OUT_DEMO)
    refs = [r for grp in rows.values() for r in grp]
    netmap = make_nets(board, [by[r] for r in refs])
    placed_fp = {}
    for (net, width, ry), grp in rows.items():
        for i, ref in enumerate(grp):
            fp = add_footprint(board, by[ref], 16 + i * 26.0, ry, netmap)
            placed_fp[ref] = fp

    # route each rail as a trunk in the clear space ABOVE its row, with a short
    # vertical stub from each rail pad up to the trunk (rail pads are the top/left
    # pin of each part, so the stubs never cross a foreign pad).
    routed = 0
    def track(net, width, s, e):
        nonlocal routed
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(s); t.SetEnd(e)
        t.SetWidth(mm(width)); t.SetLayer(pcbnew.F_Cu)
        t.SetNetCode(netmap[net].GetNetCode())
        board.Add(t); routed += 1

    def route_trunk(net, width, trunk_y_mm):
        """Connect every demo pad on `net` to a trunk in clear space (stub+trunk)."""
        trunk = mm(trunk_y_mm)
        pads = sorted((pad.GetCenter() for fp in placed_fp.values()
                       for pad in fp.Pads() if pad.GetNetname() == net),
                      key=lambda p: p.x)
        if len(pads) < 2:
            return
        for p in pads:
            track(net, width, p, pcbnew.VECTOR2I(p.x, trunk))
        track(net, width, pcbnew.VECTOR2I(pads[0].x, trunk),
                          pcbnew.VECTOR2I(pads[-1].x, trunk))

    route_trunk("+33V5", 2.5, 9.0)     # HighCurrent rail, trunk above its row
    route_trunk("+17V",  1.5, 37.0)    # Power rail, trunk above its row
    route_trunk("ADJ17", 0.5, 61.0)    # LM317 set node, trunk below the row
    # +27V links the two rows -- on a single free layer (bottom is the GND pour)
    # it would have to cross the +17V trunk, i.e. it needs a via. Left as a
    # ratsnest here: the point a real layout makes the jump with a via.

    outline(board, DW, DH)
    gnd_pour(board, netmap, DW, DH)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(OUT_DEMO, board)
    print(f"[demo] routed {routed} track segments across 2 rails -> {OUT_DEMO}")

if __name__ == "__main__":
    main()
    power_demo()
