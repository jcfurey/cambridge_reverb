#!/usr/bin/env python3
"""Close the connections the autorouter left open -- a small grid maze router that knows
this project's rules exactly.

Freerouting gets every net class as ONE clearance and ONE width, so two kinds of link
stay open on every run:

  * signal-level branches of a power net -- PA_OUT to the feedback parts (R_fb, C_fb_hf),
    +33V5 to the bias divider: a 1.5 mm trace with 0.4 mm of clearance does not fit
    between 0805 pads, although those branches carry microamps;
  * the reverb tank drive: its 0.6 / 0.8 mm separation is only required from the tank
    RETURN nets (the .kicad_dru rule), but the router has to keep it from everything.

This script routes exactly those leftovers on a 0.1 mm grid (A*, 45-degree moves, through
vias) with the real rules: per-pair clearances as the .kicad_dru states them, the
footprint / edge / hole keepouts, hole-to-hole spacing, no via on an SMD pad or next to
a ground pin's thermal relief -- and a necked-down width where a branch only feeds a
resistor, a small capacitor or a test point. KiCad's own DRC is the judge afterwards
(kicad/gen/check.sh <profile> --no-regen).

    python3 kicad/gen/finish_routes.py --in kicad/smd/cambridge_reverb_smd.kicad_pcb

Run it in place (next to the .kicad_pro / .kicad_dru), after route_board.py.
"""
import sys, os, re, json, math, heapq, argparse, subprocess, tempfile
import numpy as np
from scipy import ndimage
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from route_board import CLASS_CLEARANCE_UM, prune_zero_length

RES = 0.1                     # grid pitch, mm
SAFETY = 0.08                 # added to every clearance: grid quantisation + 45-degree corners
PAINT = RES / 2               # shapes are painted this much fat, so a cell centre just outside one still counts
VIA_EXTRA = 0.1               # vias keep this much more than tracks
ROUTE_LAYERS = ["F.Cu", "In2.Cu", "B.Cu"]          # In1 is the GND plane
LAYER_COST = {"F.Cu": 1.0, "In2.Cu": 1.0, "B.Cu": 1.15}
VIA_COST = 400                # in units of 0.01 mm of track (a via ~ 4 mm of detour)
EDGE_CLEAR = 1.0              # copper stays this far inside the board outline, all layers
TANK_RETURN = {"TANK_OUT", "RF2", "QRG", "WET", "DRVP"}
# a branch that ends on one of these carries signal current only -> may be necked down ...
def light_ref(ref):
    return (ref.startswith(("TP_", "R_")) and ref not in ("R_spk_rtn", "R_zobel")) or ref in ("C_fb_hf", "C_bref")
# ... unless its other end is one of the parts that carry the amps (then the link may be
# the ONLY copper to that part, however light the pad it happens to land on)
HEAVY = {"IC_PA", "C_out", "D1", "D2", "C_byp1", "C_byp2", "C_main", "F1", "BR1", "T1", "LS1", "R_spk_rtn",
         "R_zobel", "C_zobel", "JP_BR", "C_filt1", "C_filt2"}
NECK_W = 0.5                  # mm, the necked-down width for a signal-level branch (1 oz copper: > 1 A)
RELIEF_W = 0.8                # mm, second try for a rail link that cannot get through at the class width
                              # (narrower than an 0805 pad, so its end cap stays out of the keepout between the pads)

def mm(v): return pcbnew.FromMM(v)
def to_mm(v): return pcbnew.ToMM(v)

