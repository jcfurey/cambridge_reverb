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
OUT_DEMO = os.path.join(REPO_KI, "power_section_demo.kicad_pcb")

# Board parameters per build profile (see gen_kicad.set_profile):
#   tht -- the primary all-through-hole board, 190 x 115 (original 25-5274-2, errata #9)
#   smd -- the mixed SMD/THT variant, sized for the Part 7 155 x 90 "safe-bet" chassis
PROFILES = {
  # MARGIN: Part 4/5 ask 10 mm all round on the 190x115 board (chassis bracket); the
  # small-chassis SMD board keeps 6 mm (M3 holes at 5 mm inset still clear).
  # TOP_POUR: the SMD board also gets a GND pour on F.Cu (SMD ground pads have no
  # through-hole to reach the bottom pour; two pours + the THT GND pads stitching
  # them is the normal 2-layer SMD arrangement). The THT board keeps top = signal only.
  "tht": dict(BW=190.0, BH=115.0, GAP=1.2, MARGIN=10.0, ZONE_GAP=3.5, BOT_GAP=4.5, TOP_POUR=False, OUT="cambridge_reverb.kicad_pcb",     SUBDIR=""),
  "smd": dict(BW=155.0, BH=90.0,  GAP=0.4, MARGIN=6.0,  ZONE_GAP=3.0, BOT_GAP=3.0, TOP_POUR=True,  OUT="cambridge_reverb_smd.kicad_pcb", SUBDIR="smd"),
}
PROFILE = "tht"
MARGIN = 10.0              # (set per profile in configure())
ZONE_GAP = 4.0             # empty channel between columns (routing room)
ZONE_VGAP = 2.0            # gap between zones stacked in one column
def configure(profile):
    """Select the build profile: board size, margins, part gap, output path (+ gen_kicad's footprint map)."""
    global PROFILE, BW, BH, GAP, MARGIN, ZONE_GAP, EDGE_Y, MAIN_TOP, MAIN_BOT, OUT, TOP_POUR
    PROFILE = profile; P = PROFILES[profile]
    BW, BH, GAP, MARGIN, ZONE_GAP, TOP_POUR = P["BW"], P["BH"], P["GAP"], P["MARGIN"], P["ZONE_GAP"], P["TOP_POUR"]
    EDGE_Y   = BH - MARGIN - 2.5   # wiring-edge connector row (Part 5: "all pads on one edge")
    MAIN_TOP = MARGIN + 1.5
    MAIN_BOT = EDGE_Y - P["BOT_GAP"]   # bodies stay above the connector row
    OUT = os.path.join(REPO_KI, P["SUBDIR"], P["OUT"])
    g.set_profile(profile)
configure("tht")
KEEPOUT  = 10.0            # Part 5: 10 mm clearance around the LM1875 / LM317 mounting area
TP_W, TP_H = 6.0, 4.5      # test-point cell: 2 mm pad + its silk label, in a strip at the top of each zone

# Part 5 floor plan: zones left -> right. Each zone takes the on-board parts of the
# listed schematic sheets, in sheet (= signal-chain) order.
ZONES = [
  ("INPUT / PREAMP", ["Preamp"]),
  ("TONE",           ["Tone Stack"]),
  # effects column, stacked: MRB + tremolo on top (no tank wiring), REVERB at the
  # BOTTOM next to its tank / level-pot pads on the wiring edge (shortest
  # TANK_IN/OUT runs); each zone gets its own test-point strip above its parts
  ("TREMOLO / MRB",  ["MRB", "Tremolo"]),
  ("REVERB",         ["Reverb"]),
  ("POWER AMP",      ["Power Amp"]),
  ("POWER SUPPLY",   ["Power Supply"]),
]
# Off-board wiring connectors -> the zone whose stretch of the wiring edge they sit on
EDGE_ZONE = {"J_IN1": 0, "J_IN2": 0, "J_IN3": 0,
             "POT_VOL": 1, "POT_BASS": 1, "POT_TREB": 1, "SW_MID": 1,   # tone zone: 3 panel pots + the mid-cut toggle
             "POT_SPD_A": 2, "POT_SPD_B": 2, "POT_DPT": 2,   # dual-gang speed pot = two 3-pad groups
             "REV1": 3, "POT_REV": 3, "FS1": 3,
             "LS1": 4,
             "T1": 5}                      # transformer pads: far right, away from signal
