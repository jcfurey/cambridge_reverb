#!/usr/bin/env python3
"""Offset audit: things that are a little off from where they should be -- in millimetres
and in millivolts.

  1. Track ends: does every trace land on the CENTRE of its pad or via, and on the centre
     line of the trace it joins? (tidy_tracks.py fixes them; this measures what is left.)
  2. Placement file: is every assembled part's footprint origin -- the point the
     pick-and-place file reports -- the centre of its pads? And which rotation offset does
     the CPL apply per package?
  3. DC paths: a net that reaches a defined DC level only through capacitors has none of
     its own. It drifts, and the first switch, plug or meter probe that pins it sends the
     difference through the amplifier as a click (errata #38, #39).
  4. Voltage drops along the supply traces at the DC operating point: what each consumer
     actually gets, and the resistance a signal current sees in each rail.

    python3 kicad/gen/offset_audit.py smd|tht [--md out.md] [--json out.json]
"""
import sys, os, json, math, argparse, collections
import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import ground_audit as ga, loop_audit, tidy_tracks

mm = pcbnew.ToMM
PROF = {"tht": os.path.join(ROOT, "kicad", "cambridge_reverb.kicad_pcb"), "smd": os.path.join(ROOT, "kicad", "smd", "cambridge_reverb_smd.kicad_pcb")}

# ---- 3. DC conduction through each kind of part: groups of pins that are joined for DC.
# Capacitors, open switches, jacks with nothing plugged in and op-amp INPUTS join nothing.
DC_GROUPS = {
    "R": [("1", "2")], "L": [("1", "2")], "FUSE": [("1", "2")], "POT": [("1", "2", "3")], "D": [("1", "2")], "LED": [("1", "2")],
    "XFMR": [("1", "2", "3")], "BRIDGE": [("1", "2", "3", "4")], "SPEAKER": [("1", "2")],
    "NJFET": [("1", "2")],                    # channel: drain - source; the gate is a reverse-biased junction
    "NPN": [("1", "2", "3")],
    "VTL5C1": [("1", "2"), ("3", "4")],       # LED; LDR (50 Mohm when dark, but a path)
    "Reverb_Tank_4FB2A1C": [("1", "2"), ("3", "4")],     # the two coils -- only while the tank is plugged in
}
# pins that SET a DC level: op-amp / regulator / power-amp outputs
DC_DRIVERS = {"OPAMP8": ("1", "7"), "OPAMP14": ("1", "7", "8", "14"), "LM317": ("1", "2", "3"), "LM1875": ("4",)}
# THT board: three DC returns are fitted off the board, on the part itself (it is full): docs/03
OFFBOARD_RETURN = {"tht": {"GUITAR_IN": "10 M across the lugs of input jack 1", "MIDSW": "1 M across the mid-cut switch",
                           "MRB_OUT": "none: do not rest a meter on TP MRB with the amplifier turned up"}, "smd": {}}

# ---- 4. DC loads per rail: (rail, source pad, [(consumer pad, mA, what)])
RAILS = [
    ("+33V5", "C_main.1", [("IC_PA.5", 640.0, "LM1875 at full sine power (70 mA idle, 2 A peaks)"), ("R_27V.1", 32.0, "regulator pre-filter"),
                           ("R_bleed.1", 3.4, "bleeder"), ("R_bias1.1", 0.8, "PA bias divider")]),
    ("PGND", "C_main.2", [("IC_PA.3", -640.0, "LM1875 return"), ("R_spk_rtn.2", -32.0, "signal-ground return through the star")]),
    ("VREG_IN", "R_27V.2", [("U1.3", 32.0, "LM317 input")]),
    ("+17V", "U1.2", [("IC1.8", 3.0, "reverb driver / mixer TL072"), ("IC2.8", 3.0, "LFO / output buffer TL072"), ("IC3.4", 5.6, "tone TL074"),
                      ("R_c.1", 4.0, "vactrol LED (average with the tremolo on)"), ("R_pre.1", 2.4, "JFET rail"), ("R_reg1.1", 5.2, "LM317 divider"),
                      ("R_vbr1.1", 0.09, "VBIAS_R divider"), ("R_vbt1.1", 0.09, "VBIAS_T divider"), ("R_vb31.1", 0.09, "VBIAS_3 divider"), ("R_b1.1", 0.09, "LED driver bias")]),
    ("+17V_PRE", "R_pre.2", [("R_d1.1", 0.8, "Q1"), ("R_d2.1", 0.8, "Q2"), ("R_rec1.1", 0.8, "Q_rec (reverb recovery)")]),
]
VIA_MOHM = 1.0            # one plated via barrel