class Rules:
    def __init__(self, pcb_path):
        pro = json.load(open(os.path.splitext(pcb_path)[0] + ".kicad_pro"))
        ns = pro["net_settings"]
        self.cls = {c["name"]: c for c in ns["classes"]}
        self.pat = {p["pattern"]: p["netclass"] for p in ns["netclass_patterns"]}
        prof = "smd" if os.sep + "smd" + os.sep in os.path.abspath(pcb_path) else "tht"
        cc = CLASS_CLEARANCE_UM[prof]
        self.hc = cc["HighCurrent"] / 1000.0; self.td = cc["TankDrive"] / 1000.0
        r = pro["board"]["design_settings"]["rules"]
        self.min_clear = r["min_clearance"]; self.hole_clear = r["min_hole_clearance"]; self.hole_hole = r["min_hole_to_hole"]
    def klass(self, net):
        return self.pat.get(net, "Default")
    def width(self, net): return self.cls[self.klass(net)]["track_width"]
    def via(self, net):
        c = self.cls[self.klass(net)]; return c["via_diameter"], c["via_drill"]
    def clearance(self, net, other, other_is_track):
        """Required copper gap between a NEW TRACK / VIA of `net` and an existing item of `other`."""
        k, ko = self.klass(net), self.klass(other)
        c = max(self.cls[k]["clearance"], self.cls[ko]["clearance"], self.min_clear)
        if k == "HighCurrent" and ko in ("Default", "HiZ"): c = max(c, self.hc)
        if ko == "HighCurrent" and k in ("Default", "HiZ") and other_is_track: c = max(c, self.hc)
        if k == "TankDrive" and other in TANK_RETURN: c = max(c, self.td)
        if ko == "TankDrive" and net in TANK_RETURN and other_is_track: c = max(c, self.td)
        return c

