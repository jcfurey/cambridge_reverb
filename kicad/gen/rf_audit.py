#!/usr/bin/env python3
"""Ground and parasitics audit of a routed board: is the copper built the way an RF
board is, and does any stray capacitance reach the audio band?

    python3 kicad/gen/rf_audit.py --board kicad/smd/cambridge_reverb_smd.kicad_pcb [--md report.md]

What it measures (everything from the board file, nothing assumed):

  stack        which layers carry tracks and which are planes; no track on a plane
  planes       every opening in each plane, by size: a row of pins whose clearance holes
               merge is a SLOT, and return current has to walk round it
  edge         nearest copper to the board outline per layer (JLCPCB: >= 0.2 mm from a
               routed edge, which itself is +/- 0.2 mm; this board keeps 0.5 mm)
  pour gaps    nearest top-pour copper to any foreign trace / pad, and to HiZ copper
  fence        ground vias along the perimeter: count and the largest gap between two
  stitching    ground vias in all, and the point of the board furthest from one
  SMD grounds  every SMD ground pad has a via to the planes within reach
  parasitics   capacitance to ground of every sensitive net -- trace over its plane
               (microstrip on F.Cu, offset stripline on In2), pads, vias -- and the
               corner frequency it makes with that node's impedance

Capacitance model (JLC04161H-7628: 0.2104 mm prepreg er 4.4 between F.Cu/In1 and
In2/B.Cu, 1.065 mm core er 4.6 between In1 and In2; 35 um outer, 15 um inner copper):
  F.Cu trace   microstrip over In1, Hammerstad-Jensen Z0 and eps_eff; C' = sqrt(eps_eff) / (c Z0)
               x 1.10 for the top pour 0.5 mm (HiZ: 1.0 mm) to each side
  In2 trace    offset stripline, B.Cu plane 0.21 mm below, In1 plane 1.07 mm above
               (IPC-2141 asymmetric stripline); C' = sqrt(er) / (c Z0)
  SMD pad      parallel plate to In1 x 1.2 fringe
  PTH pad      0.35 pF (outer rings beside the top pour / bottom plane, barrel through
               two plane openings) -- an estimate, stated as one
  via          0.4 pF (same reasoning, smaller)
Good to roughly +/- 30 %: enough to tell 5 pF from 50, which is the question.
"""
import sys, os, math, json, argparse, collections
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

C0 = 299792458.0
H_PP, ER_PP = 0.2104e-3, 4.4       # prepreg F.Cu-In1 and In2-B.Cu
H_CORE, ER_CORE = 1.065e-3, 4.6    # core In1-In2
T_OUT, T_IN = 35e-6, 15.2e-6
C_PTH, C_VIA = 0.35e-12, 0.4e-12
PX = 0.05                          # raster pitch for the plane / pour measurements, mm

# node impedance at audio (ohm): what the stray capacitance works against. Driven nodes
# take their source resistance; pot wipers the worst case R/4; unlisted nets 10 k.
Z_NODE = {
    "GUITAR_IN": (50e3, "pickup, a few H: tens of kohm near resonance"), "RF1": (50e3, "pickup + C_in_pre"), "Q1G": (51e3, "pickup + R_rf1"),
    "Q2G": (10e3, "Q1 drain load"), "TANK_OUT": (3e3, "tank output coil"), "RF2": (3e3, "tank coil + C_rev2"), "QRG": (4e3, "tank coil + R_rf2"),
    "JA": (10e3, "R_j1"), "JB": (10e3, "R_j2"), "JWB": (72e3, "bass wiper, pot at noon"), "JTA": (36e3, "C_j3 at 2 kHz"), "JTB": (36e3, "C_j4 at 2 kHz"),
    "JWT": (62e3, "treble wiper"), "JOUT": (1e3, "R_j4 from the treble wiper"), "TONE_OUT": (62e3, "volume wiper at half resistance"),
    "DRVP": (62e3, "volume wiper through C_drvin"), "OBUF_IN": (10e3, "R_mrb_ser"), "WN1": (15e3, "LFO series arm (sub-audio)"),
    "LFO_P": (15e3, "LFO shunt arm (sub-audio)"), "MRB_T": (10e3, "R_mrb_ser"), "PA_BIAS": (22e3, "R_bias3"), "FS_REV": (10e3, "recovery drain load"),
    "WET": (62e3, "reverb-level wiper"), "FS_MRB": (10e3, "MRB tank return, pedal open"), "PA_IN": (0.1e3, "op-amp output"),
    "SUMJ": (33e3, "summer inputs in parallel -- a feedback node: see the stability note"), "MKN": (5e3, "make-up gain divider"),
    "R_INV": (9.1e3, "tank-driver gain divider"), "PA_INV": (0.96e3, "power-amp gain divider"), "LFO_N": (3.2e3, "LFO gain divider"),
}
AUDIO_LIMIT = 100e3                # Hz: a corner above this is < 0.2 dB at 20 kHz

