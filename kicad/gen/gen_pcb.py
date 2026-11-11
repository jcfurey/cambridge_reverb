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
import math
import pcbnew
import gen_kicad as g

REPO_KI = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYS_FP  = "/usr/share/kicad/footprints"
OUT_DEMO = os.path.join(REPO_KI, "power_section_demo.kicad_pcb")

# ---- copper rules (errata #31) -------------------------------------------------
# Stack: F.Cu signal + GND pour / In1 solid GND plane / In2 signal / B.Cu solid GND plane.
# Every trace has a solid plane 0.21 mm away (F.Cu over In1, In2 over B.Cu), the inner
# signal layer is buried between the two planes, and nothing is routed on the bottom.
PLANE_CLEAR = 0.2     # plane copper to foreign copper on In1 / B.Cu. With the unused inner pads removed the
                      # opening around a foreign pin is hole + 2 x 0.35 mm, so a 0.8 mm DIP hole leaves a
                      # 1.0 mm web between 2.54 mm pins. (At KiCad's default 0.5 mm the openings of every pin
                      # row merged into one slot -- 15 mm long under the TL074.)
POUR_CLEAR = 0.5      # top pour to any trace or pad (the .kicad_dru asks 1.0 mm from HiZ nets): > 2 x the
                      # 0.21 mm to the plane, so the plane sets a trace's capacitance, not the pour beside it
POUR_MIN_W = 0.4      # no pour sliver narrower than this
FENCE_PITCH = 5.0     # perimeter ground vias (lambda/10 at 2.9 GHz in FR4)
FENCE_INSET = 2.5     # just inside the 2 mm no-route frame along the board edge

# silkscreen label geometry (see the silkscreen section below)
LBL_H, LBL_W, LBL_T = 1.0, 0.65, 0.15
LBL_OFF = 0.95             # label centre above the part's top edge: the baseline clears it by 0.45 mm,
                           # the underscores in "R_rec_bias" (0.25 mm below the baseline) by 0.2 mm
STRIP = LBL_OFF + 0.6      # label strip height: up to the top of the capitals
LBL_CLEAR = 0.4            # clear silk between a label and the next part's courtyard
STRIP_CELL = STRIP         # height the strip ADDS to the placement cell (set in configure(): the
                           # label shares the part gap, so only STRIP - (GAP - LBL_CLEAR) is extra)

