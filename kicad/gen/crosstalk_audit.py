#!/usr/bin/env python3
"""Crosstalk audit of a routed board: how much of each AGGRESSOR net's signal lands on
each SENSITIVE net through trace-to-trace capacitance, and whether the loudest pair
could close a feedback loop.

    python3 kicad/gen/crosstalk_audit.py [--board kicad/cambridge_reverb.kicad_pcb] [--md out.md]

Model (first order, deliberately conservative -- this is a screen, not a field solver):
  * same-layer parallel runs: two microstrips of width w at centre spacing d over the
    ground pour at h = 1.5 mm (1.6 mm FR4, 2 layers). Self capacitance per length from
    the Hammerstad microstrip formula (eps_r 4.5); the coupled fraction
    k = 1 / (1 + (d/h)^2)  (Howard Johnson's near-field estimate). C_m = k * C_self * L.
  * different-layer parallel runs (one on top of the other): broadside plates,
    C_m = eps0 * eps_r * w_min / h * L.
  * only segments that are parallel within 20 deg, closer than 4 mm (centre-to-centre)
    and overlapping in projection by >= 0.5 mm are counted; pads are ignored.
  * the coupled voltage on the victim node = V_aggr * |Z_victim| * 2*pi*f * C_m
    (valid while Z_victim << 1/(2*pi*f*C_m), always true here). Each victim carries an
    assumed node impedance and signal level (Vrms) so the result is a ratio in dB.
  * f = 150 Hz for mains-derived aggressors (AC1/AC2, VRAW, +33V5 ripple), 5 kHz for
    audio aggressors (PA_OUT, SPK, TANK_IN). Sub-audio LFO nets are not aggressors
    (capacitive coupling at 1-10 Hz is nil).
Loop check: for PA_OUT/SPK -> a preamp node, forward gain (node -> PA_OUT, 1 kHz, pots at
noon, volume max; from spice/noise_frontend.cir) + coupling = loop gain; < -20 dB wanted.
"""
import sys, os, math, argparse, collections
import pcbnew

EPS0, EPSR, H = 8.854e-12, 4.5, 1.5e-3
# aggressors: net -> (Vrms at full drive, frequency for the estimate, what it is)
AGGR = {"PA_OUT": (9.8, 5e3, "LM1875 output, 12 W"), "SPK_P": (9.8, 5e3, "speaker +"),
        "ZOB": (9.8, 5e3, "Zobel node = output"),
        "AC1": (24.0, 150, "transformer secondary"), "AC2": (24.0, 150, "transformer secondary"),
        "VRAW": (1.0, 150, "rectifier output, pulsating"), "+33V5": (0.25, 150, "main rail ripple"),
        "TANK_IN": (3.0, 5e3, "reverb tank drive")}
# victims: net -> (|Z_node| ohms at the estimate frequency, signal Vrms, note)
VICT = {"GUITAR_IN": (50e3, 0.1, "jack -> C_in; pickup + 1 M"), "Q1G": (50e3, 0.1, "Q1 gate"),
        "Q1D": (10e3, 1.3, "Q1 drain"), "Q2G": (10e3, 1.3, "Q2 gate"), "Q2D": (10e3, 16, "Q2 drain (clips)"),
        "PREAMP_OUT": (10e3, 3.0, "tone buffer in"), "JA": (50e3, 3.0, "bass ladder"), "JB": (50e3, 3.0, "bass ladder"),
        "JWB": (50e3, 1.5, "bass wiper"), "JTA": (50e3, 3.0, "treble ladder"), "JTB": (50e3, 3.0, "treble ladder"),
        "JWT": (50e3, 1.5, "treble wiper"), "JOUT": (10e3, 1.5, "James sum node"),
        "TONE_OUT": (50e3, 1.0, "volume wiper"), "DRVP": (100e3, 1.0, "tank driver +in"),
        "TANK_OUT": (10e3, 0.02, "tank return (recovery gate)"), "QRG": (10e3, 0.02, "recovery JFET gate"),
        "QRD": (10e3, 0.3, "recovery drain"), "WET": (50e3, 0.3, "reverb level wiper"),
        "SUMJ": (100e3, 1.0, "summer virtual ground: coupled charge x R_fb -> BLEND (1 V)"),
        "TREM_OUT": (10e3, 1.0, "tremolo shunt node"), "TREM_S": (10e3, 1.0, "LDR node"),
        "OBUF_IN": (100e3, 1.0, "output buffer +in"), "MRB_T": (50e3, 1.0, "MRB tank node"),
        "PA_IN": (11e3, 1.0, "PA input (22k||22k)"), "PA_BIAS": (11e3, 1.0, "PA +in"),
        "PA_INV": (1e3, 0.4, "PA -in (1k||22k)"), "MID": (10e3, 1.5, "mid-cut node"), "GYA": (5e3, 0.5, "gyrator")}
