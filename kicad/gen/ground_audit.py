#!/usr/bin/env python3
"""Ground-return audit: where the big currents flow in the ground copper, and what that
costs in hum and stability.

A ground plane is not an equipotential. The rectifier refills the reservoir capacitor in
short pulses of several times the average current, and the loudspeaker current returns
through the same copper. Each produces microvolts of drop across the planes, and whatever
part of that drop lies BETWEEN the two ground references of a stage is amplified like
signal -- with up to 74 dB of gain behind the input jack, microvolts matter.

This tool solves the real copper: the three ground layers (F.Cu pour, In1 plane, B.Cu
plane) are rasterised from the filled zones, joined by every ground via, and solved as a
resistive network (finite differences, one sparse factorisation). For each current loop
it reports the voltage between each stage's pair of ground references per ampere, then

  * hum at the loudspeaker from the reservoir charging pulses at idle (time-domain
    rectifier model -> harmonics -> A-weighted sum), and
  * the loop gain the loudspeaker return closes around the amplifier (it must stay far
    below 1: that is the "motorboating" / high-level distortion margin).

    python3 kicad/gen/ground_audit.py --board kicad/smd/cambridge_reverb_smd.kicad_pcb \
            [--md report.md] [--json out.json] [--png map.png]

What it is not: a field solver. It is a DC / audio-frequency sheet model (skin depth at
1 kHz is 2 mm, 60x the copper thickness), gains are the simulated ones (spice/results),
and the transformer is a resistance. Good for comparing layouts and for an order of
magnitude; the bench decides the rest.
"""
import sys, os, json, math, argparse
import numpy as np
from PIL import Image, ImageDraw
from scipy import sparse
from scipy.sparse import linalg as sla
from scipy.sparse import csgraph
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

PX = 0.25                 # solver cell, mm
SUB = 2                   # raster oversampling per cell (a cell conducts when >= half of it is copper)
RHO = 1.72e-8             # ohm.m, copper
# finished copper per layer, um (JLC04161H-7628: 1 oz outer, 0.5 oz inner)
THICK = {"F.Cu": 35.0, "In1.Cu": 15.2, "In2.Cu": 15.2, "B.Cu": 35.0}
STACK = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
# layer-to-layer distance along a barrel, mm (prepreg 0.2104, core 1.065, + copper)
SPAN = {("F.Cu", "In1.Cu"): 0.2104 + 0.025, ("In1.Cu", "In2.Cu"): 1.065 + 0.015, ("In2.Cu", "B.Cu"): 0.2104 + 0.025,
        ("F.Cu", "B.Cu"): 1.55}                                     # (two-layer board)
PLATING = 18e-6           # m, barrel plating
# The ground SYSTEM: the signal ground (planes), the power ground and the speaker return,
# joined by the 0R links below (ohms: a soldered wire link; a 0805 "0R" chip is <= 50 mohm,
# typically 20). Boards before errata #32 have no PGND: everything is on GND.
GROUND_NETS = ["GND", "PGND", "SPK_N", "TANK_G"]
LINK_OHM = {"R_spk_rtn": 0.003, "R_gnd": 0.02,
            "R_tg": 10.0}      # the reverb tank's input-shield return (SMD board): a 10 ohm loop breaker, errata #41