def mm(v): return pcbnew.ToMM(v)

def microstrip(w, h, er, t):
    """Z0, eps_eff of a microstrip (Hammerstad-Jensen, with the thickness correction)."""
    we = w + (t / math.pi) * (1 + math.log(2 * h / t)) if w / h > 1 / (2 * math.pi) else w + (t / math.pi) * (1 + math.log(4 * math.pi * w / t))
    u = we / h
    ee = (er + 1) / 2 + (er - 1) / 2 / math.sqrt(1 + 12 / u)
    z = 60 / math.sqrt(ee) * math.log(8 / u + u / 4) if u <= 1 else 120 * math.pi / (math.sqrt(ee) * (u + 1.393 + 0.667 * math.log(u + 1.444)))
    return z, ee

def c_fcu(w):
    """F/m of an F.Cu trace of width w (m) over the In1 plane."""
    z, ee = microstrip(w, H_PP, ER_PP, T_OUT)
    return math.sqrt(ee) / (C0 * z)

def c_in2(w):
    """F/m of an In2 trace: B.Cu plane 0.21 mm below, In1 plane 1.07 mm above."""
    er = (ER_PP + ER_CORE) / 2
    z = 80 / math.sqrt(er) * math.log(1.9 * (2 * H_PP + T_IN) / (0.8 * w + T_IN)) * (1 - H_PP / (4 * H_CORE))
    if z < 5:                       # the formula runs out for wide traces: parallel plate + fringe
        return 8.854e-12 * ER_PP * (w + 2 * H_PP) / H_PP + 8.854e-12 * ER_CORE * w / H_CORE
    return math.sqrt(er) / (C0 * z)

def plane_names(b):
    return {b.GetLayerName(z.GetLayer()): z for z in b.Zones() if not z.GetIsRuleArea() and z.GetZoneName().startswith("plane_")}

def raster_fill(b, zone, layer, W, H, x0, y0):
    """Boolean image of a zone's filled copper on one layer."""
    img = Image.new("1", (W, H), 0); d = ImageDraw.Draw(img)
    ps = zone.GetFilledPolysList(layer)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [((mm(o.CPoint(k).x) - x0) / PX, (mm(o.CPoint(k).y) - y0) / PX) for k in range(o.PointCount())]
        if len(pts) >= 3: d.polygon(pts, fill=1)
        for hI in range(ps.HoleCount(i)):
            ho = ps.Hole(i, hI)
            pts = [((mm(ho.CPoint(k).x) - x0) / PX, (mm(ho.CPoint(k).y) - y0) / PX) for k in range(ho.PointCount())]
            if len(pts) >= 3: d.polygon(pts, fill=0)
    return np.array(img, dtype=bool)