BODY_ZONE = {"R_spk_rtn": 4}                # switching-sheet part that lives on the board body
# The 155x90 SMD board's wiring edge (137 mm between the corner holes) is ~9 mm
# too short for all 13 connector groups once the Bass/Treble pots and the mid-cut
# toggle join it, so there the input-jack pads run down the LEFT edge instead,
# rotated 90 deg, in the 6 mm margin next to the preamp (shortest input wiring;
# the margin between the two M3 holes is free). The 190x115 THT board keeps
# Part 5's "all pads on one edge".
LEFT_EDGE = {"smd": ["J_IN1", "J_IN2", "J_IN3"]}
# pack these with another sheet's parts: the footswitch pull-downs belong next to
# the DIN pads on the wiring edge (reverb block = bottom of the effects column)
SHEET_OVERRIDE = {"R_fs_trem": "Reverb", "R_fs_mrb": "Reverb",
                  # the VBIAS_R / VBIAS_T mid-rail dividers (drawn on the PSU sheet) feed
                  # only the effects ICs: place them next to their loads
                  "R_vbr1": "Reverb", "R_vbr2": "Reverb", "C_vbr": "Reverb",
                  "R_vbt1": "Tremolo", "R_vbt2": "Tremolo", "C_vbt": "Tremolo"}
HEATSINK  = {"IC_PA": 4, "U1": 5}           # top edge of their zone, tab outward, keep-out around
# Board columns, left -> right; a column may stack several zones top -> bottom.
# TONE stays stacked under INPUT/PREAMP: Part 5 drew it as its own column, but a
# fifth column (one more channel, a 10 mm DIP-14 alone on 16 mm-wide shelves)
# does not fit either board's area with the errata #20 parts. Instead the
# tone/preamp column gets extra WIDTH (ZONE_WEIGHT): the 26-part tone zone is the
# dense one, and a wider zone means shorter rows, the four panel-control pad
# groups sitting right under it, and room for the router (8-9 links were left
# open there when the column was 28 mm wide).
COLUMNS = [[0, 1], [2, 3], [4], [5]]
# extra width weight: tone/preamp column (routing room, see above) and the PA
# zone that carries the fat HighCurrent/Power traces
ZONE_WEIGHT = {1: 1.35, 4: 1.05}     # (a bigger PA weight starves the effects column once the TP strips are in)

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
    if "(opt)" in c["value"]:                # optional MRB caps: on the board, not fitted
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP)   # -> excluded from the JLC position file
    if hide_text:
        fp.Value().SetVisible(False); fp.Reference().SetVisible(False)
    if c["libsym"] == "TP":                      # the value IS the silk label (net alias)
        fp.Value().SetVisible(True)
    fp.SetPosition(V(x, y))
    if rot:
        fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        net = c["nets"].get(pad.GetNumber())
        if net and net in netmap:
            pad.SetNet(netmap[net])
        if TOP_POUR and pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and net == "GND":
            # SMD ground pads connect SOLID into the top pour (no thermal spokes to
            # starve; reflow/hot-air does not care) -- THT pads keep thermal reliefs
            pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    return fp

def outline(board, w, h):
    pts = [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.15))
        board.Add(seg)

def gnd_pour(board, netmap, w, h, layer=None):
    if "GND" not in netmap:
        return
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu if layer is None else layer)
    if layer == pcbnew.F_Cu:
        # top pour: copper for the SMD ground pads (they carry a SOLID per-pad
        # override) and shielding; it does NOT put thermal spokes on the through-
        # hole pads -- those ground through the bottom pour, so no starved spokes
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_NONE)
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

def keepouts(board, w, h, edge=2.0, hole_inset=5.0, hole_r=3.6):
    """Rule areas (no tracks / vias, pours allowed) that the Specctra export hands
    to Freerouting as keepouts: a 2 mm frame inside the board edge (KiCad's
    copper-to-edge rule is 0.5 mm; the router only knows the outline) and a square
    around each M3 hole (its 0.5 mm local clearance does not survive the export).
    Without them the SMD board's left-edge jack pads invited 45 mm of trace along
    the edge and under a mounting hole."""
    rects = [(0.3, 0.3, w - 0.3, edge), (0.3, h - edge, w - 0.3, h - 0.3),
             (0.3, 0.3, edge, h - 0.3), (w - edge, 0.3, w - 0.3, h - 0.3)]
    for cx, cy in [(hole_inset, hole_inset), (w - hole_inset, hole_inset),
                   (hole_inset, h - hole_inset), (w - hole_inset, h - hole_inset)]:
        rects.append((cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r))
    for x0, y0, x1, y1 in rects:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET(); ls.addLayer(pcbnew.F_Cu); ls.addLayer(pcbnew.B_Cu)
        z.SetLayerSet(ls)
        sps = z.Outline(); sps.NewOutline()
        for px, py in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
            sps.Append(mm(px), mm(py))
        board.Add(z)