# ---- the current loops in the ground copper: (name, into the copper at, out of it at, what)
LOOPS = [
  ("charge-CT",  "C_main.2",    "T1.2",     "reservoir charging pulses, centre-tapped transformer (default build)"),
  ("charge-BR",  "C_main.2",    "JP_BR.2",  "reservoir charging pulses, single winding + JP_BR fitted"),
  ("speaker",    "LS1.2",       "C_main.2", "loudspeaker return, positive half-cycle (supply -> IC -> speaker -> reservoir)"),
  ("speaker-IC", "LS1.2",       "IC_PA.3",  "loudspeaker return, negative half-cycle (C_out -> IC ground pin -> speaker)"),
  ("prefilter",  "C_filt1.2",   "C_main.2", "ripple current of the 100 R / 2000 uF pre-filter"),
]
# ---- the ground-reference pairs: an error voltage phi(a) - phi(b) is in series with the
# signal there; gain = from that point to the loudspeaker terminals, all controls at
# maximum. Gains: spice/results/noise_frontend.txt (input -> speaker 5248 with the optional
# source bypass capacitors, x11.2 / x280 preamp gain without / with them), LM1875 stage 23,
# reverb recovery gm.Rd ~ 25. `hot` = the same with C_s1 / C_s2 fitted.
G_PA = 23.0
VICTIMS = [
  # name,                                   a,           b,            gain (default), gain (C_s1/C_s2 fitted)
  ("input jack sleeve -> Q1 source",        "J_IN1.2",   "R_s1.2",     210.0,  5248.0),
  ("Q1 drain rail reference -> Q2 source",  "C_pre.2",   "R_s2.2",     63.0,   314.0),
  ("Q2 drain rail reference -> tone ref",   "C_pre.2",   "C_vb3.2",    19.0,   19.0),
  ("tone reference -> volume pot ground",   "C_vb3.2",   "POT_VOL.1",  G_PA,   G_PA),
  ("volume pot ground -> mixer reference",  "POT_VOL.1", "C_vbr.2",    2 * G_PA, 2 * G_PA),
  ("tank return -> recovery source",        "REV1.4",    "C_rec_byp.2", 25 * G_PA, 25 * G_PA),
  ("recovery rail reference -> reverb pot", "C_pre.2",   "POT_REV.1",  G_PA,   G_PA),
  ("mixer reference -> PA feedback ground", "C_vbr.2",   "C_gain.2",   G_PA,   G_PA),
  ("PA bias reference -> feedback ground",  "C_bref.2",  "C_gain.2",   1.7,    1.7),
  ("PA feedback ground -> speaker return",  "C_gain.2",  "LS1.2",      1.0,    1.0),
]
# ---- rectifier at idle (the condition in which hum is heard)
MAINS_HZ = 50.0
V_SEC_PK = 24.0 * math.sqrt(2)   # each half of the 24-0-24 secondary
R_SRC = 2.8                      # ohm per half winding incl. reflected primary (50 VA toroid, ~12 % regulation)
V_DIODE = 0.85
C_RES = 4700e-6
I_IDLE = 0.10                    # A: LM1875 quiescent 70 mA + 17 V rail ~25 mA + bleeder / bias
I_FULL = 0.90                    # A average at full sine power (for the worst-case pulse figure only)
R_PRE = 100.0                    # R_27V: the reservoir's ripple voltage drives this much current into C_filt1/2,
                                 # the one supply current that still returns through the planes on the star-ground boards
R_SPK = 8.0
P_REF_V = 9.66                   # Vrms at the speaker for the 11.7 W of sweep_pa_headroom (33.5 V rail)
SPK_SENS = 97.0                  # dB SPL at 1 W / 1 m, a typical 10 in guitar speaker

def mm(v): return pcbnew.ToMM(v)

def raster_poly_set(ps, W, H, x0, y0, px):
    img = Image.new("1", (W, H), 0); d = ImageDraw.Draw(img)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [((mm(o.CPoint(k).x) - x0) / px, (mm(o.CPoint(k).y) - y0) / px) for k in range(o.PointCount())]
        if len(pts) >= 3: d.polygon(pts, fill=1)
        for h in range(ps.HoleCount(i)):
            ho = ps.Hole(i, h)
            pts = [((mm(ho.CPoint(k).x) - x0) / px, (mm(ho.CPoint(k).y) - y0) / px) for k in range(ho.PointCount())]
            if len(pts) >= 3: d.polygon(pts, fill=0)
    return img

def a_weight(f):
    f2 = f * f
    ra = (12194.0 ** 2 * f2 * f2) / ((f2 + 20.6 ** 2) * math.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194.0 ** 2))
    return ra * 10 ** (2.0 / 20)

def rectifier_harmonics(i_load, nharm=40):
    """Full-wave, capacitor-input: charging-current harmonics (A peak) at 2f, 4f, ... and the pulse peak."""
    f = MAINS_HZ; n = 20000; dt = 1.0 / f / n
    v = V_SEC_PK - V_DIODE - i_load * R_SRC          # start near the answer, then settle
    i_d = np.zeros(n)
    for cyc in range(60):
        for k in range(n):
            vs = abs(V_SEC_PK * math.sin(2 * math.pi * k / n))
            i = max(0.0, (vs - V_DIODE - v) / R_SRC)
            v += (i - i_load) * dt / C_RES
            i_d[k] = i
    spec = np.fft.rfft(i_d) / n * 2
    harm = [(2 * f * m, abs(spec[2 * m])) for m in range(1, nharm + 1)]
    # ripple VOLTAGE on the reservoir: the integral of (i_d - i_load) / C
    ripple = [(fr, a / (2 * math.pi * fr * C_RES)) for fr, a in harm]
    return harm, float(i_d.max()), ripple