class Grid:
    """Rasterised board: exact copper shapes per layer, grouped by owner net."""
    def __init__(self, board, rules):
        self.b = board; self.r = rules
        bb = board.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = to_mm(bb.GetLeft()), to_mm(bb.GetTop())
        self.W = int(round(to_mm(bb.GetWidth()) / RES)) + 1; self.H = int(round(to_mm(bb.GetHeight()) / RES)) + 1
        self.yy, self.xx = np.mgrid[0:self.H, 0:self.W]
        self.collect()
    def cell(self, x, y):
        return int(round((y - self.y0) / RES)), int(round((x - self.x0) / RES))
    def pos(self, iy, ix):
        return self.x0 + ix * RES, self.y0 + iy * RES
    # --- primitive rasterisers: paint cells whose centre is within `grow` of the shape
    def _win(self, xa, ya, xb, yb, grow):
        i0 = max(0, int((min(ya, yb) - grow - self.y0) / RES) - 1); i1 = min(self.H, int((max(ya, yb) + grow - self.y0) / RES) + 3)
        j0 = max(0, int((min(xa, xb) - grow - self.x0) / RES) - 1); j1 = min(self.W, int((max(xa, xb) + grow - self.x0) / RES) + 3)
        if i0 >= i1 or j0 >= j1: return None
        X = self.x0 + self.xx[i0:i1, j0:j1] * RES; Y = self.y0 + self.yy[i0:i1, j0:j1] * RES
        return (slice(i0, i1), slice(j0, j1)), X, Y
    def seg(self, g, xa, ya, xb, yb, r):
        w = self._win(xa, ya, xb, yb, r)
        if w is None: return
        sl, X, Y = w
        dx, dy = xb - xa, yb - ya; L2 = dx * dx + dy * dy
        t = np.clip(((X - xa) * dx + (Y - ya) * dy) / L2, 0, 1) if L2 > 1e-12 else 0.0
        d2 = (X - (xa + t * dx)) ** 2 + (Y - (ya + t * dy)) ** 2
        g[sl] |= d2 <= r * r
    def rect(self, g, cx, cy, hx, hy, grow=0.0):
        w = self._win(cx - hx, cy - hy, cx + hx, cy + hy, grow)
        if w is None: return
        sl, X, Y = w
        ddx = np.maximum(np.abs(X - cx) - hx, 0); ddy = np.maximum(np.abs(Y - cy) - hy, 0)
        g[sl] |= ddx * ddx + ddy * ddy <= grow * grow + 1e-12
    def pad_shape(self, g, p, grow=0.0):
        c = p.GetPosition(); cx, cy = to_mm(c.x), to_mm(c.y)
        sx, sy = to_mm(p.GetSize().x), to_mm(p.GetSize().y)
        if int(round(p.GetOrientationDegrees())) % 180 == 90: sx, sy = sy, sx
        sh = p.GetShape()
        if sh == pcbnew.PAD_SHAPE_CIRCLE:
            self.seg(g, cx, cy, cx, cy, sx / 2 + grow)
        elif sh == pcbnew.PAD_SHAPE_OVAL:
            r = min(sx, sy) / 2
            if sx >= sy: self.seg(g, cx - (sx / 2 - r), cy, cx + (sx / 2 - r), cy, r + grow)
            else:        self.seg(g, cx, cy - (sy / 2 - r), cx, cy + (sy / 2 - r), r + grow)
        else:                                   # rect / roundrect / anything else: its box (conservative)
            self.rect(g, cx, cy, sx / 2, sy / 2, grow)
    def collect(self):
        """Lists of copper items per routing layer: (kind, net, is_track, painter)."""
        b = self.b; self.items = {l: [] for l in ROUTE_LAYERS}; self.holes = []; self.smd_pads = []; self.gnd_tht = []
        lid = {l: b.GetLayerID(l) for l in ROUTE_LAYERS}
        for fp in b.GetFootprints():
            for p in fp.Pads():
                net = p.GetNetname(); ds = p.GetDrillSize(); c = p.GetPosition()
                if ds.x > 0:
                    self.holes.append((to_mm(c.x), to_mm(c.y), to_mm(max(ds.x, ds.y)) / 2))
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    for l in ROUTE_LAYERS:      # bare hole: keep copper 0.5 mm off its edge
                        self.items[l].append(("npth", "", False, lambda g, grow, p=p, c=c, ds=ds: self.seg(g, to_mm(c.x), to_mm(c.y), to_mm(c.x), to_mm(c.y), to_mm(max(ds.x, ds.y)) / 2 + 0.3 + grow)))
                    continue
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    self.smd_pads.append(p)
                elif net == "GND":
                    self.gnd_tht.append(p)
                for l in ROUTE_LAYERS:
                    if p.IsOnLayer(lid[l]):
                        self.items[l].append(("pad", net, False, lambda g, grow, p=p: self.pad_shape(g, p, grow)))
        for t in b.GetTracks():
            net = t.GetNetname()
            if t.GetClass() == "PCB_VIA":
                c = t.GetPosition(); r = to_mm(t.GetWidth()) / 2
                self.holes.append((to_mm(c.x), to_mm(c.y), to_mm(t.GetDrill()) / 2))
                for l in ROUTE_LAYERS:
                    self.items[l].append(("via", net, True, lambda g, grow, c=c, r=r: self.seg(g, to_mm(c.x), to_mm(c.y), to_mm(c.x), to_mm(c.y), r + grow)))
            else:
                l = b.GetLayerName(t.GetLayer())
                if l in self.items:
                    a, e = t.GetStart(), t.GetEnd(); r = to_mm(t.GetWidth()) / 2
                    self.items[l].append(("track", net, True, lambda g, grow, a=a, e=e, r=r: self.seg(g, to_mm(a.x), to_mm(a.y), to_mm(e.x), to_mm(e.y), r + grow)))
        self.keep_track = {l: [] for l in ROUTE_LAYERS}; self.keep_via = []
        for z in b.Zones():
            if not z.GetIsRuleArea(): continue
            bb = z.GetBoundingBox(); cx, cy = to_mm(bb.GetCenter().x), to_mm(bb.GetCenter().y)
            hx, hy = to_mm(bb.GetWidth()) / 2, to_mm(bb.GetHeight()) / 2
            for l in ROUTE_LAYERS:
                if z.IsOnLayer(lid[l]) and z.GetDoNotAllowTracks():
                    self.keep_track[l].append((cx, cy, hx, hy))
            if z.GetDoNotAllowVias():
                self.keep_via.append((cx, cy, hx, hy))
    def blocked(self, net, width):
        """Per layer: cells where a track of `width` on `net` may NOT have its centre line."""
        hw = width / 2; out = {}
        edge = np.ones((self.H, self.W), bool)
        e = int(math.ceil((EDGE_CLEAR + hw) / RES)); edge[e:self.H - e, e:self.W - e] = False
        for l in ROUTE_LAYERS:
            groups = {}
            for kind, onet, is_track, paint in self.items[l]:
                if onet == net and kind != "npth": continue
                c = 0.2 if kind == "npth" else self.r.clearance(net, onet, is_track)
                groups.setdefault(round(c, 3), []).append(paint)
            blk = edge.copy()
            for c, painters in groups.items():
                g = np.zeros((self.H, self.W), bool)
                for paint in painters: paint(g, PAINT)
                d = ndimage.distance_transform_edt(~g) * RES
                blk |= d < (hw + c + SAFETY)
            for cx, cy, hx, hy in self.keep_track[l]:
                self.rect(blk, cx, cy, hx, hy, hw + 0.05)
            out[l] = blk
        return out
    def via_blocked(self, net, blk_by_width):
        """Cells where a via of `net` may NOT be centred."""
        vd, vdr = self.r.via(net); vr = vd / 2
        vb = np.zeros((self.H, self.W), bool)
        viablk = self.blocked(net, vd + 2 * VIA_EXTRA)  # a via is a track of its own diameter, standing still
        for l in ROUTE_LAYERS: vb |= viablk[l]
        g = np.zeros((self.H, self.W), bool)
        for x, y, r in self.holes: self.seg(g, x, y, x, y, r)
        vb |= ndimage.distance_transform_edt(~g) * RES < (vdr / 2 + self.r.hole_hole + SAFETY)
        for cx, cy, hx, hy in self.keep_via: self.rect(vb, cx, cy, hx, hy, vr + 0.05)
        g = np.zeros((self.H, self.W), bool)
        for p in self.smd_pads: self.pad_shape(g, p)    # no via in / on an SMD pad (any net)
        vb |= ndimage.distance_transform_edt(~g) * RES < (vr + 0.2)
        g = np.zeros((self.H, self.W), bool)
        for p in self.gnd_tht: self.pad_shape(g, p)     # keep the In1 plane's thermal spokes whole
        vb |= ndimage.distance_transform_edt(~g) * RES < (vr + 1.0)
        return vb