# Board parameters per build profile (see gen_kicad.set_profile):
#   tht -- the primary all-through-hole board, 190 x 115 (original 25-5274-2, errata #9)
#   smd -- the mixed SMD/THT variant, sized for the Part 7 155 x 90 "safe-bet" chassis
PROFILES = {
  # MARGIN: Part 4/5 ask 10 mm all round on the 190x115 board (chassis bracket); the
  # small-chassis SMD board keeps 6 mm (M3 holes at 5 mm inset still clear).
  # TOP_POUR: the SMD board also gets a GND pour on F.Cu (SMD ground pads have no
  # through-hole to reach the bottom pour; two pours + the THT GND pads stitching
  # them is the normal 2-layer SMD arrangement). The THT board keeps top = signal only.
  # GAP: 1.6 / 0.5 mm since the footprint keepouts (errata #24) -- traces now go AROUND parts,
  # so the gaps between them are the routing channels.
  # LAYERS: both boards are 4-layer (2026-09-08): F.Cu signal / In1 solid GND plane /
  # In2 +17V plane / B.Cu signal + GND pour. Every outer-layer trace then sits 0.21 mm
  # over a plane (JLC 7628 prepreg) instead of 1.5 mm: ~10x less trace-to-trace
  # coupling, a real RF/EMI reference, and the router no longer has to thread between
  # pins. Set LAYERS=2 to get the old two-layer boards back (TOP_POUR then applies).
  # LBL_CLEAR 0.05 on the THT board: its 1.6 mm part gap is exactly one label strip, so the
  # silkscreen labels cost no board area there (the SMD board keeps 0.4 mm of clear silk).
  # GAP 1.5 / ZONE_GAP 3.0 / BOT_GAP 4.0 (were 1.6 / 3.5 / 4.5) since the axial VTL5C1 footprint
  # (2026-11): with the old numbers the narrowest fitting columns needed 167 mm of 159.5.
  "tht": dict(BW=190.0, BH=115.0, GAP=1.5, MARGIN=10.0, ZONE_GAP=3.0, BOT_GAP=4.0, TOP_POUR=True,  LAYERS=4, OUT="cambridge_reverb.kicad_pcb",     SUBDIR="", LBL_CLEAR=0.05),
  # SMD board 170x100 since the 4-layer / keepout regime (was 155x90, Part 7's "safe bet"):
  # at a 0.5 mm part gap no via fits next to an SMD ground or rail pad, and 30 of 52 open
  # links were exactly those. 170x100 still fits any chassis the 190x115 original did.
  # 170x105 since the silkscreen labels, the axial VTL5C1 footprint and JP_BR (2026-11): at
  # 170x100 the narrowest fitting columns added up to 146.7 mm of 146.6 mm available.
  "smd": dict(BW=170.0, BH=105.0, GAP=1.2, MARGIN=6.0,  ZONE_GAP=3.0, BOT_GAP=3.0, TOP_POUR=True,  LAYERS=4, OUT="cambridge_reverb_smd.kicad_pcb", SUBDIR="smd"),
}
PROFILE = "tht"
MARGIN = 10.0              # (set per profile in configure())
ZONE_GAP = 4.0             # empty channel between columns (routing room)
ZONE_VGAP = 2.0            # gap between zones stacked in one column
def configure(profile):
    """Select the build profile: board size, margins, part gap, output path (+ gen_kicad's footprint map)."""
    global PROFILE, BW, BH, GAP, MARGIN, ZONE_GAP, EDGE_Y, MAIN_TOP, MAIN_BOT, OUT, TOP_POUR, LAYERS, STRIP_CELL
    PROFILE = profile; P = PROFILES[profile]
    BW, BH, GAP, MARGIN, ZONE_GAP, LAYERS = P["BW"], P["BH"], P["GAP"], P["MARGIN"], P["ZONE_GAP"], P["LAYERS"]
    STRIP_CELL = max(0.0, STRIP - (GAP - P.get("LBL_CLEAR", LBL_CLEAR)))
    TOP_POUR = P["TOP_POUR"]        # SMD board: F.Cu GND pour connects the SMD ground pads solid (plus a via each from the router)
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
             "JP_BR": 5,                   # the no-centre-tap link: two power pads right beside the transformer pads
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
SHEET_OVERRIDE = {"R_fs_mrb": "Reverb",
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

# ---- silkscreen -----------------------------------------------------------------
# Every part carries its reference on F.SilkS (JLCPCB legend minimum: 1.0 mm high,
# 0.15 mm stroke; the glyphs are set 0.65 mm wide so "R_rec_bias" is 6 mm, not 9).
# Small parts RESERVE a label strip above themselves in the placer (bbox_mm), so a
# label never lands on a pad, on a neighbour or under a part -- and the strip is free
# copper: an extra routing channel between every two rows. Big parts carry the label
# inside their outline; the heat-sinked TO-220s carry it below (the tab side is the
# board edge / heatsink).
LBL = {}                   # ref -> (mode, label width mm): "above" | "below" | "inside" | "edge" | None
BOARD_ID = {"tht": "VOX CAMBRIDGE REVERB  25-5274-2 REBUILD  THT  REV B  2026-11",
            "smd": "VOX CAMBRIDGE REVERB  25-5274-2 REBUILD  SMD/THT  REV B  2026-11"}
# off-board wiring pads: what each pad is FOR (printed next to it), pad number -> label.
# Pots: lug 1 = CCW end, 2 = wiper, 3 = CW end (clockwise = more on every control).
POT_PADS = {"1": "CCW", "2": "W", "3": "CW"}
PAD_LABELS = {
  "J_IN1": {"1": "T", "2": "S"}, "J_IN2": {"1": "T", "2": "S"}, "J_IN3": {"1": "T", "2": "S"},
  "POT_VOL": POT_PADS, "POT_BASS": POT_PADS, "POT_TREB": POT_PADS, "POT_REV": POT_PADS,
  "POT_DPT": POT_PADS, "POT_SPD_A": POT_PADS, "POT_SPD_B": POT_PADS,
  "SW_MID": {"1": "A", "2": "B"},
  "REV1": {"1": "IN", "2": "G", "3": "OUT", "4": "G"},
  "FS1": {"1": "REV", "2": "TRM", "3": "MRB", "4": "G", "5": "G", "6": "G"},
  "LS1": {"1": "+", "2": "-"},
  "T1": {"1": "AC", "2": "CT", "3": "AC"},
  "JP_BR": {"1": "NO CT", "2": "ONLY"},      # read together: fit the link for a transformer with NO centre tap ONLY
}
# a second silk line under a part where the reference alone is not enough
NOTE = {"F1": "T1A 250V"}
LEFT_LABEL = 2.4           # extra room right of the left-edge jack pads for their labels (SMD board)

def label_mode(fp, c):
    ref = c["ref"]; name = c["fp"].split(":")[-1]
    if c["libsym"] == "TP":
        return None                                   # the VALUE (net alias) is the silk label
    if ref in EDGE_ZONE:
        return "edge"
    if ref in HEATSINK:
        return "below"
    if name.startswith(("DIP-", "Fuseholder", "R_Axial_Power", "Inductor_MRB")) or "_Horizontal" in name and name.startswith("R_Axial_DIN0414"):
        return "inside"
    return "above"

def style_ref(fp, c):
    """Reference text: front silk, JLC-legal size, visible. Returns (mode, label width)."""
    t = fp.Reference()
    t.SetLayer(pcbnew.F_SilkS); t.SetVisible(True); t.SetKeepUpright(True)
    t.SetTextSize(pcbnew.VECTOR2I(mm(LBL_W), mm(LBL_H))); t.SetTextThickness(mm(LBL_T))
    t.SetItalic(False); t.SetBold(False)
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetTextAngleDegrees(0)
    mode = label_mode(fp, c)
    if mode is None:
        t.SetVisible(False)
    bb = t.GetBoundingBox()
    return mode, pcbnew.ToMM(bb.GetWidth())

def silk_text(board_or_fp, board, text, x, y, angle=0, h=LBL_H, w=LBL_W, layer=None, mirror=False):
    t = pcbnew.PCB_TEXT(board_or_fp)
    t.SetText(text); t.SetLayer(pcbnew.F_SilkS if layer is None else layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(w), mm(h))); t.SetTextThickness(mm(LBL_T))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetPosition(V(x, y)); t.SetTextAngleDegrees(angle); t.SetMirrored(mirror)
    board_or_fp.Add(t)
    return t

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
    lib, item = c["fp"].split(":")
    fp.SetFPID(pcbnew.LIB_ID(lib, item))     # keep the library link ("Lib:Name"), as the schematic's Footprint field has it
    fp.SetReference(c["ref"]); fp.SetValue(c["value"])
    if "(opt)" in c["value"]:                # optional MRB caps: on the board, not fitted
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP)   # -> excluded from the JLC position file
    if hide_text:
        fp.Value().SetVisible(False)
    LBL[c["ref"]] = style_ref(fp, c)
    if c["libsym"] == "TP":                      # the value IS the silk label (net alias)
        fp.Value().SetVisible(True)
    fp.SetPosition(V(x, y))
    if rot:
        fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        net = c["nets"].get(pad.GetNumber())
        if net and net in netmap:
            pad.SetNet(netmap[net])
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and LAYERS == 4:
            # no pad copper on an inner layer unless something connects there: the plane's
            # opening around this pin is then set by the hole (errata #31)
            pad.SetRemoveUnconnected(True); pad.SetKeepTopBottom(True)
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
    """layer=None: the bottom layer. On a 4-layer board that is a solid GND PLANE (named
    plane_GND_B: no tracks are routed on it) -- the reference for the In2 traces 0.21 mm
    above it and the board's shield towards the chassis. layer=F.Cu: the top GND pour
    around the component-side traces."""
    if "GND" not in netmap:
        return
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu if layer is None else layer)
    zone.SetNetCode(netmap["GND"].GetNetCode())
    zone.SetAssignedPriority(0)
    if layer == pcbnew.F_Cu:
        # top pour: copper for the SMD ground pads (they carry a SOLID per-pad
        # override) and shielding; it does NOT put thermal spokes on the through-
        # hole pads -- those ground through the In1 plane
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_NONE)
        zone.SetZoneName("pour_GND_F")
        zone.SetLocalClearance(mm(POUR_CLEAR)); zone.SetMinThickness(mm(POUR_MIN_W))
    elif LAYERS == 4:
        # bottom PLANE: the In1 plane grounds every through-hole pad (thermal reliefs there);
        # this one makes no pad connections, so the solder side of a ground pin is an
        # ordinary pad to solder -- the two planes are tied by the stitching vias
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_NONE)
        zone.SetZoneName("plane_GND_B")
        zone.SetLocalClearance(mm(PLANE_CLEAR))
    sps = zone.Outline(); sps.NewOutline()
    for (px, py) in [(0.5, 0.5), (w - 0.5, 0.5), (w - 0.5, h - 0.5), (0.5, h - 0.5)]:
        sps.Append(mm(px), mm(py))
    zone.SetIsFilled(True)
    board.Add(zone)