class Net:
    """The ground copper of one board as a resistor network: one sheet per (net, layer)."""
    def __init__(self, path, px=PX, nets=None, extra_links=None):
        """nets: the nets to solve as one network (default: the ground system).
        extra_links: [(pad a, pad b, ohm)] -- connections that are NOT on the board, e.g. a
        chassis that touches two of its grounds, to ask what a wiring mistake would cost."""
        self.px = px
        b = self.board = pcbnew.LoadBoard(path)
        bb = b.GetBoardEdgesBoundingBox()
        self.x0, self.y0, self.bw, self.bh = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetWidth()), mm(bb.GetHeight())
        self.W, self.H = int(round(self.bw / px)) + 1, int(round(self.bh / px)) + 1
        fw, fh, fpx = self.W * SUB, self.H * SUB, px / SUB
        self.nets = [n for n in (nets or GROUND_NETS) if b.FindNet(n) is not None]
        code = {b.FindNet(n).GetNetCode(): n for n in self.nets}
        cu = [l for l in STACK if b.IsLayerEnabled(b.GetLayerID(l))]
        imgs, draws = {}, {}
        def sheet(net, layer):
            k = (net, layer)
            if k not in imgs:
                imgs[k] = Image.new("1", (fw, fh), 0); draws[k] = ImageDraw.Draw(imgs[k])
            return draws[k]
        def disc(net, layer, x, y, r):
            cx, cy = (x - self.x0) / fpx, (y - self.y0) / fpx
            sheet(net, layer).ellipse([cx - r / fpx, cy - r / fpx, cx + r / fpx, cy + r / fpx], fill=1)
        zone_layer = {}
        for z in b.Zones():
            if z.GetIsRuleArea() or z.GetNetCode() not in code: continue
            net, layer = code[z.GetNetCode()], b.GetLayerName(z.GetLayer())
            if layer not in cu: continue
            img = raster_poly_set(z.GetFilledPolysList(z.GetLayer()), fw, fh, self.x0, self.y0, fpx)
            sheet(net, layer); imgs[(net, layer)] = Image.fromarray(np.array(img) | np.array(imgs[(net, layer)])); draws[(net, layer)] = ImageDraw.Draw(imgs[(net, layer)])
            zone_layer.setdefault(net, []).append(layer)
        # a through-hole pad of a POURED net is copper on the layer whose zone connects it (In1 on the
        # four-layer boards, else the bottom pour) -- on the other planes it is an island; a pad of
        # a ROUTED net is copper on every layer and its barrel joins them
        self.pads = {}                    # "REF.pad" -> (net, x, y, [layers], drill or 0)
        self.barrels = []                 # (net, x, y, drill, [layers])
        for fp in b.GetFootprints():
            for p in fp.Pads():
                key = f"{fp.GetReference()}.{p.GetNumber()}"
                x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
                if p.GetNetCode() not in code:
                    self.pads.setdefault(key, (None, x, y, [], 0)); continue
                net = code[p.GetNetCode()]
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    r = mm(min(p.GetSize().x, p.GetSize().y)) / 2
                    if net in zone_layer:
                        ls = ["In1.Cu"] if "In1.Cu" in zone_layer[net] else [zone_layer[net][-1]]
                    else:
                        ls = list(cu)
                    for l in ls: disc(net, l, x, y, r)
                    drill = mm(min(p.GetDrillSize().x, p.GetDrillSize().y))
                    self.pads[key] = (net, x, y, ls, drill)
                    if len(ls) > 1: self.barrels.append((net, x, y, drill, ls))
                elif p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    bbx = p.GetBoundingBox()
                    sheet(net, "F.Cu").rectangle([(mm(bbx.GetLeft()) - self.x0) / fpx, (mm(bbx.GetTop()) - self.y0) / fpx,
                                                  (mm(bbx.GetRight()) - self.x0) / fpx, (mm(bbx.GetBottom()) - self.y0) / fpx], fill=1)
                    self.pads[key] = (net, x, y, ["F.Cu"], 0)
        self.vias = []; thin = []
        for t in b.GetTracks():
            if t.GetNetCode() not in code: continue
            net = code[t.GetNetCode()]
            if t.GetClass() == "PCB_VIA":
                x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
                ls = [l for l in cu if t.IsOnLayer(b.GetLayerID(l))]
                for l in ls: disc(net, l, x, y, mm(t.GetWidth()) / 2)
                self.barrels.append((net, x, y, mm(t.GetDrill()), ls))
                if net == "GND": self.vias.append((x, y))
            else:
                l = b.GetLayerName(t.GetLayer())
                if l not in cu: continue
                a, e = t.GetStart(), t.GetEnd(); w = mm(t.GetWidth())
                sheet(net, l).line([((mm(a.x) - self.x0) / fpx, (mm(a.y) - self.y0) / fpx), ((mm(e.x) - self.x0) / fpx, (mm(e.y) - self.y0) / fpx)],
                                   fill=1, width=max(1, int(round(w / fpx))))
                for pt in (a, e): disc(net, l, mm(pt.x), mm(pt.y), w / 2)
                if w < 2 * px: thin.append((net, l, mm(a.x), mm(a.y), mm(e.x), mm(e.y)))
        self.sheets = sorted(imgs, key=lambda k: (self.nets.index(k[0]), STACK.index(k[1])))
        self.cu = {}
        for k in self.sheets:
            a = np.array(imgs[k], dtype=np.float32).reshape(self.H, SUB, self.W, SUB).mean(axis=(1, 3))
            self.cu[k] = a >= 0.5
        # a track narrower than two cells can fall between the cells and come out as a dotted
        # line (a 0.5 mm trace on a 0.5 mm grid: TANK_G, the ground stubs of small parts).
        # Walk its centre line cell by cell, 4-connected, so that it always conducts.
        for net, l, x1, y1, x2, y2 in thin:
            n = max(1, int(math.hypot(x2 - x1, y2 - y1) / (px / 4))); prev = None; g = self.cu[(net, l)]
            for i in range(n + 1):
                c = self.cell(x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n)
                if not (0 <= c[0] < self.H and 0 <= c[1] < self.W): continue
                if prev is not None and c[0] != prev[0] and c[1] != prev[1]: g[prev[0], c[1]] = True
                g[c] = True; prev = c
        self.links = []                   # 0R links between two ground nets: (ref, pad a, pad b, ohm)
        for fp in b.GetFootprints():
            ref = fp.GetReference()
            if ref in LINK_OHM:
                ps = [f"{ref}.{p.GetNumber()}" for p in fp.Pads()]
                if len(ps) == 2 and all(self.pads[k][0] for k in ps):
                    self.links.append((ref, ps[0], ps[1], LINK_OHM[ref]))
        self.board_links = list(self.links)
        for a, b_, ohm in (extra_links or []):
            if self.pads.get(a, (None,))[0] and self.pads.get(b_, (None,))[0]:
                self.links.append(("(off-board)", a, b_, ohm))
        self.layers = sorted(set(zone_layer.get("GND", [])), key=STACK.index)      # the layers that carry signal-ground planes / pours
        self._build()

    def cell(self, x, y):
        return int(round((y - self.y0) / self.px)), int(round((x - self.x0) / self.px))

    def _find(self, net, layers, x, y, reach=6):
        """Raw node index of the copper cell nearest (x, y) on one of `layers` of `net`."""
        iy, ix = self.cell(x, y)
        for r in range(0, reach + 1):
            best = None
            for l in layers:
                i = self.idx.get((net, l))
                if i is None: continue
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if max(abs(dy), abs(dx)) != r: continue
                        yy, xx = iy + dy, ix + dx
                        if 0 <= yy < self.H and 0 <= xx < self.W and i[yy, xx] >= 0:
                            d2 = dy * dy + dx * dx
                            if best is None or d2 < best[0]: best = (d2, int(i[yy, xx]))
            if best: return best[1]
        return None

    def _build(self):
        W, H = self.W, self.H
        self.idx = {}; n = 0
        for k in self.sheets:
            m = self.cu[k]; i = -np.ones((H, W), dtype=np.int64); c = int(m.sum())
            i[m] = np.arange(n, n + c); n += c; self.idx[k] = i
        rows, cols, vals = [], [], []
        for k in self.sheets:
            g = THICK[k[1]] * 1e-6 / RHO                   # sheet conductance, S per square
            i = self.idx[k]
            for a, b_ in ((i[:, :-1], i[:, 1:]), (i[:-1, :], i[1:, :])):
                ok = (a >= 0) & (b_ >= 0)
                rows.append(a[ok]); cols.append(b_[ok]); vals.append(np.full(int(ok.sum()), g))
        er, ec, ev = [], [], []
        for (net, x, y, drill, ls) in self.barrels:        # vias and through-hole pads: layer to layer
            ls = sorted(ls, key=STACK.index)
            nodes = [(l, self._find(net, [l], x, y, reach=1)) for l in ls]
            nodes = [(l, nd) for l, nd in nodes if nd is not None]
            for (la, na), (lb, nb) in zip(nodes, nodes[1:]):
                span = sum(SPAN.get((STACK[q], STACK[q + 1]), 0.5) for q in range(STACK.index(la), STACK.index(lb))) * 1e-3
                if (la, lb) in SPAN: span = SPAN[(la, lb)] * 1e-3
                er.append(na); ec.append(nb); ev.append(math.pi * max(drill, 0.3) * 1e-3 * PLATING / (RHO * span))
        self._pending_links = []
        for ref, pa, pb, ohm in self.links:
            na = self._find(self.pads[pa][0], self.pads[pa][3], self.pads[pa][1], self.pads[pa][2])
            nb = self._find(self.pads[pb][0], self.pads[pb][3], self.pads[pb][1], self.pads[pb][2])
            if na is not None and nb is not None:
                er.append(na); ec.append(nb); ev.append(1.0 / ohm)
        r = np.concatenate(rows + [np.array(er, dtype=np.int64)]); c = np.concatenate(cols + [np.array(ec, dtype=np.int64)]); v = np.concatenate(vals + [np.array(ev)])
        A = sparse.coo_matrix((np.concatenate([v, v]), (np.concatenate([r, c]), np.concatenate([c, r]))), shape=(n, n)).tocsr()
        ncomp, lab = csgraph.connected_components(A, directed=False)
        main = np.bincount(lab).argmax()
        keep_idx = np.nonzero(lab == main)[0]
        self.islands = ncomp - 1
        self.remap = -np.ones(n, dtype=np.int64); self.remap[keep_idx] = np.arange(len(keep_idx))
        A = A[keep_idx][:, keep_idx]
        d = np.asarray(A.sum(axis=1)).ravel()
        Lap = (sparse.diags(d) - A).tolil()
        Lap[0, 0] += 1.0                                   # reference node: every loop is balanced, so no current flows here
        self.lu = sla.splu(Lap.tocsc())
        self.m = len(keep_idx)

    def node(self, key):
        """Solver node of a ground-system pad 'REF.pad' (nearest connected copper cell), or None."""
        if key not in self.pads or self.pads[key][0] is None:
            return None
        net, x, y, ls, _ = self.pads[key]
        raw = self._find(net, ls, x, y)
        if raw is None or self.remap[raw] < 0:
            return None
        return int(self.remap[raw])

    def solve(self, src, snk):
        """Potential of every node for 1 A into the copper at pad `src`, out at pad `snk`."""
        a, b_ = self.node(src), self.node(snk)
        if a is None or b_ is None: return None
        rhs = np.zeros(self.m); rhs[a] += 1.0; rhs[b_] -= 1.0
        return self.lu.solve(rhs)

    def field(self, phi, layer, net="GND"):
        out = np.full((self.H, self.W), np.nan)
        i = self.idx.get((net, layer))
        if i is None: return out
        m = i >= 0
        r = self.remap[i[m]]
        out[m] = np.where(r >= 0, phi[np.maximum(r, 0)], np.nan)
        return out