def astar(grid, blk, vb, src, src_layers, dst, dst_layers, max_nodes=3_000_000):
    """src/dst: SETS of (iy, ix) cells (a pad centre, or every cell on a track's centre
    line). Returns [(layer, iy, ix), ...] from a source cell to a target cell, or None."""
    L = ROUTE_LAYERS; H, W = grid.H, grid.W
    y0 = min(c[0] for c in dst); y1 = max(c[0] for c in dst); x0 = min(c[1] for c in dst); x1 = max(c[1] for c in dst)
    def h(iy, ix):                               # octile distance to the target's bounding box (admissible)
        dy = max(y0 - iy, 0, iy - y1); dx = max(x0 - ix, 0, ix - x1)
        return 10 * max(dy, dx) + 4 * min(dy, dx)
    openq = []; best = {}; came = {}
    for l in src_layers:
        for c in src:
            s = (L.index(l), c[0], c[1]); best[s] = 0; heapq.heappush(openq, (h(c[0], c[1]), 0, s))
    dl = {L.index(l) for l in dst_layers}
    own = src | dst                              # the two items being joined are never obstacles to themselves
    free = lambda li, iy, ix: not blk[L[li]][iy, ix] or (iy, ix) in own
    n = 0
    while openq:
        f, gc, s = heapq.heappop(openq)
        if gc > best.get(s, 1e18): continue
        if s[0] in dl and (s[1], s[2]) in dst:
            path = [s]
            while s in came: s = came[s]; path.append(s)
            return [(L[a], b, c) for a, b, c in reversed(path)]
        n += 1
        if n > max_nodes: return None
        li, iy, ix = s; lc = LAYER_COST[L[li]]
        for dy, dx, c in ((1, 0, 10), (-1, 0, 10), (0, 1, 10), (0, -1, 10), (1, 1, 14), (1, -1, 14), (-1, 1, 14), (-1, -1, 14)):
            y, x = iy + dy, ix + dx
            if not (0 <= y < H and 0 <= x < W) or not free(li, y, x): continue
            if dy and dx and not (free(li, iy + dy, ix) and free(li, iy, ix + dx)): continue   # no corner cutting
            t = (li, y, x); ng = gc + c * lc
            if ng < best.get(t, 1e18):
                best[t] = ng; came[t] = s; heapq.heappush(openq, (ng + h(y, x), ng, t))
        if not vb[iy, ix]:
            for lj in range(len(L)):
                if lj == li or blk[L[lj]][iy, ix]: continue
                t = (lj, iy, ix); ng = gc + VIA_COST
                if ng < best.get(t, 1e18):
                    best[t] = ng; came[t] = s; heapq.heappush(openq, (ng + h(iy, ix), ng, t))
    return None