# forward gain from the victim node to PA_OUT (dB, 1 kHz, pots noon, volume max; noise_frontend.cir)
FWD_DB = {"GUITAR_IN": 74.3, "Q1G": 74.3, "Q1D": 50.0, "Q2G": 50.0, "Q2D": 25.5, "PREAMP_OUT": 25.5,
          "JA": 27.0, "JB": 27.0, "JWB": 27.0, "JTA": 27.0, "JTB": 27.0, "JWT": 27.0, "JOUT": 33.0,
          "MID": 27.0, "TONE_OUT": 27.3, "DRVP": 27.3, "SUMJ": 27.3, "TREM_OUT": 27.3, "TREM_S": 27.3,
          "OBUF_IN": 27.3, "MRB_T": 27.3, "PA_IN": 27.3, "PA_BIAS": 27.3, "PA_INV": 27.3 - 27.0,
          "TANK_OUT": 27.3 + 20, "QRG": 27.3 + 20, "QRD": 27.3, "WET": 27.3, "GYA": 20.0}

def c_self_per_m(w):
    """Hammerstad microstrip capacitance per metre (F/m) for width w over height H."""
    u = w / H
    eps_eff = (EPSR + 1) / 2 + (EPSR - 1) / 2 / math.sqrt(1 + 12 / u) if u >= 1 else \
              (EPSR + 1) / 2 + (EPSR - 1) / 2 * (1 / math.sqrt(1 + 12 / u) + 0.04 * (1 - u) ** 2)
    if u <= 1:
        z0 = 60 / math.sqrt(eps_eff) * math.log(8 / u + u / 4)
    else:
        z0 = 120 * math.pi / math.sqrt(eps_eff) / (u + 1.393 + 0.667 * math.log(u + 1.444))
    return math.sqrt(eps_eff) / (3e8 * z0)

def segs_by_net(board):
    out = collections.defaultdict(list)
    for t in board.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        a, b = t.GetStart(), t.GetEnd()
        p = (pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)); q = (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y))
        L = math.dist(p, q)
        if L < 0.05:
            continue
        out[t.GetNetname()].append((p, q, L, t.GetLayer(), pcbnew.ToMM(t.GetWidth())))
    return out

def parallel_overlap(s1, s2, max_d=4.0):
    """(overlap_mm, centre_distance_mm) for two roughly parallel segments, else None."""
    (p1, q1, L1, _, _), (p2, q2, L2, _, _) = s1, s2
    ux, uy = (q1[0] - p1[0]) / L1, (q1[1] - p1[1]) / L1
    vx, vy = (q2[0] - p2[0]) / L2, (q2[1] - p2[1]) / L2
    cosang = abs(ux * vx + uy * vy)
    if cosang < math.cos(math.radians(20)):
        return None
    # project s2's ends on s1's axis; perpendicular distances
    def proj(pt): return (pt[0] - p1[0]) * ux + (pt[1] - p1[1]) * uy
    def perp(pt): return abs(-(pt[0] - p1[0]) * uy + (pt[1] - p1[1]) * ux)
    a, b = sorted((proj(p2), proj(q2)))
    ov = min(b, L1) - max(a, 0.0)
    if ov < 0.5:
        return None
    d = (perp(p2) + perp(q2)) / 2
    if d > max_d:
        return None
    return ov, d