def audit(path, px=PX, png=None, extra_links=None):
    net = Net(path, px, extra_links=extra_links)
    R = {"board": os.path.relpath(path, ROOT), "size": (round(net.bw, 1), round(net.bh, 1)), "layers": net.layers,
         "cell_mm": px, "nodes": net.m, "ground_vias": len(net.vias), "floating_copper_pieces": net.islands,
         "nets": net.nets, "links": [(ref, f"{net.pads[a][0]} - {net.pads[b_][0]}", ohm) for ref, a, b_, ohm in net.board_links],
         "star": "PGND" in net.nets}
    pos = {k: (round(v[1] - net.x0, 1), round(v[2] - net.y0, 1)) for k, v in net.pads.items()}
    R["net_of"] = {k: v[0] for k, v in net.pads.items() if v[0]}
    harm_idle, pk_idle, ripple = rectifier_harmonics(I_IDLE)
    _, pk_full, _ = rectifier_harmonics(I_FULL)
    R["rectifier"] = dict(idle_A=I_IDLE, pulse_peak_idle_A=round(pk_idle, 2), pulse_peak_full_A=round(pk_full, 2),
                          harmonics_idle_mA=[(f, round(a * 1e3, 1)) for f, a in harm_idle[:6]])
    # equivalent current for the hum sums: rms and A-weighted rms of the harmonics below 5 kHz
    i_rms = math.sqrt(sum((a / math.sqrt(2)) ** 2 for f, a in harm_idle if f <= 5000))
    i_a = math.sqrt(sum((a / math.sqrt(2) * a_weight(f)) ** 2 for f, a in harm_idle if f <= 5000))
    R["rectifier"]["ac_rms_idle_A"] = round(i_rms, 3); R["rectifier"]["ac_rms_idle_A_weighted"] = round(i_a, 4)
    # the pre-filter's ripple current (reservoir ripple across R_27V; C_filt is a short at these frequencies)
    ip_rms = math.sqrt(sum((v / R_PRE / math.sqrt(2)) ** 2 for f, v in ripple if f <= 5000))
    ip_a = math.sqrt(sum((v / R_PRE / math.sqrt(2) * a_weight(f)) ** 2 for f, v in ripple if f <= 5000))
    R["rectifier"]["ripple_mV_rms"] = round(math.sqrt(sum((v / math.sqrt(2)) ** 2 for f, v in ripple)) * 1e3, 1)
    R["rectifier"]["prefilter_mA_rms"] = round(ip_rms * 1e3, 3)
    R["loops"] = {}
    fields = {}
    for name, src, snk, what in LOOPS:
        phi = net.solve(src, snk)
        if phi is None:
            R["loops"][name] = dict(what=what, missing=True); continue
        a, b_ = net.node(src), net.node(snk)
        rows = []
        for vname, pa, pb, g, ghot in VICTIMS:
            na, nb = net.node(pa), net.node(pb)
            if na is None or nb is None:
                rows.append(dict(victim=vname, a=pa, b=pb, missing=True)); continue
            dv = float(phi[na] - phi[nb])                  # V per A
            rows.append(dict(victim=vname, a=pa, b=pb, uV_per_A=round(dv * 1e6, 3), gain=g, gain_hot=ghot))
        R["loops"][name] = dict(what=what, src=src, snk=snk, distance_mm=round(math.dist(pos[src], pos[snk]), 1),
                                loop_mohm=round(float(phi[a] - phi[b_]) * 1e3, 3), victims=rows)
        fields[name] = phi
    # ---- hum at the speaker at idle: the charging pulses, plus the pre-filter's ripple current
    # (same waveform family, unknown relative sign: the two shares are added as magnitudes)
    def at_speaker(loop, gk):
        Lp = R["loops"].get(loop)
        if not Lp or Lp.get("missing"): return 0.0, None
        ok = [v for v in Lp["victims"] if not v.get("missing")]
        tot = sum(v["uV_per_A"] * 1e-6 * v[gk] for v in ok)
        return abs(tot), max(ok, key=lambda v: abs(v["uV_per_A"] * v[gk]))["victim"]
    for name in ("charge-CT", "charge-BR"):
        Lp = R["loops"].get(name)
        if not Lp or Lp.get("missing"): continue
        for tag, gk in (("hum", "gain"), ("hum_hot", "gain_hot")):
            zc, worst = at_speaker(name, gk); zp, worst_p = at_speaker("prefilter", gk)
            v_c, v_p = zc * i_rms, zp * ip_rms
            v_rms, v_a = v_c + v_p, zc * i_a + zp * ip_a
            Lp[tag] = dict(speaker_uV_rms=round(v_rms * 1e6, 2), pulses_uV_rms=round(v_c * 1e6, 2), prefilter_uV_rms=round(v_p * 1e6, 2),
                           speaker_uV_A_weighted=round(v_a * 1e6, 3),
                           dB_re_full_power=round(20 * math.log10(max(v_rms, 1e-9) / P_REF_V), 1),
                           dBA_SPL_1m=round(SPK_SENS + 10 * math.log10(max(v_a ** 2 / R_SPK, 1e-18)), 1),
                           dominant=worst if v_c >= v_p else worst_p, dominant_loop="charging pulses" if v_c >= v_p else "pre-filter ripple current")
    # ---- loop gain closed by the speaker return. The last pair (PA feedback ground -> the
    # speaker's - terminal, gain 1) is not feedback into an earlier stage: it is plain series
    # resistance in the speaker circuit, reported as such.
    for name in ("speaker", "speaker-IC"):
        Lp = R["loops"].get(name)
        if not Lp or Lp.get("missing"): continue
        ok = [v for v in Lp["victims"] if not v.get("missing")]
        for tag, gk in (("feedback", "gain"), ("feedback_hot", "gain_hot")):
            z = sum(v["uV_per_A"] * 1e-6 * v[gk] for v in ok if v[gk] > 1.0)       # V at the speaker per A of speaker current
            Lp[tag] = dict(loop_gain=round(abs(z) / R_SPK, 7), loop_gain_dB=round(20 * math.log10(max(abs(z) / R_SPK, 1e-15)), 1))
        Lp["series_mohm"] = round(abs(sum(v["uV_per_A"] for v in ok if v["gain"] <= 1.0)) * 1e-3, 2)
    R["pads"] = {k: pos[k] for k in sorted({p for _, a, b_, _ in LOOPS for p in (a, b_)} | {p for _, a, b_, _, _ in VICTIMS for p in (a, b_)}) if k in pos}
    # ---- distance of the LM1875's support parts from its pins (datasheet: "as close as possible")
    def d(a, b_): return round(math.dist(pos[a], pos[b_]), 1) if a in pos and b_ in pos else None
    R["pa_support"] = {"C_byp1 (100 nF) to pin 5": d("C_byp1.1", "IC_PA.5"), "C_byp1 ground to pin 3": d("C_byp1.2", "IC_PA.3"),
                       "C_byp2 (10 uF) to pin 5": d("C_byp2.1", "IC_PA.5"), "R_zobel to pin 4": d("R_zobel.1", "IC_PA.4"),
                       "C_zobel ground to pin 3": d("C_zobel.2", "IC_PA.3"), "C_lp to pin 1": d("C_lp.1", "IC_PA.1"),
                       "R_fb to pin 2": d("R_fb.1", "IC_PA.2"), "R_gain to pin 2": d("R_gain.1", "IC_PA.2")}
    if png and "charge-CT" in fields:
        picture(net, fields["charge-CT"], R, png)
    return R

