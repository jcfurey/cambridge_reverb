#!/usr/bin/env python3
"""Ground-loop audit: every way a current can go round instead of there and back.

ground_audit.py prices the return currents that are SUPPOSED to flow. This tool looks for
the loops nobody drew:

  1. Closed loops in the routed copper of a net (a ring is a shorted turn for any stray
     field, and usually a routing accident).
  2. The big current loops -- reservoir charging, loudspeaker, LM1875 decoupling, Zobel --
     traced through the actual tracks and parts: enclosed area (the magnetic moment per
     ampere), copper resistance, and the field the charging loop makes at 10 cm.
  3. Copper under the mounting hardware: a screw head on ground copper is a chassis bond
     that nobody planned.
  4. Wiring mistakes, simulated: each adds one off-board connection between two of the
     board's grounds (a bare LM1875 tab on the chassis, a metal speaker jack, ...) and
     ground_audit's solver says what the SAME charging and speaker currents then do.
  5. Loops that close OFF the board -- two jack sleeves joined by the panel, the two tank
     shields joined at the tank, a chassis bonded twice: the current a stray field drives
     round such a loop crosses the board between two pads; the solver gives the volts at
     the loudspeaker per milliamp, and the wiring rule that keeps the loop open.

    python3 kicad/gen/loop_audit.py --board kicad/smd/cambridge_reverb_smd.kicad_pcb [--md out.md] [--json out.json]
"""
import sys, os, json, math, argparse, collections, heapq
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import ground_audit as ga

mm = pcbnew.ToMM
LAND_MIN = 3.5            # mm: outer-layer copper stays this far from a mounting-hole CENTRE (7 mm washer)
RING_MIN = 1.0            # mm2 of copper-free area inside a closed loop of traces before it counts as a ring
MU0 = 4e-7 * math.pi
# stray field assumed for the off-board loops: 1 uT at 50 Hz is a toroid at 10-15 cm; an
# EI-core transformer makes 10-50 uT there
B_REF, F_REF, A_REF = 1e-6, 50.0, 100e-4          # T, Hz, m2 (100 cm2)