IN2_PLANE = None    # "+17V" to make In2 a +17 V plane; None = In2 is the inner SIGNAL layer

def planes(board, netmap, w, h):
    """In1 = solid GND plane, the reference for every F.Cu trace. (In2 is the inner signal
    layer; its reference is the B.Cu plane, see gnd_pour.) Through-hole ground pads connect
    with thermal reliefs; SMD ground pads get a via (stitch.fanout)."""
    for layer, net in ((pcbnew.In1_Cu, "GND"), (pcbnew.In2_Cu, IN2_PLANE)):
        if not net or net not in netmap:
            continue
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNetCode(netmap[net].GetNetCode())
        zone.SetAssignedPriority(0)
        zone.SetZoneName(f"plane_{net}")
        zone.SetLocalClearance(mm(PLANE_CLEAR))
        sps = zone.Outline(); sps.NewOutline()
        for (px, py) in [(0.5, 0.5), (w - 0.5, 0.5), (w - 0.5, h - 0.5), (0.5, h - 0.5)]:
            sps.Append(mm(px), mm(py))
        zone.SetIsFilled(True)
        board.Add(zone)

def stitching_vias(board, netmap, w, h, pitch=FENCE_PITCH, inset=FENCE_INSET):
    """The ground FENCE: GND vias around the perimeter every 5 mm (Part 4 asked 15), tying
    the top pour and the two planes together along the board edge so the edge of the
    plane pair is closed. Skips the corner holes, the wiring-edge pads and the SMD
    board's left-edge jack pads."""
    if "GND" not in netmap:
        return 0
    pads = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y), pcbnew.ToMM(max(p.GetSize().x, p.GetSize().y)) / 2)
            for fp in board.GetFootprints() for p in fp.Pads()]
    holes = [(5.0, 5.0), (w - 5.0, 5.0), (5.0, h - 5.0), (w - 5.0, h - 5.0)]
    pts = []
    n_x = max(1, int((w - 2 * inset) // pitch)); n_y = max(1, int((h - 2 * inset) // pitch))
    for i in range(n_x + 1):
        x = inset + (w - 2 * inset) * i / n_x
        pts += [(x, inset), (x, h - inset)]
    for j in range(1, n_y):
        y = inset + (h - 2 * inset) * j / n_y
        pts += [(inset, y), (w - inset, y)]
    n = 0
    for x, y in pts:
        if any(math.dist((x, y), hc) < 5.0 for hc in holes):
            continue
        if any(math.dist((x, y), (px, py)) < pr + 1.6 for px, py, pr in pads):
            continue
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y)); v.SetDrill(mm(0.4)); v.SetWidth(mm(0.8))
        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(netmap["GND"].GetNetCode()); v.SetLocked(True)
        v.SetRemoveUnconnected(True); v.SetKeepStartEnd(True)
        board.Add(v); n += 1
    return n