def _font(size):
    from PIL import ImageFont
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans.ttf"):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()

def picture(net, phi, R, png, layer="In1.Cu", scale=6):
    """Signal-ground potential for 1 A of reservoir charging current, on the In1 plane:
    log colour scale in uV, relative to the power amp's feedback ground."""
    f = net.field(phi, layer if layer in net.layers else net.layers[0])
    ref = net.node("C_gain.2")
    f = (f - (phi[ref] if ref is not None else np.nanmedian(f))) * 1e6          # uV per A
    mag = np.log10(np.clip(np.abs(f), 0.1, 1e4))                              # 0.1 uV .. 10 mV
    t = (mag + 1) / 5.0
    stops = [(0.0, (16, 24, 48)), (0.25, (34, 84, 140)), (0.5, (60, 160, 120)), (0.75, (235, 200, 70)), (1.0, (220, 60, 50))]
    rgb = np.zeros(f.shape + (3,), dtype=np.uint8)
    for c in range(3):
        rgb[..., c] = np.interp(np.nan_to_num(t, nan=0), [s_[0] for s_ in stops], [s_[1][c] for s_ in stops]).astype(np.uint8)
    rgb[np.isnan(f)] = (0, 0, 0)
    s = max(1, int(round(scale * net.px / 0.5)))
    img = Image.fromarray(rgb).resize((f.shape[1] * s, f.shape[0] * s), Image.NEAREST)
    d = ImageDraw.Draw(img); font = _font(15)
    # the other ground nets' copper (power ground, speaker return), drawn over the plane
    for (nm, l), m in net.cu.items():
        if nm == "GND": continue
        ys, xs = np.nonzero(m)
        col = (255, 120, 220) if nm == "PGND" else (120, 220, 255)
        for y, x in zip(ys[::1], xs[::1]):
            d.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], fill=col)
    show = ["C_main.2", "T1.2", "LS1.2", "IC_PA.3", "J_IN1.2", "REV1.4", "C_rec_byp.2", "C_pre.2", "R_s1.2", "C_gain.2", "POT_VOL.1"]
    for key in show:
        if key not in R["pads"]: continue
        x, y = R["pads"][key]
        cx, cy = x / net.px * s, y / net.px * s
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=(255, 255, 255), width=2)
        tx = cx + 9 if cx < img.width - 110 else cx - 9 - d.textlength(key, font=font)
        d.text((tx, cy - 9), key, fill=(255, 255, 255), font=font)
    x0, y0, w = 24, 14, 300
    for i in range(w):
        tt = i / (w - 1.0)
        d.line([(x0 + i, y0), (x0 + i, y0 + 16)], fill=tuple(int(np.interp(tt, [s_[0] for s_ in stops], [s_[1][c] for s_ in stops])) for c in range(3)))
    for k, lab in enumerate(["0.1", "1", "10", "100", "1 mV", "10 mV per A"]):
        d.text((x0 + k * w / 5 - 8, y0 + 20), lab, fill=(255, 255, 255), font=font)
    img.save(png)