# ---- the big current loops, as a walk: ("net", net, pad, pad) follows the copper,
# ("part", pad, pad) goes through a component, ("ext", pad, pad) through the off-board wiring
HEAVY = [
  ("reservoir charging, half-cycle 1", 0.213,
   [("net", "AC1", "T1.1", "BR1.2"), ("part", "BR1.2", "BR1.1"), ("net", "VRAW", "BR1.1", "F1.1"), ("part", "F1.1", "F1.2"),
    ("net", "+33V5", "F1.2", "C_main.1"), ("part", "C_main.1", "C_main.2"), ("net", "PGND", "C_main.2", "T1.2"), ("ext", "T1.2", "T1.1")]),
  ("reservoir charging, half-cycle 2", 0.213,
   [("net", "AC2", "T1.3", "BR1.3"), ("part", "BR1.3", "BR1.1"), ("net", "VRAW", "BR1.1", "F1.1"), ("part", "F1.1", "F1.2"),
    ("net", "+33V5", "F1.2", "C_main.1"), ("part", "C_main.1", "C_main.2"), ("net", "PGND", "C_main.2", "T1.2"), ("ext", "T1.2", "T1.3")]),
  ("loudspeaker, positive half (reservoir -> IC -> speaker -> reservoir)", 1.2,
   [("net", "+33V5", "C_main.1", "IC_PA.5"), ("part", "IC_PA.5", "IC_PA.4"), ("net", "PA_OUT", "IC_PA.4", "C_out.1"), ("part", "C_out.1", "C_out.2"),
    ("net", "SPK_P", "C_out.2", "LS1.1"), ("ext", "LS1.1", "LS1.2"), ("net", "SPK_N", "LS1.2", "R_spk_rtn.1"), ("part", "R_spk_rtn.1", "R_spk_rtn.2"),
    ("net", "PGND", "R_spk_rtn.2", "C_main.2"), ("part", "C_main.2", "C_main.1")]),
  ("loudspeaker, negative half (C_out -> IC -> speaker)", 1.2,
   [("net", "PA_OUT", "IC_PA.4", "C_out.1"), ("part", "C_out.1", "C_out.2"), ("net", "SPK_P", "C_out.2", "LS1.1"), ("ext", "LS1.1", "LS1.2"),
    ("net", "SPK_N", "LS1.2", "R_spk_rtn.1"), ("part", "R_spk_rtn.1", "R_spk_rtn.2"), ("net", "PGND", "R_spk_rtn.2", "IC_PA.3"), ("part", "IC_PA.3", "IC_PA.4")]),
  ("LM1875 decoupling (C_byp1)", None,
   [("net", "+33V5", "C_byp1.1", "IC_PA.5"), ("part", "IC_PA.5", "IC_PA.3"), ("net", "PGND", "IC_PA.3", "C_byp1.2"), ("part", "C_byp1.2", "C_byp1.1")]),
  ("Zobel (R_zobel + C_zobel)", None,
   [("net", "PA_OUT", "IC_PA.4", "R_zobel.1"), ("part", "R_zobel.1", "R_zobel.2"), ("net", "ZOB", "R_zobel.2", "C_zobel.1"), ("part", "C_zobel.1", "C_zobel.2"),
    ("net", "PGND", "C_zobel.2", "IC_PA.3"), ("part", "IC_PA.3", "IC_PA.4")]),
]
# ---- wiring mistakes: (name, [(pad, pad, ohm)], what it is). CHS = the board's chassis pad
MISTAKES = [
  ("LM1875 tab bare on the chassis", [("IC_PA.3", "J_IN1.2", 0.010)],
   "the tab is pin 3 = power ground; with the chassis also on signal ground at the jacks it bridges the star"),
  ("metal speaker jack on the chassis", [("LS1.2", "J_IN1.2", 0.010)],
   "the speaker's return terminal reaches signal ground a second way"),
  ("transformer centre tap also to the chassis", [("T1.2", "J_IN1.2", 0.010)],
   "the charging pulses get a second way home, through the chassis and the input ground"),
  ("chassis bonded twice (jacks AND the chassis pad)", [("CHS", "J_IN1.2", 0.005)],
   "no supply current is diverted -- but it is a loop for stray fields, see the table below"),
]
# ---- loops that close off the board: (name, pad, pad, off-board milliohms in SERIES with a signal, gain there, rule)
# power ground must be a star AT the reservoir: the charging pulses (centre tap -> reservoir
# minus) on copper of their own, everything else on other arms (errata #43)
STAR_SRC, STAR_HUB = "T1.2", "C_main.2"
STAR_QUIET = ["IC_PA.3", "R_spk_rtn.2", "C_byp1.2", "C_byp2.2", "C_zobel.2", "D2.2", "TP_PGND.1"]
STAR_MAX = 2.0            # mohm of charging-path copper any of them may share (the pad itself is ~0.1)

EXTERNAL = [
  ("two input-jack sleeves joined by a metal panel", "J_IN1.2", "J_IN2.2", 5.0, "input",
   "non-insulated jacks: ONE sleeve wire to the board (the panel joins the sleeves); insulated jacks: all three"),
  ("input jack 1 and the FX jack sleeves joined by the panel", "J_IN1.2", "J_IN3.2", 5.0, "input", "as above"),
  ("the two reverb-tank cable shields joined at the tank (4FB2A1C: both connectors grounded)", "REV1.2", "REV1.4", 40.0, "tank",
   "solder only the OUTPUT cable's shield at the board (pad 4) and leave the input shield open at this end; run the two cables together"),
  ("chassis bonded at the input jacks and again at the chassis pad", "J_IN1.2", "CHS", 5.0, "input",
   "ONE chassis bond: the jacks if they are not insulated, otherwise the chassis pad"),
  ("footswitch cable shield / DIN shell on the chassis", "FS1.4", "J_IN1.2", 0.0, "none",
   "DIN pins 4-6 are the pedal's commons; do not tie them to the connector shell"),
  ("volume-pot case soldered to its ground lug (case on the panel)", "POT_VOL.1", "J_IN1.2", 0.0, "none",
   "do not solder pot lugs to pot cases; the panel already holds the cases at chassis potential"),
  ("reverb-pot case soldered to its ground lug", "POT_REV.1", "J_IN1.2", 0.0, "none", "as above"),
]