def track_ends(board):
    return tidy_tracks.summary(tidy_tracks.survey(board))

def placement_offsets(board):
    """Footprint origin against the centre of its pads, for every assembled SMD part."""
    import fab_jlcpcb
    rows = []; rot = collections.Counter()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if not (fp.GetAttributes() & pcbnew.FP_SMD) or ref.startswith("FID"): continue
        xs = [mm(p.GetPosition().x) for p in fp.Pads()]; ys = [mm(p.GetPosition().y) for p in fp.Pads()]
        # bounding box of the pads' copper, not of their centres (SOT-23: three pads, two rows)
        lo_x = min(mm(p.GetBoundingBox().GetLeft()) for p in fp.Pads()); hi_x = max(mm(p.GetBoundingBox().GetRight()) for p in fp.Pads())
        lo_y = min(mm(p.GetBoundingBox().GetTop()) for p in fp.Pads()); hi_y = max(mm(p.GetBoundingBox().GetBottom()) for p in fp.Pads())
        off = math.hypot((lo_x + hi_x) / 2 - mm(fp.GetPosition().x), (lo_y + hi_y) / 2 - mm(fp.GetPosition().y))
        pkg = fp.GetFPIDAsString().split(":")[-1]
        rows.append((ref, pkg, round(off, 4), fp.GetOrientationDegrees() % 90))
        rot[(pkg, fab_jlcpcb.rotation_fix(pkg))] += 1
    return dict(parts=len(rows), max_offset_mm=max((r[2] for r in rows), default=0.0),
                off_centre=[r for r in rows if r[2] > 0.005], off_axis=[r[0] for r in rows if abs(r[3]) > 0.01 and abs(r[3] - 90) > 0.01],
                rotation_offsets=sorted((pkg, deg, n) for (pkg, deg), n in rot.items()))

def dc_paths(profile):
    """Nets with no DC path to ground or to a driven node."""
    import gen_kicad as g
    g.set_profile(profile); g.COMPONENTS.clear(); g.build()
    nets = set(); adj = collections.defaultdict(set); driven = {"GND"}; via_tank = set()
    for c in g.COMPONENTS:
        pinnet = c["nets"]; nets |= set(pinnet.values())
        if "(opt)" in c["value"] and c["libsym"] == "LINK":
            continue                                           # an unfitted build-option link
        if c["libsym"] == "LINK":
            ps = list(pinnet.values()); adj[ps[0]].add(ps[1]); adj[ps[1]].add(ps[0])
        for grp in DC_GROUPS.get(c["libsym"], []):
            ns = [pinnet[p] for p in grp if p in pinnet]
            for a in ns:
                for b_ in ns:
                    if a != b_: adj[a].add(b_)
        for p in DC_DRIVERS.get(c["libsym"], ()):
            if p in pinnet: driven.add(pinnet[p])
    def reach(skip_tank):
        a2 = collections.defaultdict(set)
        for c in g.COMPONENTS:
            if skip_tank and c["libsym"].startswith("Reverb_Tank"): continue
            if c["libsym"] == "LINK" and "(opt)" not in c["value"]:
                ps = list(c["nets"].values()); a2[ps[0]].add(ps[1]); a2[ps[1]].add(ps[0])
            for grp in DC_GROUPS.get(c["libsym"], []):
                ns = [c["nets"][p] for p in grp if p in c["nets"]]
                for a in ns:
                    for b_ in ns:
                        if a != b_: a2[a].add(b_)
        seen = set(driven); st = list(driven)
        while st:
            u = st.pop()
            for v in a2[u]:
                if v not in seen: seen.add(v); st.append(v)
        return seen
    full = reach(False); notank = reach(True)
    floating = sorted(n for n in nets if n and n not in full)
    return dict(nets=len(nets), floating=floating, only_through_the_tank=sorted(n for n in full if n not in notank),
                offboard_return={n: OFFBOARD_RETURN[profile][n] for n in floating if n in OFFBOARD_RETURN[profile]},
                unexplained=[n for n in floating if n not in OFFBOARD_RETURN[profile]])