def report(R):
    o = []
    o.append(f"# Ground-return audit -- {R['board']}\n")
    o.append(f"Board {R['size'][0]} x {R['size'][1]} mm; signal-ground copper on {', '.join(R['layers'])}, joined by {R['ground_vias']} ground vias; "
             f"solved on a {R['cell_mm']} mm grid ({R['nodes']} nodes).\n")
    if R.get("star"):
        o.append("Ground system: " + ", ".join(R["nets"]) + f" -- {len(R['nets'])} nets, joined only by "
                 + " and ".join(f"{ref} ({nets})" for ref, nets, _ in R["links"]) + ". The planes carry signal ground only.\n")
    else:
        o.append("Ground system: one net. Every return current shares the planes.\n")
    rc = R["rectifier"]
    o.append(f"Rectifier at idle ({rc['idle_A'] * 1e3:.0f} mA): charging pulses peak {rc['pulse_peak_idle_A']} A "
             f"({rc['pulse_peak_full_A']} A at full power); AC content {rc['ac_rms_idle_A'] * 1e3:.0f} mA rms, "
             f"{rc['ac_rms_idle_A_weighted'] * 1e3:.1f} mA A-weighted. First harmonics (mA peak): "
             + ", ".join(f"{int(f)} Hz {a}" for f, a in rc["harmonics_idle_mA"]) + f". Reservoir ripple {rc['ripple_mV_rms']} mV rms, "
             f"which drives {rc['prefilter_mA_rms']} mA rms through the 100 R pre-filter into C_filt1 / C_filt2.\n")
    for name, Lp in R["loops"].items():
        if Lp.get("missing"):
            o.append(f"## {name}: {Lp['what']} -- not on this board\n"); continue
        o.append(f"## {name}: {Lp['what']}\n")
        o.append(f"{Lp['src']} -> {Lp['snk']}: {Lp['distance_mm']} mm apart in the copper, {Lp['loop_mohm']} mohm between the two pads.\n")
        o.append("| ground references of | from -> to | uV per A | gain to speaker | uV at speaker per A |")
        o.append("|---|---|---:|---:|---:|")
        for v in Lp["victims"]:
            if v.get("missing"):
                o.append(f"| {v['victim']} | {v['a']} -> {v['b']} | n/a | | |"); continue
            o.append(f"| {v['victim']} | {v['a']} -> {v['b']} | {v['uV_per_A']:.2f} | {v['gain']:g} | {v['uV_per_A'] * v['gain']:.1f} |")
        o.append("")
        for tag, label in (("hum", "Hum at the speaker, idle, standard build"), ("hum_hot", "Same with C_s1 / C_s2 fitted (25x more preamp gain)")):
            if tag in Lp:
                h = Lp[tag]
                spl = f"{h['dBA_SPL_1m']} dBA SPL at 1 m" if h["dBA_SPL_1m"] > -20 else "far below 0 dBA SPL"
                o.append(f"**{label}:** {h['speaker_uV_rms']} uV rms ({h['dB_re_full_power']} dB re full power) = "
                         f"{h['pulses_uV_rms']} uV from the charging pulses + {h['prefilter_uV_rms']} uV from the pre-filter's ripple current "
                         f"returning through the planes; {h['speaker_uV_A_weighted']} uV A-weighted = {spl}; "
                         f"largest share: {h['dominant']} ({h['dominant_loop']}).\n")
        for tag, label in (("feedback", "Loop gain closed through the ground copper, standard build"), ("feedback_hot", "Same with C_s1 / C_s2 fitted")):
            if tag in Lp:
                o.append(f"**{label}:** " + (f"{Lp[tag]['loop_gain']:.2g} ({Lp[tag]['loop_gain_dB']} dB).\n" if Lp[tag]["loop_gain_dB"] > -200
                                             else "none -- this current does not enter the planes.\n"))
        if "series_mohm" in Lp:
            o.append(f"Series resistance this return adds to the speaker circuit: {Lp['series_mohm']} mohm.\n")
    o.append("## LM1875 support parts: distance from the IC pins (mm)\n")
    o.append("The data sheet: keep the output compensation and the 0.1 uF supply decoupling as close as possible to the LM1875.\n")
    for k, v in R["pa_support"].items():
        if v is not None: o.append(f"- {k}: {v}")
    o.append("")
    return "\n".join(o)

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--board", required=True); ap.add_argument("--md"); ap.add_argument("--json"); ap.add_argument("--png")
    ap.add_argument("--px", type=float, default=PX)
    a = ap.parse_args()
    R = audit(a.board, a.px, a.png)
    txt = report(R)
    if a.md: open(a.md, "w").write(txt)
    if a.json: json.dump(R, open(a.json, "w"), indent=1)
    print(txt)

if __name__ == "__main__":
    main()