class NetGraph:
    """The routed copper of one net as a graph: nodes = pads, vias, junctions; edges = track pieces."""
    def __init__(self, board, netname):
        b = board
        segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname]
        vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == netname]
        pads = [(fp.GetReference(), p) for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() == netname]
        self.nodes = []; self.named = collections.defaultdict(list)
        def add(kind, x, y): self.nodes.append((kind, x, y)); return len(self.nodes) - 1
        pad_items = []
        for ref, p in pads:
            k = add("pad", mm(p.GetPosition().x), mm(p.GetPosition().y)); self.named[f"{ref}.{p.GetNumber()}"].append(k); pad_items.append((k, p))
        via_items = [(add("via", mm(v.GetPosition().x), mm(v.GetPosition().y)), v) for v in vias]
        S = [((mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth()), t.GetLayer()) for t in segs]
        self.tracks = segs; self.vias = {k: v for k, v in via_items}
        self.piece = []          # per edge: (track index, d1, d2) -- the stretch of that track, or None for a joint
        def anchor(pt, layer):
            P = pcbnew.VECTOR2I(pcbnew.FromMM(pt[0]), pcbnew.FromMM(pt[1]))
            for k, p in pad_items:
                if p.IsOnLayer(layer) and p.HitTest(P): return k
            for k, v in via_items:
                if v.IsOnLayer(layer) and math.dist(pt, (self.nodes[k][1], self.nodes[k][2])) <= mm(v.GetWidth()) / 2: return k
            return None
        cluster = {}
        def node_at(pt, layer, w):
            k = anchor(pt, layer)
            if k is not None: return k
            key = (layer, round(pt[0], 3), round(pt[1], 3))
            if key not in cluster:
                for (l2, x2, y2), k2 in cluster.items():
                    if l2 == layer and math.dist(pt, (x2, y2)) <= max(0.02, w / 4): cluster[key] = k2; break
                else: cluster[key] = add("junction", pt[0], pt[1])
            return cluster[key]
        def foot(q, a, e):
            L = math.dist(a, e)
            if L < 1e-6: return None
            u = ((q[0] - a[0]) * (e[0] - a[0]) + (q[1] - a[1]) * (e[1] - a[1])) / (L * L)
            if not 0.02 < u < 0.98: return None
            f = (a[0] + u * (e[0] - a[0]), a[1] + u * (e[1] - a[1]))
            return u * L, f, math.dist(q, f)
        self.edges = []          # (a, b, length mm, width mm, layer name)
        for i, (a, e, w, layer) in enumerate(S):
            L = math.dist(a, e); pts = [(0.0, a), (L, e)]
            others = [q for j, (a2, e2, w2, l2) in enumerate(S) if j != i and l2 == layer for q in (a2, e2)]
            others += [(self.nodes[k][1], self.nodes[k][2]) for k, p in pad_items if p.IsOnLayer(layer)]
            others += [(self.nodes[k][1], self.nodes[k][2]) for k, v in via_items if v.IsOnLayer(layer)]
            for q in others:
                f = foot(q, a, e)
                if f and f[2] <= w / 2: pts.append((f[0], f[1]))
            pts.sort()
            ks = [node_at(p, layer, w) for _, p in pts]
            for (d1, _), (d2, _), k1, k2 in zip(pts, pts[1:], ks, ks[1:]):
                if k1 != k2: self.edges.append((k1, k2, d2 - d1, w, b.GetLayerName(layer))); self.piece.append((i, d1, d2))
            # an end of this segment that sits on another one's body, off its centre line: join it to the foot
            for q in (a, e):
                kq = node_at(q, layer, w)
                for j, (a2, e2, w2, l2) in enumerate(S):
                    if j == i or l2 != layer: continue
                    f = foot(q, a2, e2)
                    if f and 1e-4 < f[2] <= w2 / 2:
                        kf = node_at(f[1], layer, w2)
                        if kf != kq: self.edges.append((kq, kf, f[2], min(w, w2), b.GetLayerName(layer))); self.piece.append(None)
        self.adj = collections.defaultdict(list)
        for n, (a, b_, L, w, l) in enumerate(self.edges):
            self.adj[a].append((b_, n)); self.adj[b_].append((a, n))

    def rings(self):
        """Closed loops in the copper: (polygon, [edge index, ...]) per independent cycle."""
        uniq = {}
        for n, (a, b_, L, w, l) in enumerate(self.edges):
            key = (min(a, b_), max(a, b_))
            if key not in uniq or L < self.edges[uniq[key]][2]: uniq[key] = n
        adj = collections.defaultdict(list)
        for (a, b_), n in uniq.items(): adj[a].append((b_, n)); adj[b_].append((a, n))
        self.uadj = adj
        parent, depth, out = {}, {}, []
        for root in list(adj):
            if root in parent: continue
            parent[root] = None; depth[root] = 0; st = [root]; used = set()
            while st:
                u = st.pop()
                for v, n in adj[u]:
                    if n in used: continue
                    used.add(n)
                    if v not in parent:
                        parent[v] = u; depth[v] = depth[u] + 1; st.append(v)
                    else:
                        pa, pb = [u], [v]; x, y = u, v
                        while x != y:
                            if depth[x] >= depth[y]: x = parent[x]; pa.append(x)
                            else: y = parent[y]; pb.append(y)
                        cyc = pa + pb[-2::-1]
                        es = [uniq[(min(p, q), max(p, q))] for p, q in zip(cyc, cyc[1:] + cyc[:1]) if (min(p, q), max(p, q)) in uniq]
                        out.append(([(self.nodes[k][1], self.nodes[k][2]) for k in cyc], es, cyc))
        return out

    def hole(self, poly, es):
        """Copper-free area inside a ring, mm2 (<= 0: the traces fill it -- a blob, not a ring)."""
        per = sum(math.dist(p, q) for p, q in zip(poly, poly[1:] + poly[:1]))
        w = sum(self.edges[n][3] * self.edges[n][2] for n in es) / max(sum(self.edges[n][2] for n in es), 1e-9)
        return abs(poly_area(poly)) - per * w / 2

    def path(self, src, dst):
        """Shortest copper path between two pads: (points, length mm, edges) or None."""
        S, D = set(self.named.get(src, [])), set(self.named.get(dst, []))
        if not S or not D: return None
        dist = {s: 0.0 for s in S}; prev = {}; h = [(0.0, s) for s in S]; end = None
        while h:
            c, u = heapq.heappop(h)
            if u in D: end = u; break
            if c > dist.get(u, 1e18): continue
            for v, n in self.adj[u]:
                nc = c + self.edges[n][2]
                if nc < dist.get(v, 1e18): dist[v] = nc; prev[v] = (u, n); heapq.heappush(h, (nc, v))
        if end is None: return None
        pts, es, u = [], [], end
        while u not in S:
            pts.append((self.nodes[u][1], self.nodes[u][2])); u, n = prev[u]; es.append(n)
        pts.append((self.nodes[u][1], self.nodes[u][2]))
        return pts[::-1], dist[end], [self.edges[n] for n in es[::-1]]