def audit(path):
    board = pcbnew.LoadBoard(path)
    segs = segs_by_net(board)
    rows = []
    for an, (va, f, what) in AGGR.items():
        for vn, (zv, vs, vnote) in VICT.items():
            if an not in segs or vn not in segs:
                continue
            cm, longest, detail = 0.0, 0.0, collections.Counter()
            for sa in segs[an]:
                for sv in segs[vn]:
                    r = parallel_overlap(sa, sv)
                    if not r:
                        continue
                    ov, d = r
                    if sa[3] == sv[3]:               # same layer: coplanar microstrips
                        w = (sa[4] + sv[4]) / 2 * 1e-3
                        k = 1.0 / (1.0 + (d * 1e-3 / H) ** 2)
                        c = k * c_self_per_m(w) * ov * 1e-3
                        detail["same"] += 1
                    else:                             # broadside, only if really on top of each other
                        if d > 1.0:
                            continue
                        c = EPS0 * EPSR * min(sa[4], sv[4]) * 1e-3 / H * ov * 1e-3
                        detail["cross"] += 1
                    cm += c; longest = max(longest, ov)
            if cm <= 0:
                continue
            vx = va * zv * 2 * math.pi * f * cm            # coupled Vrms on the victim node
            ratio_db = 20 * math.log10(vx / vs) if vs > 0 else float("nan")
            loop_db = None
            if an in ("PA_OUT", "SPK_P", "ZOB") and vn in FWD_DB:
                loop_db = FWD_DB[vn] + 20 * math.log10(vx / va)   # forward + coupling
            rows.append(dict(aggr=an, vict=vn, cm_pF=cm * 1e12, longest=longest, f=f, vx_uV=vx * 1e6,
                             ratio_db=ratio_db, loop_db=loop_db, what=what, vnote=vnote,
                             same=detail["same"], cross=detail["cross"]))
    rows.sort(key=lambda r: (-(r["loop_db"] if r["loop_db"] is not None else -999), -r["ratio_db"]))
    return rows

def report(path, rows, top=18):
    name = os.path.basename(path)
    out = [f"### Crosstalk screen — `{name}`", "",
           "| Aggressor | Victim | C_m (pF) | longest run (mm) | f | on victim (µV) | vs signal (dB) | loop gain (dB) |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    worst = sorted(rows, key=lambda r: -r["ratio_db"])[:top]
    for r in worst:
        lg = "" if r["loop_db"] is None else f"{r['loop_db']:+.0f}"
        out.append(f"| `{r['aggr']}` | `{r['vict']}` ({r['vnote']}) | {r['cm_pF']:.2f} | {r['longest']:.1f} | "
                   f"{int(r['f'])} Hz | {r['vx_uV']:.1f} | {r['ratio_db']:+.0f} | {lg} |")
    loops = [r for r in rows if r["loop_db"] is not None]
    if loops:
        w = max(loops, key=lambda r: r["loop_db"])
        out += ["", f"Worst feedback loop: `{w['aggr']}` → `{w['vict']}`: loop gain **{w['loop_db']:+.0f} dB** "
                    f"(forward {FWD_DB[w['vict']]:.0f} dB + coupling {20*math.log10(w['vx_uV']*1e-6/AGGR[w['aggr']][0]):.0f} dB); "
                    f"stable with margin if well below 0 dB."]
    return "\n".join(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default=os.path.join(os.path.dirname(__file__), "..", "cambridge_reverb.kicad_pcb"))
    ap.add_argument("--md", default=None, help="write the markdown table here")
    ap.add_argument("--top", type=int, default=18)
    a = ap.parse_args()
    rows = audit(a.board)
    md = report(a.board, rows, a.top)
    print(md)
    if a.md:
        open(a.md, "w").write(md + "\n")
