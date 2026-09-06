#!/usr/bin/env python3
"""Build the Vox Cambridge Reverb boards from the schematic component/net data.

KiCad 8 pcbnew API. Produces two boards:

  cambridge_reverb.kicad_pcb   full board: every footprint placed into the Part 5
                               floor-plan ZONES (Input/Preamp | Tone | Reverb/
                               Tremolo | Power Amp | PSU, left -> right, signal
                               order inside each zone), off-board wiring connectors
                               on the bottom WIRING EDGE under their zone, heat-
                               sinking devices on the top edge with the Part 5
                               10 mm keep-out, 4 x M3 mounting holes, 190x115 mm
                               Edge.Cuts, bottom GND pour. Placed, not routed --
                               see route_board.py for the Freerouting pass.

  power_section_demo.kicad_pcb small isolated demo: the +33V5 and +17V rails
                               cleanly placed and ROUTED at their net-class
                               widths (2.5 / 1.5 mm) over a GND pour -- DRC-clean.

Also prints a chassis-fit packing-density check (190x115 vs the Part 7 155x90
safe-bet) and per-zone utilisation. Run from repo root:  python3 kicad/gen/gen_pcb.py
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
MARGIN = 10.0              # Part 4/5: 10 mm margin all round for the chassis / bracket
GAP      = 1.7             # courtyard-to-courtyard spacing inside a zone (routing channel between parts)
ZONE_GAP = 4.0             # empty channel between zones (routing room)
EDGE_Y   = BH - MARGIN - 2.5   # wiring-edge connector row (Part 5: "all pads on one edge")
MAIN_TOP = MARGIN + 1.5
MAIN_BOT = EDGE_Y - 6.0    # bodies stay above the connector row
KEEPOUT  = 10.0            # Part 5: 10 mm clearance around the LM1875 / LM317 mounting area

# Part 5 floor plan: zones left -> right. Each zone takes the on-board parts of the
# listed schematic sheets, in sheet (= signal-chain) order.
ZONES = [
  ("INPUT / PREAMP", ["Preamp"]),
  ("TONE",           ["Tone Stack"]),
  # MRB on top (no off-board wiring), tremolo in the middle, REVERB at the BOTTOM
  # next to its tank / level-pot pads on the wiring edge (shortest TANK_IN/OUT runs)
  ("REVERB / TREM",  ["MRB", "Tremolo", "Reverb"]),
  ("POWER AMP",      ["Power Amp"]),
  ("POWER SUPPLY",   ["Power Supply"]),
]
# Off-board wiring connectors -> the zone whose stretch of the wiring edge they sit on
EDGE_ZONE = {"J_IN1": 0, "J_IN2": 0, "J_IN3": 0,
             "POT_VOL": 1, "POT_TONE": 1,
             "REV1": 2, "POT_REV": 2, "POT_SPD": 2, "POT_DPT": 2, "FS1": 2,
             "LS1": 3,
             "T1": 4}                      # transformer pads: far right, away from signal
BODY_ZONE = {"R_spk_rtn": 3}                # switching-sheet part that lives on the board body
# pack these with another sheet's parts: the footswitch pull-downs belong next to
# the DIN pads on the wiring edge (reverb block = bottom of the effects column)
SHEET_OVERRIDE = {"R_fs_trem": "Reverb", "R_fs_mrb": "Reverb",
                  # the VBIAS_R / VBIAS_T mid-rail dividers (drawn on the PSU sheet) feed
                  # only the effects ICs: place them next to their loads
                  "R_vbr1": "Reverb", "R_vbr2": "Reverb", "C_vbr": "Reverb",
                  "R_vbt1": "Tremolo", "R_vbt2": "Tremolo", "C_vbt": "Tremolo"}
HEATSINK  = {"IC_PA": 3, "U1": 4}           # top edge of their zone, tab outward, keep-out around
# Board columns, left -> right; a column may stack several zones top -> bottom
# (the 4-part TONE zone sits under INPUT/PREAMP instead of wasting a whole strip).
COLUMNS = [[0, 1], [2], [3], [4]]
# extra width weight for zones that carry the fat HighCurrent/Power traces (routing room)
ZONE_WEIGHT = {3: 1.35, 4: 1.05}

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

def escape_stubs(board, fps):
    """Pre-routed, LOCKED escape stubs from the LM1875's inner pins.

    The TO-220-5 pins sit on a 1.70 mm pitch, so a 1.5 mm (Power) or 2.5 mm
    (HighCurrent) trace cannot enter pins 3/4/5 without violating the 0.3 mm
    class clearance to the neighbouring pins -- the autorouter leaves exactly
    these unrouted. A hand layout necks the trace down at the pin; we do the same
    with a 0.9 mm stub per pin (0.9 mm of 1 oz copper carries the ~1.7 A peak with
    margin over a few mm): pin 4 (PA_OUT) straight down 6 mm, pin 5 (+33V5)
    fanned 5 mm right / 5 mm down, so the full-width traces attach to stub ends
    ~6.8 mm apart, clear of the pin row. Locked tracks export to the DSN as
    `(type fix)`, so Freerouting keeps them and connects to their far ends."""
    if "IC_PA" not in fps:
        return 0
    fp = fps["IC_PA"][1]
    n = 0
    # pin 3 (GND, V-) needs no stub: it is a THT pad in the bottom GND pour.
    for num, dx, dy in (("4", 0.0, 6.0), ("5", 5.0, 5.0)):
        pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
        c = pad.GetCenter()
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(c); t.SetEnd(pcbnew.VECTOR2I(c.x + mm(dx), c.y + mm(dy)))
        t.SetWidth(mm(0.9)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(pad.GetNetCode())
        t.SetLocked(True); board.Add(t); n += 1
    return n

def mounting_holes(board, w, h, inset=5.0):
    for i, (x, y) in enumerate([(inset, inset), (w - inset, inset), (inset, h - inset), (w - inset, h - inset)]):
        fp = pcbnew.FootprintLoad(os.path.join(SYS_FP, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
        if fp is None:
            return
        # unique references: the Specctra DSN exporter (route_board.py) refuses duplicates
        board.Add(fp); fp.SetReference(f"H{i+1}"); fp.Reference().SetVisible(False)
        fp.SetPosition(V(x, y))
        for pad in fp.Pads():            # keep the GND pour 0.5 mm off the NPTH hole edge
            pad.SetLocalClearance(mm(0.5))

# ---------------------------------------------------------------------------
# Placement helpers: work in bounding-box space (no text), then move the anchor.
def bbox_mm(fp):
    bb = fp.GetBoundingBox(False, False)
    return (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()),
            pcbnew.ToMM(bb.GetCenter().x) - pcbnew.ToMM(fp.GetPosition().x),
            pcbnew.ToMM(bb.GetCenter().y) - pcbnew.ToMM(fp.GetPosition().y))

def put(fp, cx, cy, rot=0):
    """Place the footprint so that its (text-less) bounding box is centred on (cx, cy)."""
    fp.SetOrientationDegrees(rot)
    w, h, ox, oy = bbox_mm(fp)
    fp.SetPosition(V(cx - ox, cy - oy))
    return w, h

def shelf_pack(parts, x0, x1, y0, ybot, rot=0):
    """Row ('shelf') packing, keeping the given part order, top->bottom; rows run
    serpentine (left->right, then right->left) so consecutive parts stay
    neighbours across a row wrap. Returns the y below the last row + (ref, w, h)."""
    rows, row, roww = [], [], 0.0
    for c, fp in parts:
        fp.SetOrientationDegrees(rot)
        w, h, _, _ = bbox_mm(fp)
        if row and roww + w > (x1 - x0) + 1e-6:      # wrap to the next row
            rows.append(row); row, roww = [], 0.0
        row.append((c, fp, w, h)); roww += w + GAP
    if row:
        rows.append(row)
    y, out = y0, []
    for i, row in enumerate(rows):
        row_h = max(h for _, _, _, h in row)
        x = x0
        for c, fp, w, h in (row if i % 2 == 0 else row[::-1]):
            put(fp, x + w / 2, y + h / 2, rot)
            out.append((c["ref"], w, h)); x += w + GAP
        y += row_h + GAP
    return y - GAP, out

# ---------------------------------------------------------------------------
def main():
    g.build()
    comps = [c for c in g.COMPONENTS if c["fp"]]
    board = pcbnew.NewBoard(OUT)
    netmap = make_nets(board, comps)

    # load everything first (at the origin) so we can measure real bounding boxes
    fps, miss = {}, []
    for c in comps:
        fp = add_footprint(board, c, 0, 0, netmap)
        if fp is None:
            miss.append(c["fp"]); continue
        fps[c["ref"]] = (c, fp)

    sheet_zone = {sh: i for i, (_, shs) in enumerate(ZONES) for sh in shs}
    sheet_order = [sh for _, shs in ZONES for sh in shs] + ["Switching / I-O"]
    zone_parts = [[] for _ in ZONES]; edge_parts = [[] for _ in ZONES]; hs = {}
    for ref, (c, fp) in fps.items():
        if ref in HEATSINK:      hs[ref] = (c, fp)
        elif ref in EDGE_ZONE:   edge_parts[EDGE_ZONE[ref]].append((c, fp))
        elif ref in BODY_ZONE:   zone_parts[BODY_ZONE[ref]].append((c, fp))
        else:
            c = dict(c, sheet=SHEET_OVERRIDE.get(ref, c["sheet"]))
            zone_parts[sheet_zone[c["sheet"]]].append((c, fp))

    # inside a zone keep the sheet (signal-chain) grouping, but sort each sheet's
    # parts tallest-first so the shelves pack tightly (heights vary 3x: discs vs cans)
    for zp in zone_parts:
        zp.sort(key=lambda cf: (sheet_order.index(cf[0]["sheet"]), -bbox_mm(cf[1])[1]))

    def pack_zone(zi, x0, x1, y):
        """Place zone zi between x0..x1 starting at y; returns the y its parts reach."""
        for ref, z in HEATSINK.items():        # top edge, centred, tab (-y) outward
            if z == zi and ref in hs:
                w, h, _, _ = bbox_mm(hs[ref][1])
                put(hs[ref][1], (x0 + x1) / 2, y + h / 2 + 1.0, 0)
                y += h + 1.0 + KEEPOUT
        ybot, _ = shelf_pack(zone_parts[zi], x0, x1, y, MAIN_BOT)
        return ybot

    def pack_column(ci, x0, x1):
        y = MAIN_TOP
        for zi in COLUMNS[ci]:
            y = pack_zone(zi, x0, x1, y) + ZONE_GAP
        return y - ZONE_GAP

    # column widths: start proportional to (weighted) padded part area, then
    # rebalance a few times so every column packs to about the same height,
    # floored at the widest part so nothing sticks out sideways.
    ncol = len(COLUMNS)
    total_w = BW - 2 * MARGIN - ZONE_GAP * (ncol - 1)
    def padded(parts):
        return sum((bbox_mm(fp)[0] + GAP) * (bbox_mm(fp)[1] + GAP) for _, fp in parts)
    zarea = [padded(p) for p in zone_parts]
    for ref, z in HEATSINK.items():
        if ref in hs:
            w, h, _, _ = bbox_mm(hs[ref][1]); zarea[z] += (w + 2 * KEEPOUT) * (h + KEEPOUT)
    wt = [max(ZONE_WEIGHT.get(z, 1.0) for z in col) for col in COLUMNS]
    areas = [sum(zarea[z] for z in col) * k for col, k in zip(COLUMNS, wt)]
    edge_w = [[put(fp, 0, 0, 0)[0] for _, fp in ep] for ep in edge_parts]   # wire pads run along the edge
    minw = [max([bbox_mm(fp)[0] for z in col for _, fp in zone_parts[z]] + [12.0]) + GAP for col in COLUMNS]
    widths = [max(total_w * a / sum(areas), m) for a, m in zip(areas, minw)]
    for _ in range(12):
        widths = [w * total_w / sum(widths) for w in widths]
        x = MARGIN; hts = []
        for ci in range(ncol):
            hts.append(pack_column(ci, x, x + widths[ci]) - MAIN_TOP); x += widths[ci] + ZONE_GAP
        target = sum(w * h * k for w, h, k in zip(widths, hts, wt)) / total_w
        widths = [max(w * (0.5 + 0.5 * (h * k) / target), m) for w, h, m, k in zip(widths, hts, minw, wt)]
    widths = [w * total_w / sum(widths) for w in widths]

    # final placement, plus the wiring-edge connector row (one global cursor so
    # neighbouring groups never collide; T1 pinned to the far right)
    x = MARGIN; util = []; cursor = MARGIN
    for ci, col in enumerate(COLUMNS):
        x0, x1 = x, x + widths[ci]
        ybot = pack_column(ci, x0, x1)
        eps = [(c, fp, w) for z in col for (c, fp), w in zip(edge_parts[z], edge_w[z])]
        span = sum(w for _, _, w in eps) + GAP * max(len(eps) - 1, 0)
        ex = max((x0 + x1) / 2 - span / 2, cursor)
        if ci == ncol - 1:
            ex = max(ex, x1 - span)
        for c, fp, w in eps:
            put(fp, ex + w / 2, EDGE_Y, 0); ex += w + GAP
        cursor = ex
        name = " + ".join(ZONES[z][0] for z in col)
        util.append((name, x0, x1, ybot, ybot > MAIN_BOT + 1e-6))
        x = x1 + ZONE_GAP

    outline(board, BW, BH)
    mounting_holes(board, BW, BH)
    stubs = escape_stubs(board, fps)
    gnd_pour(board, netmap, BW, BH)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(OUT, board)

    # chassis-fit packing-density check (bounding boxes, as before)
    areas_all = [bbox_mm(fp)[0] * bbox_mm(fp)[1] for _, fp in fps.values()]
    part_area = sum(areas_all)
    print(f"[full] placed {len(fps)}/{len(comps)} footprints, {len(netmap)} nets, {stubs} locked escape stubs")
    if miss:
        print("  MISSING:", sorted(set(miss)))
    for zname, x0, x1, ybot, over in util:
        print(f"  column {zname:28s} x={x0:6.1f}..{x1:6.1f} ({x1-x0:5.1f} mm)  parts reach y={ybot:5.1f} "
              f"of {MAIN_BOT:.0f}{'  ** OVERFLOW **' if over else ''}")
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
    DW, DH = 160.0, 70.0
    rows = {
      ("+33V5", 2.5, 20.0): ["F1", "C_main", "R_bleed", "R_27V"],     # HighCurrent
      ("+17V",  1.5, 48.0): ["U1", "R_reg1", "C_reg_out1", "R_vbr1"],  # Power
    }
    board = pcbnew.NewBoard(OUT_DEMO)
    refs = [r for grp in rows.values() for r in grp]
    netmap = make_nets(board, [by[r] for r in refs])
    placed_fp = {}
    for (net, width, ry), grp in rows.items():
        for i, ref in enumerate(grp):
            fp = add_footprint(board, by[ref], 22 + i * 36.0, ry, netmap)
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
    # VREG_IN links the two rows -- on a single free layer (bottom is the GND pour)
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