def poly_area(poly):
    return 0.5 * sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))

def pad_xy(board):
    return {f"{fp.GetReference()}.{p.GetNumber()}": (mm(p.GetPosition().x), mm(p.GetPosition().y)) for fp in board.GetFootprints() for p in fp.Pads()}

def hole_lands(board):
    """Nearest plane / pour copper to each mounting-hole centre, per layer (mm)."""
    out = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if not (ref.startswith("H") and ref[1:].isdigit()): continue
        c = fp.GetPosition()
        for z in board.Zones():
            if z.GetIsRuleArea(): continue
            ps = z.GetFilledPolysList(z.GetLayer()); r = None
            for k in range(30, 200):
                rr = k * 0.05
                if any(ps.Contains(pcbnew.VECTOR2I(int(c.x + pcbnew.FromMM(rr) * math.cos(a * math.pi / 24)), int(c.y + pcbnew.FromMM(rr) * math.sin(a * math.pi / 24)))) for a in range(48)):
                    r = rr; break
            l = board.GetLayerName(z.GetLayer())
            out[l] = min(out.get(l, 99.0), r if r is not None else 99.0)
    return out

def audit(path, px=0.5):
    b = pcbnew.LoadBoard(path)
    R = {"board": os.path.relpath(path, ROOT)}
    xy = pad_xy(b)
    chs = "J_CHS.1" if "J_CHS.1" in xy else "TP_GND_PSU.1"
    R["chassis_pad"] = chs
    # ---- 1. closed copper loops
    nets = sorted({p.GetNetname() for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() and p.GetNetname() != "GND"})
    graphs = {}; rings = []
    for n in nets:
        g = graphs[n] = NetGraph(b, n)
        for poly, es, cyc in g.rings():
            if g.hole(poly, es) >= RING_MIN: rings.append((n, round(abs(poly_area(poly)), 1), len(poly)))
    R["rings"] = sorted(rings, key=lambda r: -r[1]); R["nets_checked"] = len(nets)
    # ---- 2. the big current loops
    R["heavy"] = []
    for name, i_rms, walk in HEAVY:
        poly, cu_mm, mohm, ok = [], 0.0, 0.0, True
        for step in walk:
            if step[0] == "net":
                p = graphs[step[1]].path(step[2], step[3]) if step[1] in graphs else None
                if p is None: ok = False; break
                poly += p[0]; cu_mm += p[1]
                mohm += sum(ga.RHO * (L * 1e-3) / ((w * 1e-3) * ga.THICK[l] * 1e-6) for (_, _, L, w, l) in p[2]) * 1e3
            else:
                if step[1] not in xy or step[2] not in xy: ok = False; break
                poly += [xy[step[1]], xy[step[2]]]
        if not ok:
            R["heavy"].append(dict(name=name, missing=True)); continue
        area = abs(poly_area(poly)) / 100.0                                   # cm2
        d = dict(name=name, area_cm2=round(area, 1), copper_mm=round(cu_mm), copper_mohm=round(mohm, 1))
        if i_rms:
            d["i_rms"] = i_rms
            d["field_uT_10cm"] = round(MU0 * i_rms * area * 1e-4 / (2 * math.pi * 0.1 ** 3) * 1e6, 4)
        R["heavy"].append(d)
    # ---- 3. mounting holes
    R["hole_copper_mm"] = hole_lands(b)
    # ---- 4. wiring mistakes: the same on-board currents, one extra connection
    def digest(A):
        L = A["loops"]
        return dict(hum_uV=L["charge-CT"]["hum"]["speaker_uV_rms"], hum_hot_uV=L["charge-CT"]["hum_hot"]["speaker_uV_rms"],
                    feedback_dB=max(L[k]["feedback"]["loop_gain_dB"] for k in ("speaker", "speaker-IC")),
                    feedback_hot_dB=max(L[k]["feedback_hot"]["loop_gain_dB"] for k in ("speaker", "speaker-IC")))
    R["as_built"] = digest(ga.audit(path, px))
    R["mistakes"] = []
    for name, links, why in MISTAKES:
        links = [(chs if a == "CHS" else a, chs if b_ == "CHS" else b_, o) for a, b_, o in links]
        R["mistakes"].append(dict(name=name, why=why, link=[f"{a} - {b_} ({o * 1e3:g} mohm)" for a, b_, o in links], **digest(ga.audit(path, px, extra_links=links))))
    # ---- 5. loops that close off the board: volts at the speaker per mA circulating
    net = ga.Net(path, px)
    gains = {"input": (210.0, 5248.0), "tank": (25 * ga.G_PA, 25 * ga.G_PA), "none": (0.0, 0.0)}
    emf = 2 * math.pi * F_REF * B_REF * A_REF                                # V in the reference loop
    R["external"] = []; R["emf_ref_uV"] = round(emf * 1e6, 2)
    # ---- 2b. what the charging pulses share with the rest of power ground: 1 A from the centre tap
    # to the reservoir, and how far that moves each "quiet" pad against the reservoir's minus
    phi = net.solve(STAR_SRC, STAR_HUB)
    if phi is not None:
        hub = float(phi[net.node(STAR_HUB)])
        sh = {k: round((float(phi[net.node(k)]) - hub) * 1e3, 2) for k in STAR_QUIET if net.node(k) is not None}
        R["pgnd_star"] = dict(run_mohm=round((float(phi[net.node(STAR_SRC)]) - hub) * 1e3, 1), shared_mohm=sh, worst_mohm=max(abs(v) for v in sh.values()),
                              tab_vs_star_mohm=round(sh.get("IC_PA.3", 0.0) - sh.get("R_spk_rtn.2", 0.0), 2))
    for name, a, b_, series_mohm, where, rule in EXTERNAL:
        a = chs if a == "CHS" else a; b_ = chs if b_ == "CHS" else b_
        phi = net.solve(a, b_)
        if phi is None:
            R["external"].append(dict(name=name, missing=True)); continue
        z = zh = 0.0
        for _, va, vb, g, gh in ga.VICTIMS:
            na, nb = net.node(va), net.node(vb)
            if na is None or nb is None: continue
            z += float(phi[na] - phi[nb]) * g; zh += float(phi[na] - phi[nb]) * gh
        board_mohm = float(phi[net.node(a)] - phi[net.node(b_)]) * 1e3
        g, gh = gains[where]
        # per mA: through the board's copper, plus the off-board conductor that is in series with a signal
        # the loop's resistance: the board between the two pads (incl. any link resistor) plus two off-board conductors
        loop_ohm = board_mohm * 1e-3 + 2 * max(series_mohm, 5.0) * 1e-3
        i_ref = emf / loop_ohm                                                # A for the reference field
        per_mA = abs(z) + series_mohm * 1e-3 * g; per_mA_hot = abs(zh) + series_mohm * 1e-3 * gh      # V at the speaker per A
        R["external"].append(dict(name=name, a=a, b=b_, board_mohm=round(board_mohm, 2), loop_mohm=round(loop_ohm * 1e3, 1),
                                  uV_per_mA_board=round(abs(z) * 1e3, 3), uV_per_mA_board_hot=round(abs(zh) * 1e3, 3),
                                  uV_per_mA_wire=round(series_mohm * 1e-3 * g * 1e3, 1), uV_per_mA_wire_hot=round(series_mohm * 1e-3 * gh * 1e3, 1),
                                  i_ref_uA=round(i_ref * 1e6, 2), ref_uV=round(i_ref * per_mA * 1e6, 2), ref_hot_uV=round(i_ref * per_mA_hot * 1e6, 2),
                                  series_mohm=series_mohm, rule=rule))
    return R