def audit(path):
    b = pcbnew.LoadBoard(path)
    bb = b.GetBoardEdgesBoundingBox(); x0, y0 = mm(bb.GetLeft()), mm(bb.GetTop()); bw, bh = mm(bb.GetWidth()), mm(bb.GetHeight())
    W, H = int(round(bw / PX)) + 1, int(round(bh / PX)) + 1
    R = {"board": os.path.relpath(path), "size": (round(bw, 1), round(bh, 1))}
    cu = [b.GetLayerName(l) for l in b.GetEnabledLayers().CuStack()]
    planes = plane_names(b)
    tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]; vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    # ---- stack
    length = collections.Counter()
    for t in tracks: length[b.GetLayerName(t.GetLayer())] += mm(t.GetLength())
    R["stack"] = [(l, "GND plane" if l in planes else "signal", round(length.get(l, 0))) for l in cu]
    R["tracks_on_planes"] = sum(1 for t in tracks if b.GetLayerName(t.GetLayer()) in planes)
    # ---- planes: openings
    fps = [(fp.GetReference(), mm(fp.GetPosition().x), mm(fp.GetPosition().y)) for fp in b.GetFootprints()]
    pads_xy = [(fp.GetReference(), mm(p.GetPosition().x), mm(p.GetPosition().y)) for fp in b.GetFootprints() for p in fp.Pads()]
    def nearest_ref(x, y):
        return min(pads_xy, key=lambda q: (q[1] - x) ** 2 + (q[2] - y) ** 2)[0]
    R["planes"] = {}
    margin = int(1.0 / PX)
    for name, z in planes.items():
        fill = raster_fill(b, z, z.GetLayer(), W, H, x0, y0)
        void = ~fill; void[:margin, :] = void[-margin:, :] = False; void[:, :margin] = void[:, -margin:] = False
        lab, n = ndimage.label(void)
        sl = ndimage.find_objects(lab); openings = []
        for k, s_ in enumerate(sl):
            hh, ww = (s_[0].stop - s_[0].start) * PX, (s_[1].stop - s_[1].start) * PX
            cy, cx = (s_[0].start + s_[0].stop) / 2 * PX + y0, (s_[1].start + s_[1].stop) / 2 * PX + x0
            openings.append((round(max(hh, ww), 2), round(min(hh, ww), 2), nearest_ref(cx, cy)))
        openings.sort(reverse=True)
        pieces = ndimage.label(fill)[1]
        R["planes"][name] = dict(coverage=round(100 * fill.sum() * PX * PX / (bw * bh), 1), pieces=pieces, openings=len(openings),
                                 longest=openings[:6], over5=sum(1 for o in openings if o[0] > 5.0))
    # ---- edge pullback
    edge = collections.defaultdict(lambda: 1e9)
    def d_edge(x, y, r): return min(x - x0, x0 + bw - x, y - y0, y0 + bh - y) - r
    for t in tracks:
        l = b.GetLayerName(t.GetLayer())
        for pt in (t.GetStart(), t.GetEnd()): edge[l] = min(edge[l], d_edge(mm(pt.x), mm(pt.y), mm(t.GetWidth()) / 2))
    for v in vias:
        for l in cu: edge[l] = min(edge[l], d_edge(mm(v.GetPosition().x), mm(v.GetPosition().y), mm(v.GetWidth()) / 2))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
            r = mm(max(p.GetSize().x, p.GetSize().y)) / 2
            for l in cu:
                if p.IsOnLayer(b.GetLayerID(l)): edge[l] = min(edge[l], d_edge(mm(p.GetPosition().x), mm(p.GetPosition().y), r))
    zone_fill = {}
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        l = b.GetLayerName(z.GetLayer()); f = raster_fill(b, z, z.GetLayer(), W, H, x0, y0); zone_fill[l] = f
        ys, xs = np.nonzero(f)
        if len(ys): edge[l] = min(edge[l], min(xs.min(), W - 1 - xs.max(), ys.min(), H - 1 - ys.max()) * PX)
    R["edge"] = {l: round(edge[l], 2) for l in cu}
    # ---- top pour: gap to foreign copper
    hiz = set()
    try:
        pro = json.load(open(os.path.splitext(path)[0] + ".kicad_pro"))
        hiz = {p["pattern"] for p in pro["net_settings"]["netclass_patterns"] if p["netclass"] == "HiZ"}
    except Exception: pass
    if "F.Cu" in zone_fill:
        dist = ndimage.distance_transform_edt(~zone_fill["F.Cu"]) * PX
        gap_all = gap_hiz = 1e9
        def sample(x, y, r, net):
            nonlocal gap_all, gap_hiz
            iy, ix = int(round((y - y0) / PX)), int(round((x - x0) / PX))
            if 0 <= iy < H and 0 <= ix < W:
                g = dist[iy, ix] - r
                gap_all = min(gap_all, g)
                if net in hiz: gap_hiz = min(gap_hiz, g)
        for t in tracks:
            if t.GetLayer() != pcbnew.F_Cu or t.GetNetname() == "GND": continue
            a, e = t.GetStart(), t.GetEnd(); n = max(1, int(mm(t.GetLength()) / 0.1))
            for k in range(n + 1):
                sample(mm(a.x) + (mm(e.x) - mm(a.x)) * k / n, mm(a.y) + (mm(e.y) - mm(a.y)) * k / n, mm(t.GetWidth()) / 2, t.GetNetname())
        R["pour_gap"] = dict(any=round(gap_all, 2), hiz=round(gap_hiz, 2) if gap_hiz < 1e8 else None,
                             pieces=ndimage.label(zone_fill["F.Cu"])[1], coverage=round(100 * zone_fill["F.Cu"].sum() * PX * PX / (bw * bh), 1))
    # ---- fence and stitching
    gnd_vias = [(mm(v.GetPosition().x), mm(v.GetPosition().y)) for v in vias if v.GetNetname() == "GND"]
    per = []
    for x, y in gnd_vias:
        d = min(x - x0, x0 + bw - x, y - y0, y0 + bh - y)
        if d < 3.5:                                  # on the perimeter: its position along the outline, clockwise from the top-left
            s = (x - x0) if d == y - y0 else (bw + (y - y0)) if d == x0 + bw - x else (2 * bw + bh - (x - x0)) if d == y0 + bh - y else (2 * bw + 2 * bh - (y - y0))
            per.append(s)
    per.sort(); gaps = [b_ - a_ for a_, b_ in zip(per, per[1:])] + ([per[0] + 2 * (bw + bh) - per[-1]] if per else [])
    R["fence"] = dict(vias=len(per), median=round(float(np.median(gaps)), 1) if gaps else None, largest=round(max(gaps), 1) if gaps else None,
                      over10=sum(1 for g in gaps if g > 10.0))
    pts = np.ones((int(bh / 0.25) + 1, int(bw / 0.25) + 1), bool)
    for x, y in gnd_vias:
        pts[min(pts.shape[0] - 1, int(round((y - y0) / 0.25))), min(pts.shape[1] - 1, int(round((x - x0) / 0.25)))] = False
    far = ndimage.distance_transform_edt(pts) * 0.25 if gnd_vias else np.full(pts.shape, 1e9)
    iy, ix = np.unravel_index(np.argmax(far), far.shape)
    R["stitch"] = dict(gnd_vias=len(gnd_vias), per_cm2=round(len(gnd_vias) / (bw * bh / 100), 2), furthest=round(float(far.max()), 1),
                       furthest_at=nearest_ref(x0 + ix * 0.25, y0 + iy * 0.25), mean=round(float(far.mean()), 1))
    # ---- SMD ground pads: a ground via within 3.5 mm
    lonely = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetNetname() == "GND":
                px, py = mm(p.GetPosition().x), mm(p.GetPosition().y)
                if not any(math.dist((px, py), q) <= 3.5 for q in gnd_vias): lonely.append(fp.GetReference())
    R["smd_gnd"] = dict(pads=sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetNetname() == "GND"), lonely=lonely)
    # ---- parasitic capacitance per net
    cap = collections.defaultdict(lambda: dict(c=0.0, f=0.0, i=0.0, pads=0, vias=0))
    for t in tracks:
        n = t.GetNetname(); l = b.GetLayerName(t.GetLayer()); w = mm(t.GetWidth()) * 1e-3; L = mm(t.GetLength()) * 1e-3
        if l == "F.Cu": cap[n]["c"] += c_fcu(w) * 1.10 * L; cap[n]["f"] += L * 1e3
        else:           cap[n]["c"] += c_in2(w) * L; cap[n]["i"] += L * 1e3
    for v in vias:
        cap[v.GetNetname()]["c"] += C_VIA; cap[v.GetNetname()]["vias"] += 1
    for fp in b.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if not n: continue
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                cap[n]["c"] += 8.854e-12 * ER_PP * mm(p.GetSize().x) * mm(p.GetSize().y) * 1e-6 / H_PP * 1.2
            elif p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                cap[n]["c"] += C_PTH
            cap[n]["pads"] += 1
    rows = []
    for n, (z, why) in Z_NODE.items():
        if n not in cap: continue
        c = cap[n]["c"]; fc = 1 / (2 * math.pi * z * c) if c > 0 else float("inf")
        rows.append((fc, n, c * 1e12, cap[n]["f"], cap[n]["i"], cap[n]["pads"], cap[n]["vias"], z, why))
    rows.sort()
    R["parasitics"] = rows
    R["c_sumj"] = cap["SUMJ"]["c"] * 1e12 if "SUMJ" in cap else None
    return R