def _merged_intervals(iv, min_gap=0.0):
    iv = sorted(iv); out = []
    for a, b in iv:
        if out and a <= out[-1][1] + min_gap:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out

def footprint_keepouts(board, min_gap=0.5):
    """'No routes through footprints': for every real part, rule areas (tracks disallowed,
    vias too under SMD parts; component side F.Cu) covering the space BETWEEN its pads -- the strips between
    the pins of a row and the body between two rows -- across the full courtyard. A
    trace can still reach any pad from the outside; it can no longer sneak between the
    legs of a resistor, under a DIP, or through the toroid. The router sees them as
    Specctra keepouts, KiCad DRC checks them afterwards."""
    # power-only parts (every pad on a HighCurrent / Power / GND net: the bridge, filter
    # cans, output cap, clamp diodes, transformer and speaker pads ...) are exempt: the
    # 1.5 mm rail traces have to pass somewhere, and a rail under a rail part is not the
    # noise path this rule exists for
    import json
    pro = json.load(open(os.path.join(REPO_KI, "cambridge_reverb.kicad_pro")))
    power_nets = {p["pattern"] for p in pro["net_settings"]["netclass_patterns"]
                  if p["netclass"] in ("HighCurrent", "Power")} | {"GND"}
    n = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith(("TP", "FID", "H")) or fp.GetFPIDAsString().startswith("MountingHole"):
            continue
        pads = list(fp.Pads())
        if len(pads) < 2:
            continue
        if all(p.GetNetname() in power_nets for p in pads):
            continue
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False)
        X0, Y0, X1, Y1 = (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
        pbs = [p.GetBoundingBox() for p in pads]
        pinfo = [(pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetBottom()), p.GetNetname())
                 for p, b in zip(pads, pbs)]
        xs = _merged_intervals([(l, r) for l, r, _, _, _ in pinfo])
        ys = _merged_intervals([(t, b) for _, _, t, b, _ in pinfo])
        multirow = len(ys) > 1                       # DIP / two-row parts: the body rect below covers the middle
        rects = []
        for (a0, a1), (b0, b1) in zip(xs, xs[1:]):
            if b0 - a1 < min_gap:
                continue
            left = [q for q in pinfo if q[1] <= a1 + 1e-6 and q[1] > a0 - 1e-6]
            right = [q for q in pinfo if q[0] >= b0 - 1e-6 and q[0] < b1 + 1e-6]
            # adjacent pins that share a net (a unity buffer's out/-in, a pot's wiper tied to
            # its end) need the tiny link between them: no strip there, per row
            rows = {}
            for q in left + right:
                rows.setdefault(round((q[2] + q[3]) / 2, 1), set()).add(q[4])
            if multirow:
                for yc, nets in rows.items():
                    if len(nets) > 1:
                        band = [q for q in left + right if round((q[2] + q[3]) / 2, 1) == yc]
                        y0 = min(q[2] for q in band) - 0.3; y1 = max(q[3] for q in band) + 0.3
                        rects.append((a1, max(Y0, y0), b0, min(Y1, y1)))   # pin-row band only
            else:
                if any(len(n) > 1 for n in rows.values()) or len(set(q[4] for q in left + right)) > 1:
                    rects.append((a1, Y0, b0, Y1))                          # full courtyard height
        for (a0, a1), (b0, b1) in zip(ys, ys[1:]):
            if b0 - a1 >= min_gap: rects.append((X0, a1, X1, b0))
        # vias: forbidden under SMD parts (assembly), allowed under through-hole parts -- a via
        # beneath a resistor body is not a route through it, and the inner-layer runs need a
        # way up to the pads (without this a third of the links stayed open)
        smd_part = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in pads)
        for x0, y0, x1, y1 in rects:
            z = pcbnew.ZONE(board)
            z.SetIsRuleArea(True); z.SetZoneName(f"kp_{ref}")
            z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(smd_part)
            z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
            # component side only: a B.Cu trace under a part has the whole board and the In1
            # GND plane between itself and the part (and In2 is under the plane too). With
            # the keepouts on both outer layers the router left a third of the links open.
            ls = pcbnew.LSET(); ls.addLayer(pcbnew.F_Cu)
            z.SetLayerSet(ls)
            sps = z.Outline(); sps.NewOutline()
            for px, py in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
                sps.Append(mm(px), mm(py))
            board.Add(z); n += 1
    return n

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
    Two sit in the top margin between the corner holes' courtyards and the first row of
    parts, the third in the right-hand margin above the corner hole (the wiring edge
    carries the pad labels now) -- all >= 4 mm from the board edge (JLC: >= 3.85 mm)."""
    for i, (x, y) in enumerate([(12.0, 4.0), (w - 12.0, 4.0), (w - 4.0, h - 16.0)]):
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
def raw_bbox_mm(fp):
    """Text-less bounding box: (w, h, centre offset x, centre offset y) from the anchor."""
    bb = fp.GetBoundingBox(False, False)
    return (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()),
            pcbnew.ToMM(bb.GetCenter().x) - pcbnew.ToMM(fp.GetPosition().x),
            pcbnew.ToMM(bb.GetCenter().y) - pcbnew.ToMM(fp.GetPosition().y))

def bbox_mm(fp):
    """Placement cell = the part plus its silkscreen label strip (above or below it)."""
    w, h, ox, oy = raw_bbox_mm(fp)
    ref = fp.GetReference()
    mode, lw = LBL.get(ref, (None, 0.0))
    # a label ABOVE a part shares the gap to the part above it; anything BELOW a part
    # (heatsink parts' labels, notes) takes its full strip, because the part underneath
    # may push its own label up into that same gap
    top = STRIP_CELL if mode == "above" else 0.0
    bot = STRIP if mode == "below" and ref not in HEATSINK else 0.0   # (a heatsink part's label sits in its own 10 mm keep-out)
    if mode not in ("above", "below"):
        lw = 0.0
    if ref in NOTE:
        bot += STRIP; lw = max(lw, len(NOTE[ref]) * LBL_W)
    return max(w, lw), h + top + bot, ox, oy + (bot - top) / 2

def place_labels(board, fps):
    """Put every reference where its mode says, after the final placement."""
    for ref, (c, fp) in fps.items():
        mode, lw = LBL.get(ref, (None, 0.0))
        if mode in (None, "edge"):
            continue
        t = fp.Reference()
        w, h, ox, oy = raw_bbox_mm(fp)
        cx = pcbnew.ToMM(fp.GetPosition().x) + ox; cy = pcbnew.ToMM(fp.GetPosition().y) + oy
        if mode == "above":
            t.SetPosition(V(cx, cy - h / 2 - LBL_OFF))
        elif mode == "below":
            t.SetPosition(V(cx, cy + h / 2 + STRIP - LBL_OFF + 0.1))
        else:                                   # inside the outline, clear of the pads
            name = c["fp"].split(":")[-1]
            pads = list(fp.Pads())
            pxs = [pcbnew.ToMM(p.GetPosition().x) for p in pads]; pys = [pcbnew.ToMM(p.GetPosition().y) for p in pads]
            mx, my = (min(pxs) + max(pxs)) / 2, (min(pys) + max(pys)) / 2
            if name.startswith("DIP-"):
                t.SetPosition(V(mx, my)); t.SetTextAngleDegrees(90)
            elif name.startswith("Inductor_MRB"):
                t.SetPosition(V(mx, my - 5.0))
            else:                               # fuse clip, 5 W / 1 W resistors: middle of the body
                t.SetPosition(V(mx, my))
        if ref in NOTE:
            below = cy + h / 2 + (STRIP if mode == "below" else 0.0)
            silk_text(fp, board, NOTE[ref], cx, below + STRIP - LBL_OFF + 0.1)

def edge_labels(board, fps, left_refs):
    """Wiring pads: the connector's reference plus what every pad is for. Bottom-edge
    groups: pad labels (vertical) under the pads, the reference under those. Left-edge
    jack groups (SMD board): pad labels to the right of the pads, the reference
    vertical beside them."""
    for ref, labels in PAD_LABELS.items():
        if ref not in fps:
            continue
        c, fp = fps[ref]; t = fp.Reference()
        pads = sorted(fp.Pads(), key=lambda p: p.GetNumber())
        xs = [pcbnew.ToMM(p.GetPosition().x) for p in pads]; ys = [pcbnew.ToMM(p.GetPosition().y) for p in pads]
        half = max(pcbnew.ToMM(max(p.GetSize().x, p.GetSize().y)) for p in pads) / 2 + 0.75   # pad + its silk frame
        if ref in left_refs:
            x0 = max(xs) + half
            for p in pads:
                silk_text(fp, board, labels[p.GetNumber()], x0 + 0.45, pcbnew.ToMM(p.GetPosition().y))
            t.SetPosition(V(x0 + 1.55, (min(ys) + max(ys)) / 2)); t.SetTextAngleDegrees(90)
        else:
            y0 = max(ys) + half
            longest = max((len(v) for v in labels.values()), default=0)
            run = longest * LBL_W * 0.98
            for p in pads:
                silk_text(fp, board, labels[p.GetNumber()], pcbnew.ToMM(p.GetPosition().x), y0 + 0.2 + run / 2, angle=90)
            t.SetPosition(V((min(xs) + max(xs)) / 2, y0 + 0.2 + run + 0.25 + LBL_H / 2))

def board_marks(board, w, h):
    """Board identity on the top silk (in the margin above the stitching-via row) and the
    spot JLCPCB may print its order number on: they replace the text JLCJLCJLCJLC, on the
    bottom silk here, instead of dropping the number somewhere on the top side."""
    silk_text(board, board, BOARD_ID[PROFILE], w / 2, 1.55)
    silk_text(board, board, "JLCJLCJLCJLC", w / 2, h - 1.6, layer=pcbnew.B_SilkS, mirror=True)

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
    board.GetDesignSettings().SetCopperLayerCount(LAYERS)
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
        h = raw_bbox_mm(fp)[1]
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
    X0 = MARGIN + (LEFT_LABEL if LEFT_EDGE.get(PROFILE) else 0.0)     # first column starts right of the jack labels
    total_w = BW - MARGIN - X0 - ZONE_GAP * (ncol - 1)
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
    # Column widths: shelf packing makes a column's height a STEP function of its width
    # (and not even a monotonic one), so instead of iterating towards a balance the
    # height of every column is tabulated over every width it could have (0.25 mm steps)
    # and the widths are read off: the smallest common height H at which the narrowest
    # fitting widths still add up to the board. A weighted column (ZONE_WEIGHT) is asked
    # to be that much SHORTER, i.e. it gets the extra width. Whatever width is left over
    # goes into the channels between the columns.
    avail = MAIN_BOT - MAIN_TOP
    def col_h(ci, w):
        return pack_column(ci, X0, X0 + w) - MAIN_TOP
    tab = []
    for ci in range(ncol):
        wmax = total_w - (sum(minw) - minw[ci])
        n = int((wmax - minw[ci]) / 0.25) + 1
        tab.append([(minw[ci] + 0.25 * k, col_h(ci, minw[ci] + 0.25 * k)) for k in range(n)])
    def need(ci, H):
        for w, hh in tab[ci]:
            if hh * wt[ci] <= H + 1e-6 and hh <= avail + 1e-6:
                return w
        return None
    widths = None
    for H in sorted({round(hh * wt[ci], 3) for ci in range(ncol) for _, hh in tab[ci]}):
        ws = [need(ci, H) for ci in range(ncol)]
        if None not in ws and sum(ws) <= total_w + 1e-6:
            widths = ws
            break
    narrow = [next((w for w, hh in tab[ci] if hh <= avail + 1e-6), None) for ci in range(ncol)]
    print(f"  narrowest fitting column widths {narrow} = {sum(w for w in narrow if w):.1f} mm of {total_w:.1f} mm available")
    if widths is None:                       # does not fit at all: narrowest widths, report the overflow
        widths = [max(total_w * a / sum(areas), m) for a, m in zip(areas, minw)]
        widths = [w * total_w / sum(widths) for w in widths]
    ZG = ZONE_GAP + max(0.0, total_w - sum(widths)) / max(ncol - 1, 1)

    # final placement, plus the wiring-edge connector row (one global cursor so
    # neighbouring groups never collide; T1 pinned to the far right)
    x = X0; util = []
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
        x = x1 + ZG

    # left-edge column (SMD board): pad groups stacked top -> bottom below the
    # corner hole's courtyard, centred in the margin, GAP clear of the first column
    ly = 5.0 + 3.5 + GAP                 # M3 hole at 5 mm inset, 3.45 mm courtyard radius
    for c, fp in left_parts:
        w, h = put(fp, 0, 0, 90)
        put(fp, MARGIN - GAP - w / 2, ly + h / 2, 90); ly += h + GAP
    place_labels(board, fps)
    edge_labels(board, fps, left_refs)
    board_marks(board, BW, BH)

    outline(board, BW, BH)
    mounting_holes(board, BW, BH)
    keepouts(board, BW, BH)
    nkp = footprint_keepouts(board)
    if PROFILE == "smd":                      # the assembled board: JLCPCB fiducials
        fiducials(board, BW, BH)
    stubs = escape_stubs(board, fps)
    gnd_pour(board, netmap, BW, BH)           # B.Cu: solid GND plane (4-layer) -- nothing is routed on it
    if TOP_POUR:
        gnd_pour(board, netmap, BW, BH, layer=pcbnew.F_Cu)
    nst = nfo = 0
    if LAYERS == 4:
        planes(board, netmap, BW, BH)
        nst = stitching_vias(board, netmap, BW, BH)
        import stitch
        nfo = stitch.fanout(board, OUT)       # every SMD ground pad: a locked via to the planes, before the router runs
    pcbnew.SaveBoard(OUT, board)
    # fill with the project's rules: reload (so every net has its class) and let
    # route_board.refill() initialise the rule engine before the filler runs
    from route_board import refill
    board = pcbnew.LoadBoard(OUT)
    refill(board)
    pcbnew.SaveBoard(OUT, board)
    print(f"  {LAYERS} copper layers (F.Cu signal + pour / In1 GND / In2 signal / B.Cu GND); {nkp} footprint keepout areas; "
          f"{nst} perimeter fence vias; {nfo} SMD ground pads fanned out to the planes")

    # chassis-fit packing-density check (bounding boxes, as before)
    areas_all = [raw_bbox_mm(fp)[0] * raw_bbox_mm(fp)[1] for _, fp in fps.values()]
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
    global LAYERS
    saved, LAYERS = LAYERS, 2                 # the demo is a plain two-layer board: its bottom pour IS the ground connection
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
    LAYERS = saved
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