def rail_drops(board):
    """Solve each supply net's routed copper as a resistor network at its DC loads."""
    out = []
    for rail, src, loads in RAILS:
        if board.FindNet(rail) is None: continue
        g = loop_audit.NetGraph(board, rail)
        if src not in g.named: continue
        n = len(g.nodes); G = np.zeros((n, n))
        for a, b_, L, w, l in g.edges:
            cond = (w * 1e-3) * ga.THICK[l] * 1e-6 / (ga.RHO * max(L, 1e-3) * 1e-3)
            G[a, a] += cond; G[b_, b_] += cond; G[a, b_] -= cond; G[b_, a] -= cond
        used = [k for k in range(n) if G[k, k] > 0]
        idx = {k: i for i, k in enumerate(used)}
        s = g.named[src][0]
        if s not in idx: continue
        A = G[np.ix_(used, used)].copy(); A[idx[s], idx[s]] += 1e9          # the source pad is the reference
        rows = []
        for pad, ma, what in loads:
            ks = [k for k in g.named.get(pad, []) if k in idx]
            if not ks: rows.append(dict(pad=pad, what=what, mA=ma, missing=True)); continue
            rhs = np.zeros(len(used)); rhs[idx[ks[0]]] = -1.0                 # 1 A drawn at this pad alone
            v1 = np.linalg.solve(A, rhs)
            rows.append(dict(pad=pad, what=what, mA=ma, mohm=round(-float(v1[idx[ks[0]]]) * 1e3, 1), node=ks[0]))
        # all loads together
        rhs = np.zeros(len(used))
        for r in rows:
            if not r.get("missing"): rhs[idx[r["node"]]] -= r["mA"] * 1e-3
        v = np.linalg.solve(A, rhs)
        for r in rows:
            if not r.get("missing"): r["mV"] = round(-float(v[idx[r.pop("node")]]) * 1e3, 2)
        out.append(dict(rail=rail, source=src, loads=rows))
    return out

def audit(profile, path=None):
    path = path or PROF[profile]
    b = pcbnew.LoadBoard(path)
    R = dict(board=os.path.relpath(path, ROOT), profile=profile)
    R["track_ends"] = track_ends(b)
    R["placement"] = placement_offsets(b)
    R["dc"] = dc_paths(profile)
    R["rails"] = rail_drops(b)
    return R

def report(R):
    o = [f"# Offset audit -- {R['board']}\n", "## 1. Track ends\n"]
    te = R["track_ends"]
    o.append("| lands on | ends | off-centre | largest offset | touching with the end cap only |")
    o.append("|---|---:|---:|---:|---:|")
    for kind, label in (("pad", "a pad"), ("via", "a via"), ("track", "another track")):
        t = te[kind]; o.append(f"| {label} | {t['ends']} | **{t['off_centre']}** | {t['max_off']} mm | {t['graze']} |")
    o.append(f"\nFree ends (land on nothing): {te['free_ends']}.\n")
    p = R["placement"]
    o.append("## 2. Placement file\n")
    o.append(f"{p['parts']} SMD footprints: largest distance between a footprint's origin (what the pick-and-place file reports) and the centre of its pads "
             f"**{p['max_offset_mm']} mm**; off-centre: {p['off_centre'] or 'none'}; parts not at a multiple of 90 degrees: {p['off_axis'] or 'none'}.\n")
    o.append("Rotation added to KiCad's angle for JLCPCB's library, per package: " + ", ".join(f"{pkg} {deg:+g} deg ({n})" for pkg, deg, n in p["rotation_offsets"])
             + ". These are the commonly used offsets, not a guarantee: JLCPCB's placement preview is the check.\n")
    d = R["dc"]
    o.append("## 3. DC paths\n")
    o.append(f"{d['nets']} nets. Without a DC path on the board: " + (", ".join(f"`{n}`" for n in d["floating"]) if d["floating"] else "**none**") + ".\n")
    for n, how in d["offboard_return"].items(): o.append(f"- `{n}`: {how}")
    if d["unexplained"]: o.append("- **unexplained:** " + ", ".join(d["unexplained"]))
    if d["only_through_the_tank"]:
        o.append("\nDefined only while the reverb tank is plugged in (through its coils): " + ", ".join(f"`{n}`" for n in d["only_through_the_tank"]) + ".\n")
    o.append("\n## 4. Voltage drop along the supply traces (DC operating point)\n")
    o.append("| rail | from | to | load | trace resistance | drop with every load on |")
    o.append("|---|---|---|---:|---:|---:|")
    for r in R["rails"]:
        for l in r["loads"]:
            if l.get("missing"): continue
            o.append(f"| `{r['rail']}` | {r['source']} | {l['pad']} ({l['what']}) | {l['mA']:g} mA | {l['mohm']} mohm | {l['mV']} mV |")
    o.append("")
    return "\n".join(o)

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("profile", choices=("smd", "tht")); ap.add_argument("--board"); ap.add_argument("--md"); ap.add_argument("--json")
    a = ap.parse_args()
    R = audit(a.profile, a.board); txt = report(R)
    if a.md: open(a.md, "w").write(txt)
    if a.json: json.dump(R, open(a.json, "w"), indent=1)
    print(txt)

if __name__ == "__main__":
    main()