def report(R):
    out = []; P = out.append
    P(f"### Ground and parasitics audit — `{os.path.basename(R['board'])}` ({R['size'][0]:g} × {R['size'][1]:g} mm)\n")
    P("| Layer | Role | Track length (mm) |\n|---|---|---:|")
    for l, role, L in R["stack"]: P(f"| `{l}` | {role} | {L if role == 'signal' else '—'} |")
    P(f"\nTracks on a plane layer: **{R['tracks_on_planes']}**.\n")
    P("| Plane | Copper coverage | Pieces | Openings | Longer than 5 mm | Longest openings (length × width mm, at) |\n|---|---:|---:|---:|---:|---|")
    for name, d in R["planes"].items():
        P(f"| `{name}` | {d['coverage']} % | {d['pieces']} | {d['openings']} | **{d['over5']}** | " + "; ".join(f"{a:g} × {b_:g} `{r}`" for a, b_, r in d["longest"][:5]) + " |")
    P("\n| Check | Measured | Rule |\n|---|---:|---|")
    P(f"| Copper to board edge, per layer | " + ", ".join(f"{l} {v:g}" for l, v in R["edge"].items()) + " mm | ≥ 0.5 mm here (JLCPCB: ≥ 0.2 mm from a routed edge, ± 0.2 mm on the edge itself; ≥ 0.4 mm from a V-cut) |")
    if "pour_gap" in R:
        g = R["pour_gap"]
        P(f"| Top pour to the nearest foreign trace | {g['any']:g} mm | ≥ 0.5 mm (2.4 × the 0.21 mm to the plane) |")
        if g["hiz"] is not None: P(f"| Top pour to the nearest HiZ trace | {g['hiz']:g} mm | ≥ 1.0 mm |")
        P(f"| Top pour | {g['coverage']} % of the board in {g['pieces']} piece(s) | every piece tied to the planes (unconnected pieces are removed by the fill) |")
    f = R["fence"]
    P(f"| Perimeter ground fence | {f['vias']} vias, median pitch {f['median']:g} mm, largest gap {f['largest']:g} mm ({f['over10']} gaps over 10 mm) | 5 mm pitch; gaps only at the corner holes and the wiring pads |")
    s_ = R["stitch"]
    P(f"| Ground vias, whole board | {s_['gnd_vias']} ({s_['per_cm2']:g} per cm²) | — |")
    P(f"| Furthest point from a ground via | {s_['furthest']:g} mm (near `{s_['furthest_at']}`), mean {s_['mean']:g} mm | λ/10 in FR4: 14 mm at 1 GHz, 7.5 mm at 1.9 GHz |")
    g = R["smd_gnd"]
    P(f"| SMD ground pads with a via to the planes within 3.5 mm | {g['pads'] - len(g['lonely'])} of {g['pads']}" + (f" (missing: {', '.join(g['lonely'])})" if g["lonely"] else "") + " | all |")
    P("\n**Capacitance to ground of the sensitive nets** (trace over its plane + pads + vias; ± 30 %) and the corner it makes with the node impedance:\n")
    P("| Net | C (pF) | F.Cu (mm) | In2 (mm) | pads | vias | node impedance | corner |\n|---|---:|---:|---:|---:|---:|---|---:|")
    for fc, n, c, lf, li, pads, vias, z, why in R["parasitics"]:
        zc = f"{z / 1e3:g} k ({why})"
        P(f"| `{n}` | {c:.1f} | {lf:.0f} | {li:.0f} | {pads} | {vias} | {zc} | {'**' if fc < AUDIO_LIMIT else ''}{fc / 1e3:.0f} kHz{'**' if fc < AUDIO_LIMIT else ''} |")
    low = [r for r in R["parasitics"] if r[0] < AUDIO_LIMIT and r[1] != "SUMJ"]
    P(f"\nLowest corner: `{R['parasitics'][0][1]}` at {R['parasitics'][0][0] / 1e3:.0f} kHz. " +
      ("Every net is above 100 kHz — under 0.2 dB at 20 kHz." if not low else f"{len(low)} net(s) below 100 kHz: " + ", ".join(f"`{r[1]}`" for r in low) + "."))
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--board", required=True); ap.add_argument("--md", default=None); ap.add_argument("--json", default=None)
    a = ap.parse_args()
    R = audit(a.board); txt = report(R)
    print(txt)
    if a.md: open(a.md, "w").write(txt)
    if a.json: json.dump(R, open(a.json, "w"), indent=1, default=str)

if __name__ == "__main__":
    main()