def fiducials(board, w, h):
    """Three 1 mm copper / 2 mm mask fiducials for the pick-and-place camera (JLCPCB asks
    for >= 3 on the assembled side; a non-symmetric set so orientation is unambiguous).
    They sit in the margin strip between the corner holes' courtyards and the first row
    of parts (top) / below the wiring-edge pads (bottom right)."""
    for i, (x, y) in enumerate([(12.0, 4.0), (w - 12.0, 4.0), (w - 12.0, h - 4.0)]):
        fp = pcbnew.FootprintLoad(os.path.join(SYS_FP, "Fiducial.pretty"), "Fiducial_1mm_Mask2mm")
        if fp is None:
            return
        board.Add(fp); fp.SetReference(f"FID{i+1}"); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        fp.SetPosition(V(x, y))

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

def layout_row(row, x0, y, row_h):
    """Lay one shelf out left -> right. Parts no taller than half the row are STACKED
    vertically beside their neighbours (as many as fit in row_h), so a row that holds
    one tall can or DIP does not waste 20 mm of height under every resistor next to it.
    Returns [(c, fp, cx, cy)] and the width used."""
    x, i, out = x0, 0, []
    while i < len(row):
        c, fp, w, h = row[i]
        if h <= row_h / 2 + 1e-6:
            stack, hsum = [], 0.0
            while (i < len(row) and row[i][3] <= row_h / 2 + 1e-6
                   and hsum + row[i][3] + (GAP if stack else 0.0) <= row_h + 1e-6):
                hsum += row[i][3] + (GAP if stack else 0.0); stack.append(row[i]); i += 1
            sw, yy = max(p[2] for p in stack), y
            for c2, fp2, w2, h2 in stack:
                out.append((c2, fp2, x + sw / 2, yy + h2 / 2)); yy += h2 + GAP
            x += sw + GAP
        else:
            out.append((c, fp, x + w / 2, y + h / 2)); x += w + GAP; i += 1
    return out, x - GAP - x0