def item_layers(desc):
    m = re.search(r" on ((?:F|B|In\d)\.Cu)", desc)
    if desc.startswith("PTH pad") or desc.startswith("Via") or not m:
        return list(ROUTE_LAYERS)
    return [m.group(1)] if m.group(1) in ROUTE_LAYERS else list(ROUTE_LAYERS)
def item_ref(desc):
    m = re.search(r" of (\S+)", desc)
    return m.group(1) if m else ""
def item_net(desc):
    return re.search(r"\[([^\]]+)\]", desc).group(1)

def endpoint(board, grid, net, desc, pos):
    """The copper a ratsnest end sits on: a pad / via centre, or a whole track (any point
    of its centre line is as good as its end). Returns (cells, layers, end_point(iy, ix))."""
    layers = item_layers(desc)
    if desc.startswith("Track"):
        lid = board.GetLayerID(layers[0])
        for t in board.GetTracks():
            if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net or t.GetLayer() != lid: continue
            a, e = t.GetStart(), t.GetEnd(); ax, ay, ex, ey = to_mm(a.x), to_mm(a.y), to_mm(e.x), to_mm(e.y)
            if min(math.dist(pos, (ax, ay)), math.dist(pos, (ex, ey))) > 0.01: continue
            n = max(1, int(math.dist((ax, ay), (ex, ey)) / (RES / 2)))
            cells = {grid.cell(ax + (ex - ax) * k / n, ay + (ey - ay) * k / n) for k in range(n + 1)}
            # join at the grid cell itself: it is within 0.07 mm of the centre line, i.e. inside
            # the track, and no 0.1 mm stub is needed to reach an "exact" point
            return cells, layers, lambda iy, ix: grid.pos(iy, ix)
    return {grid.cell(*pos)}, layers, lambda iy, ix: pos        # a pad / via: end exactly on its centre

def unconnected(pcb):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f: tmp = f.name
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", tmp, pcb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(tmp)); os.remove(tmp)
    out = []
    for u in d.get("unconnected_items", []):
        a, b = u["items"][0], u["items"][1]
        out.append(dict(net=item_net(a["description"]), a=(a["pos"]["x"], a["pos"]["y"]), b=(b["pos"]["x"], b["pos"]["y"]),
                        la=item_layers(a["description"]), lb=item_layers(b["description"]),
                        ra=item_ref(a["description"]), rb=item_ref(b["description"]), da=a["description"], db=b["description"]))
    errors = [v for v in d.get("violations", []) if v["severity"] == "error"]
    unconnected.dangling = [(v["items"][0]["pos"]["x"], v["items"][0]["pos"]["y"]) for v in d.get("violations", []) if v["type"] == "track_dangling"]
    return out, errors

def clean_stubs(pcb):
    """KiCad's dangling-end test counts a segment shorter than its own width as connected
    at one end only (both ends touch the same neighbours) and reports the other end. Such
    a stub lies inside the copper it joins, so it is redundant: delete it, and keep the
    deletion only if nothing came apart."""
    todo, _ = unconnected(pcb)
    removed = 0
    for x, y in list(unconnected.dangling):
        board = pcbnew.LoadBoard(pcb)
        hit = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and not t.IsLocked() and to_mm(t.GetLength()) < to_mm(t.GetWidth())
               and min(math.dist((x, y), (to_mm(t.GetStart().x), to_mm(t.GetStart().y))), math.dist((x, y), (to_mm(t.GetEnd().x), to_mm(t.GetEnd().y)))) < 0.01]
        if not hit:
            continue
        keep = open(pcb, "rb").read()
        board.Delete(hit[0]); pcbnew.ZONE_FILLER(board).Fill(board.Zones()); pcbnew.SaveBoard(pcb, board)
        after, errs = unconnected(pcb)
        if len(after) > len(todo) or errs:
            open(pcb, "wb").write(keep)                 # it mattered after all: put it back
        else:
            removed += 1
    return removed