def report(R):
    o = [f"# Ground-loop audit -- {R['board']}\n"]
    o.append("## 1. Closed loops in the routed copper\n")
    o.append(f"{R['nets_checked']} routed nets checked (signal ground is a mesh by design and is not one of them). "
             + ("**None contains a closed loop.**\n" if not R["rings"] else "Loops: " + ", ".join(f"`{n}` {a} mm2" for n, a, _ in R["rings"]) + "\n"))
    o.append("## 2. The big current loops, through the actual tracks\n")
    o.append("| loop | enclosed area | copper in the loop | its resistance | field at 10 cm |")
    o.append("|---|---:|---:|---:|---:|")
    for h in R["heavy"]:
        if h.get("missing"): o.append(f"| {h['name']} | n/a | | | |"); continue
        f = f"{h['field_uT_10cm']} uT at {h['i_rms']} A rms" if "i_rms" in h else "--"
        o.append(f"| {h['name']} | {h['area_cm2']} cm2 | {h['copper_mm']} mm | {h['copper_mohm']} mohm | {f} |")
    o.append("\nFor scale: the mains transformer's own stray field at 10 cm is of the order of 1 uT (toroid) to 10-50 uT (EI core).\n")
    s = R.get("pgnd_star")
    if s:
        o.append("### Power ground as a star at the reservoir\n")
        o.append(f"1 A of charging current from the centre tap (`{STAR_SRC}`) to the reservoir's minus (`{STAR_HUB}`) drops {s['run_mohm']} mV along its run. "
                 "How far that moves the other power-ground pads against the reservoir's minus -- the copper they share with the charging pulses:\n")
        o.append("| pad | shared with the charging path |")
        o.append("|---|---:|")
        for k, v in s["shared_mohm"].items(): o.append(f"| `{k}` | {abs(v):g} mohm |")
        o.append(f"\nLimit {STAR_MAX:g} mohm (the reservoir pad itself is about 0.1). The LM1875's tab against the star link: {abs(s['tab_vs_star_mohm']):g} mohm -- "
                 "the voltage per ampere of charging current that a tab shorted to the chassis would put round the ground system.\n")
    o.append("## 3. Copper under the mounting hardware\n")
    o.append("Nearest plane / pour copper to a mounting-hole centre: " + ", ".join(f"{l} {v:g} mm" for l, v in R["hole_copper_mm"].items())
             + f". Outer layers need {LAND_MIN} mm (a 7 mm washer); the inner plane cannot be touched.\n")
    o.append("## 4. Wiring mistakes, simulated\n")
    o.append("One off-board connection added to the board as built; same charging pulses, same speaker current.\n")
    o.append("| | hum at the speaker, idle (standard / hot preamp) | speaker current fed back through the grounds |")
    o.append("|---|---:|---:|")
    fbs = lambda v: "none" if v < -200 else f"{v} dB"
    a = R["as_built"]
    o.append(f"| **as built** | {a['hum_uV']} / {a['hum_hot_uV']} uV | {fbs(a['feedback_dB'])} |")
    for m in R["mistakes"]:
        o.append(f"| {m['name']} ({'; '.join(m['link'])}) | **{m['hum_uV']} / {m['hum_hot_uV']} uV** | **{fbs(m['feedback_dB'])}** ({fbs(m['feedback_hot_dB'])} hot) |")
    o.append("")
    for m in R["mistakes"]: o.append(f"- *{m['name']}:* {m['why']}.")
    o.append("\n## 5. Loops that close off the board\n")
    o.append(f"A stray field drives a current round any closed ground loop. Reference field: {B_REF * 1e6:g} uT at {F_REF:g} Hz through "
             f"{A_REF * 1e4:g} cm2 of loop = {R['emf_ref_uV']} uV (a toroid at 10-15 cm; an EI core is 10-50 times that). "
             "\"Hot\" = with the optional source-bypass capacitors fitted.\n")
    o.append("| loop, IF it is closed | pads, resistance on the board | whole loop | per mA: in the board copper | per mA: in the off-board conductor that carries signal | at the speaker for the reference field | keep it open by |")
    o.append("|---|---|---:|---:|---:|---:|---|")
    for e in R["external"]:
        if e.get("missing"): o.append(f"| {e['name']} | n/a | | | | | |"); continue
        wire = f"{e['uV_per_mA_wire']} uV ({e['uV_per_mA_wire_hot']} hot), {e['series_mohm']:g} mohm" if e["series_mohm"] else "--"
        o.append(f"| {e['name']} | {e['a']} - {e['b']}, {e['board_mohm']} mohm | {e['loop_mohm']} mohm | {e['uV_per_mA_board']} uV ({e['uV_per_mA_board_hot']} hot) | {wire} "
                 f"| **{e['ref_uV']} uV** ({e['ref_hot_uV']} hot) | {e['rule']} |")
    o.append("")
    return "\n".join(o)

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--board", required=True); ap.add_argument("--md"); ap.add_argument("--json"); ap.add_argument("--px", type=float, default=0.5)
    a = ap.parse_args()
    R = audit(a.board, a.px); txt = report(R)
    if a.md: open(a.md, "w").write(txt)
    if a.json: json.dump(R, open(a.json, "w"), indent=1)
    print(txt)

if __name__ == "__main__":
    main()