def shelf_pack(parts, x0, x1, y0, ybot, rot=0):
    """Row ('shelf') packing, keeping the given part order, top->bottom; rows run
    serpentine (left->right, then right->left) so consecutive parts stay
    neighbours across a row wrap; short parts stack beside tall ones (layout_row).
    Returns the y below the last row + (ref, w, h)."""
    sized = []
    for c, fp in parts:
        fp.SetOrientationDegrees(rot)
        w, h, _, _ = bbox_mm(fp)
        sized.append((c, fp, w, h))
    rows, row = [], []
    for item in sized:
        trial = row + [item]
        if row and layout_row(trial, x0, 0.0, max(p[3] for p in trial))[1] > (x1 - x0) + 1e-6:
            rows.append(row); row = [item]
        else:
            row = trial
    if row:
        rows.append(row)
    y, out = y0, []
    for i, row in enumerate(rows):
        row_h = max(h for _, _, _, h in row)
        placed, _ = layout_row(row if i % 2 == 0 else row[::-1], x0, y, row_h)
        for c, fp, cx, cy in placed:
            put(fp, cx, cy, rot)
            w, h, _, _ = bbox_mm(fp)
            out.append((c["ref"], w, h))
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
    tp_parts = [[] for _ in ZONES]
    for ref, (c, fp) in fps.items():
        if c["libsym"] == "TP":  tp_parts[sheet_zone[c["sheet"]]].append((c, fp))
        elif ref in HEATSINK:    hs[ref] = (c, fp)
        elif ref in EDGE_ZONE:   edge_parts[EDGE_ZONE[ref]].append((c, fp))
        elif ref in BODY_ZONE:   zone_parts[BODY_ZONE[ref]].append((c, fp))
        else:
            c = dict(c, sheet=SHEET_OVERRIDE.get(ref, c["sheet"]))
            zone_parts[sheet_zone[c["sheet"]]].append((c, fp))

    # inside a zone keep the sheet (signal-chain) grouping; within a sheet sort by
    # height CLASS only -- ICs/big cans (> 8 mm), small cans (> 4.4 mm), then the
    # axials and discs -- so the shelves still pack tightly, but inside a class the
    # parts keep their schematic (signal) order: netlist neighbours stay board
    # neighbours, which is what the router needs in a dense zone
    def hkey(fp):
        h = bbox_mm(fp)[1]
        if h > 4.4:                      # ICs and cans: tallest first (few, no locality to lose)
            return (0, -h)
        return (1, 0.0)                  # axials, discs, chips: schematic order
    for zp in zone_parts:
        zp.sort(key=lambda cf: (sheet_order.index(cf[0]["sheet"]), hkey(cf[1])))

    def pack_zone(zi, x0, x1, y):
        """Place zone zi between x0..x1 starting at y; returns the y its parts reach."""
        for ref, z in HEATSINK.items():        # top edge, centred, tab (-y) outward
            if z == zi and ref in hs:
                w, h, _, _ = bbox_mm(hs[ref][1])
                put(hs[ref][1], (x0 + x1) / 2, y + h / 2 + 1.0, 0)
                y += h + 1.0 + KEEPOUT
        # test-point strip: a row of labelled 2 mm pads across the top of the zone,
        # where a probe reaches them without leaning over parts
        tps = tp_parts[zi]
        if tps:
            per_row = max(1, int((x1 - x0 + GAP) // TP_W))
            for i, (c, fp) in enumerate(tps):
                r, k = divmod(i, per_row)
                put(fp, x0 + k * TP_W + TP_W / 2, y + r * TP_H + TP_H - 1.6, 0)   # label above, courtyard flush with the cell
            y += ((len(tps) - 1) // per_row + 1) * TP_H + GAP
        ybot, _ = shelf_pack(zone_parts[zi], x0, x1, y, MAIN_BOT)
        return ybot

    def pack_column(ci, x0, x1):
        y = MAIN_TOP
        for zi in COLUMNS[ci]:
            y = pack_zone(zi, x0, x1, y) + ZONE_VGAP
        return y - ZONE_VGAP

    # column widths: start proportional to (weighted) padded part area, then
    # rebalance a few times so every column packs to about the same height,
    # floored at the widest part so nothing sticks out sideways.
    ncol = len(COLUMNS)
    total_w = BW - 2 * MARGIN - ZONE_GAP * (ncol - 1)
    def padded(parts):
        return sum((bbox_mm(fp)[0] + GAP) * (bbox_mm(fp)[1] + GAP) for _, fp in parts)
    zarea = [padded(p) + len(t) * TP_W * TP_H for p, t in zip(zone_parts, tp_parts)]
    for ref, z in HEATSINK.items():
        if ref in hs:
            w, h, _, _ = bbox_mm(hs[ref][1]); zarea[z] += (w + 2 * KEEPOUT) * (h + KEEPOUT)
    wt = [max(ZONE_WEIGHT.get(z, 1.0) for z in col) for col in COLUMNS]
    areas = [sum(zarea[z] for z in col) * k for col, k in zip(COLUMNS, wt)]
    left_refs = LEFT_EDGE.get(PROFILE, [])
    left_parts = [(c, fp) for ep in edge_parts for (c, fp) in ep if c["ref"] in left_refs]
    edge_parts = [[(c, fp) for (c, fp) in ep if c["ref"] not in left_refs] for ep in edge_parts]
    edge_w = [[put(fp, 0, 0, 0)[0] for _, fp in ep] for ep in edge_parts]   # wire pads run along the edge
    min_col = 12.0 if PROFILE == "tht" else 10.5     # narrowest useful column (axial R vs 0805 rows)
    minw = [max([bbox_mm(fp)[0] for z in col for _, fp in zone_parts[z]] + [min_col]) + GAP for col in COLUMNS]
    widths = [max(total_w * a / sum(areas), m) for a, m in zip(areas, minw)]
    for _ in range(12):
        widths = [w * total_w / sum(widths) for w in widths]
        x = MARGIN; hts = []
        for ci in range(ncol):
            hts.append(pack_column(ci, x, x + widths[ci]) - MAIN_TOP); x += widths[ci] + ZONE_GAP
        target = sum(w * h * k for w, h, k in zip(widths, hts, wt)) / total_w
        widths = [max(w * (0.5 + 0.5 * (h * k) / target), m) for w, h, m, k in zip(widths, hts, minw, wt)]
    widths = [w * total_w / sum(widths) for w in widths]
    # shelf packing is discrete, so the proportional balance can leave one column a
    # fraction of a row over MAIN_BOT while another has slack: repair by moving width
    # from a column that can spare it to the overflowing one, 1 mm at a time. A donor is
    # accepted only if it still fits after the move (a 0.5 mm step used to oscillate:
    # the donor wrapped a row, overflowed, and took the width straight back).
    def heights(ws):
        x = MARGIN; bs = []
        for ci in range(ncol):
            bs.append(pack_column(ci, x, x + ws[ci])); x += ws[ci] + ZONE_GAP
        return bs
    step = 1.0
    for _ in range(60):
        bots = heights(widths)
        over = [ci for ci in range(ncol) if bots[ci] > MAIN_BOT + 1e-6]
        if not over:
            break
        worst = max(over, key=lambda ci: bots[ci])
        moved = False
        for donor in sorted((ci for ci in range(ncol) if ci != worst and widths[ci] - step >= minw[ci]),
                            key=lambda ci: bots[ci]):
            trial = list(widths); trial[donor] -= step; trial[worst] += step
            tb = heights(trial)
            if tb[donor] <= MAIN_BOT + 1e-6 and tb[worst] <= bots[worst] + 1e-6:
                widths = trial; moved = True
                break
        if not moved:
            break

    # final placement, plus the wiring-edge connector row (one global cursor so
    # neighbouring groups never collide; T1 pinned to the far right)
    x = MARGIN; util = []
    edge_lo, edge_hi = max(MARGIN, 9.0), min(BW - MARGIN, BW - 9.0)   # clear of the corner M3 holes
    cursor = edge_lo
    for ci, col in enumerate(COLUMNS):
        x0, x1 = x, x + widths[ci]
        ybot = pack_column(ci, x0, x1)
        eps = [(c, fp, w) for z in col for (c, fp), w in zip(edge_parts[z], edge_w[z])]
        span = sum(w for _, _, w in eps) + GAP * max(len(eps) - 1, 0)
        ex = max((x0 + x1) / 2 - span / 2, cursor)
        if ci == ncol - 1:
            ex = max(ex, edge_hi - span)
        for c, fp, w in eps:
            put(fp, ex + w / 2, EDGE_Y, 0); ex += w + GAP
        cursor = ex
        name = " + ".join(ZONES[z][0] for z in col)
        util.append((name, x0, x1, ybot, ybot > MAIN_BOT + 1e-6))
        x = x1 + ZONE_GAP

    # left-edge column (SMD board): pad groups stacked top -> bottom below the
    # corner hole's courtyard, centred in the margin, GAP clear of the first column
    ly = 5.0 + 3.5 + GAP                 # M3 hole at 5 mm inset, 3.45 mm courtyard radius
    for c, fp in left_parts:
        w, h = put(fp, 0, 0, 90)
        put(fp, MARGIN - GAP - w / 2, ly + h / 2, 90); ly += h + GAP

    outline(board, BW, BH)
    mounting_holes(board, BW, BH)
    keepouts(board, BW, BH)
    if TOP_POUR:                              # the assembled (SMD) board: JLCPCB fiducials
        fiducials(board, BW, BH)
    stubs = escape_stubs(board, fps)
    gnd_pour(board, netmap, BW, BH)
    if TOP_POUR:
        gnd_pour(board, netmap, BW, BH, layer=pcbnew.F_Cu)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(OUT, board)

    # chassis-fit packing-density check (bounding boxes, as before)
    areas_all = [bbox_mm(fp)[0] * bbox_mm(fp)[1] for _, fp in fps.values()]
    part_area = sum(areas_all)
    print(f"[{PROFILE}] placed {len(fps)}/{len(comps)} footprints, {len(netmap)} nets, {stubs} locked escape stubs "
          f"-> {os.path.relpath(OUT, REPO_KI)} ({BW:.0f}x{BH:.0f} mm)")
    if miss:
        print("  MISSING:", sorted(set(miss)))
    for zname, x0, x1, ybot, over in util:
        print(f"  column {zname:28s} x={x0:6.1f}..{x1:6.1f} ({x1-x0:5.1f} mm)  parts reach y={ybot:5.1f} "
              f"of {MAIN_BOT:.0f}{'  ** OVERFLOW **' if over else ''}")
    for label, w, h in [("190x115 (orig PCB)", 190, 115), ("155x90 (Part7 safe-bet)", 155, 90)]:
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
    import argparse
    ap = argparse.ArgumentParser(description="Generate the placed board(s) from the schematic data")
    ap.add_argument("--profile", choices=tuple(PROFILES), default="tht",
                    help="tht: kicad/cambridge_reverb.kicad_pcb (190x115); smd: kicad/smd/cambridge_reverb_smd.kicad_pcb (155x90)")
    a = ap.parse_args()
    configure(a.profile)
    if a.profile == "smd":
        g.write_smd_project_files()      # .kicad_pro + lib tables next to the board (DRC needs the net classes)
    main()
    if a.profile == "tht":
        power_demo()
