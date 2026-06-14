#!/usr/bin/env python3
"""Build cambridge_reverb.kicad_pcb from the schematic's component/net data.

Uses the KiCad 8 pcbnew Python API: loads each component's footprint, places it
on a grid, assigns pad nets from the generator's net map, draws the board
outline (Edge.Cuts), and pours a bottom-layer GND plane. The result is a real,
auto-placed (not yet routed) board for DRC. Run from repo root:

    python3 kicad/gen/gen_pcb.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
import gen_kicad as g

REPO_KI = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYS_FP  = "/usr/share/kicad/footprints"
OUT     = os.path.join(REPO_KI, "cambridge_reverb.kicad_pcb")

# Board outline (mm). 190x115 matches the original 25-5274-2 footprint (errata #9).
BW, BH = 190.0, 115.0
MARGIN = 10.0

def fp_libpath(fpid):
    lib, name = fpid.split(":")
    if lib == "cambridge_reverb":
        return os.path.join(REPO_KI, "footprints", "cambridge_reverb.pretty"), name
    return os.path.join(SYS_FP, lib + ".pretty"), name

def mm(v): return pcbnew.FromMM(v)
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def main():
    g.build()                      # populates g.COMPONENTS (no files written)
    comps = [c for c in g.COMPONENTS if c["fp"]]   # drop PWR_FLAG (virtual)

    board = pcbnew.NewBoard(OUT)

    # nets
    netmap = {}
    allnets = set()
    for c in comps:
        for n in c["nets"].values():
            allnets.add(n)
    for n in sorted(allnets):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netmap[n] = ni

    # Split parts: off-board connectors go on a bottom "wiring edge" strip, the
    # 25 mm toroid gets a reserved spot, everything else fills the main grid.
    EDGE = {"JACK", "SPEAKER", "XFMR", "Footswitch_DIN6", "Reverb_Tank_4FB2A1C"}
    edge_parts = [c for c in comps if c["libsym"] in EDGE]
    big_parts  = [c for c in comps if c["libsym"] == "L"]
    main_parts = [c for c in comps if c["libsym"] not in EDGE and c["libsym"] != "L"]

    placed = 0
    miss = []

    def place(c, x, y, rot=0):
        nonlocal placed
        libpath, name = fp_libpath(c["fp"])
        fp = pcbnew.FootprintLoad(libpath, name)
        if fp is None:
            miss.append(c["fp"]); return
        board.Add(fp)
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        fp.Value().SetVisible(False)         # cut silkscreen clutter
        fp.Reference().SetVisible(False)     # ratsnest carries refs; keep silk clean
        fp.SetPosition(V(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            net = c["nets"].get(pad.GetNumber())
            if net and net in netmap:
                pad.SetNet(netmap[net])
        placed += 1

    # main grid (top area, inside margins); vertical resistors keep courtyards small
    x0, y0 = MARGIN + 5, MARGIN + 5
    pitch_x, pitch_y = 13.6, 11.8
    cols = int((BW - 2 * MARGIN - 24) // pitch_x)   # leave the right strip for the toroid
    for i, c in enumerate(main_parts):
        place(c, x0 + (i % cols) * pitch_x, y0 + (i // cols) * pitch_y)

    # reserved toroid spot (right strip)
    for j, c in enumerate(big_parts):
        place(c, BW - MARGIN - 16, MARGIN + 16 + j * 30)

    # off-board connectors along the bottom wiring edge, rotated to lie along it
    ex, ey = MARGIN + 8, BH - MARGIN - 4
    for k, c in enumerate(edge_parts):
        place(c, ex + k * 22.0, ey, rot=90)

    # board outline (Edge.Cuts rectangle)
    pts = [(0, 0), (BW, 0), (BW, BH), (0, BH), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.15))
        board.Add(seg)

    # GND pour on bottom layer
    if "GND" in netmap:
        zone = pcbnew.ZONE(board)
        zone.SetLayer(pcbnew.B_Cu)
        zone.SetNetCode(netmap["GND"].GetNetCode())
        zone.SetAssignedPriority(0)
        sps = zone.Outline()
        sps.NewOutline()
        inset = 0.5
        for (px, py) in [(inset, inset), (BW - inset, inset),
                         (BW - inset, BH - inset), (inset, BH - inset)]:
            sps.Append(mm(px), mm(py))
        zone.SetIsFilled(True)
        board.Add(zone)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    pcbnew.SaveBoard(OUT, board)
    print(f"placed {placed}/{len(comps)} footprints, {len(netmap)} nets -> {OUT}")
    if miss:
        print("MISSING FOOTPRINTS:", sorted(set(miss)))

if __name__ == "__main__":
    main()