def add_path(board, grid, rules, net, width, path, a_xy, b_xy):
    """Path cells -> tracks and vias. a_xy / b_xy are the end points: a pad's exact
    centre, or the grid cell on a track's centre line."""
    code = board.FindNet(net).GetNetCode(); vd, vdr = rules.via(net)
    pts = [(l,) + grid.pos(iy, ix) for l, iy, ix in path]
    pts[0] = (pts[0][0], a_xy[0], a_xy[1]); pts[-1] = (pts[-1][0], b_xy[0], b_xy[1])
    nseg = nvia = 0; i = 0
    while i < len(pts) - 1:
        l, x, y = pts[i]
        if pts[i + 1][0] != l:                     # layer change: a through via here
            v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            v.SetWidth(mm(vd)); v.SetDrill(mm(vdr)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(code); board.Add(v); nvia += 1; i += 1
            continue
        j = i + 1                                   # extend while collinear on this layer
        while (j + 1 < len(pts) and pts[j + 1][0] == l and
               abs((pts[j][1] - x) * (pts[j + 1][2] - pts[j][2]) - (pts[j][2] - y) * (pts[j + 1][1] - pts[j][1])) < 1e-9):
            j += 1
        t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetEnd(pcbnew.VECTOR2I(mm(pts[j][1]), mm(pts[j][2])))
        t.SetWidth(mm(width)); t.SetLayer(board.GetLayerID(l)); t.SetNetCode(code); board.Add(t); nseg += 1
        i = j
    return nseg, nvia

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--rounds", type=int, default=4)
    a = ap.parse_args()
    rules = Rules(a.src)
    for rnd in range(a.rounds):
        todo, errors = unconnected(a.src)
        print(f"round {rnd + 1}: {len(todo)} open connection(s), {len(errors)} DRC error(s)")
        if not todo:
            break
        board = pcbnew.LoadBoard(a.src)
        done = 0
        for u in todo:
            net = u["net"]
            if net == "GND":
                print(f"  GND {u['da'][:40]} <-> {u['db'][:40]}: not handled here (the plane connects ground)"); continue
            widths = [rules.width(net)]
            if widths[0] > RELIEF_W:
                widths.append(RELIEF_W)
            if (light_ref(u["ra"]) or light_ref(u["rb"])) and not ({u["ra"], u["rb"]} & HEAVY) and widths[0] > NECK_W:
                widths.append(NECK_W)
            routed = False
            for w in widths:
                grid = Grid(board, rules)                    # re-read the board: earlier links are obstacles now
                blk = grid.blocked(net, w); vb = grid.via_blocked(net, blk)
                ca, la, xa = endpoint(board, grid, net, u["da"], u["a"])
                cb, lb, xb = endpoint(board, grid, net, u["db"], u["b"])
                path = astar(grid, blk, vb, ca, la, cb, lb)
                if path:
                    ns, nv = add_path(board, grid, rules, net, w, path, xa(*path[0][1:]), xb(*path[-1][1:]))
                    length = sum(math.dist(grid.pos(p[1], p[2]), grid.pos(q[1], q[2])) for p, q in zip(path, path[1:]))
                    note = "" if w == widths[0] else (f"  (necked down from {widths[0]} mm: signal-level branch)" if w == NECK_W
                                                      else f"  (reduced from {widths[0]} mm: no room at the class width)")
                    print(f"  {net:10s} {u['ra'] or 'track':10s} <-> {u['rb'] or 'track':10s} {length:5.1f} mm, {w} mm wide, {ns} segments, {nv} via(s){note}")
                    routed = True; done += 1
                    break
            if not routed:
                print(f"  {net:10s} {u['ra'] or 'track':10s} <-> {u['rb'] or 'track':10s} NO PATH at {widths} mm")
        if not done:
            break
        prune_zero_length(board)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(a.src, board)
    n = clean_stubs(a.src)
    if n:
        print(f"removed {n} redundant stub segment(s) (shorter than their own width, inside the copper they joined)")
    todo, errors = unconnected(a.src)
    print(f"result: {len(todo)} open connection(s), {len(errors)} DRC error(s)")
    for e in errors:
        print("  DRC:", e["type"], "|", "; ".join(i["description"][:60] for i in e["items"]))
    sys.exit(0 if not todo and not errors else 1)

if __name__ == "__main__":
    main()
