#!/usr/bin/env python3
"""Make every track end land where it belongs: on the CENTRE of the pad or via it
connects to, and on the centre line of the track it joins.

Both routers leave connections that are electrically fine and geometrically sloppy.
Freerouting ends a trace wherever it first touches a big pad; its session import snaps
to its own grid; the completion router joins a track at the nearest 0.1 mm cell. KiCad's
connectivity (and DRC) only ask whether the copper overlaps, so a 0.5 mm trace that
meets its pad with the rounded end cap alone -- its centre line stopping short of the
pad -- passes. The joint is then a neck narrower than the trace, the solder fillet of a
hand-soldered pad starts beside the trace instead of on it, and a later edit that moves
the part leaves the trace behind without anyone noticing.

For each such end this adds a short segment from the end to the centre (never wider
than the pad / via / track it lands on). KiCad's DRC is the judge: a stub that would
violate a clearance, or that DRC reports as dangling, is taken out again.

    python3 kicad/gen/tidy_tracks.py --in kicad/smd/cambridge_reverb_smd.kicad_pcb
    python3 kicad/gen/tidy_tracks.py --in <board> --report      # measure only, change nothing
"""
import sys, os, math, json, argparse, subprocess, tempfile, collections
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TOL = 0.002                       # mm: closer than this IS on the centre
mm, MM = pcbnew.ToMM, pcbnew.FromMM

def _xy(p): return (mm(p.x), mm(p.y))

def survey(board):
    """Every track end and what it lands on. Returns a list of dicts:
       kind  pad / via / track / free
       off   distance from the end to the centre (pad, via) or centre line (track), mm
       graze True when the centre-line end is OUTSIDE the pad copper (only the end cap touches)"""
    segs = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = collections.defaultdict(list); pads = collections.defaultdict(list); bynet = collections.defaultdict(list)
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA": vias[t.GetNetCode()].append(t)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() > 0: pads[p.GetNetCode()].append((fp.GetReference(), p, p.GetEffectivePolygon()))
    for t in segs: bynet[(t.GetNetCode(), t.GetLayer())].append(t)
    # centres that already HAVE a track end on them, per layer: a second end that merely brushes
    # the same pad or via with its end cap (a junction just outside it) is not a landing
    ends_at = set()
    for t in segs:
        for E in (t.GetStart(), t.GetEnd()): ends_at.add((t.GetLayer(), round(mm(E.x), 3), round(mm(E.y), 3)))
    def has_centre(layer, c): return (layer, round(c[0], 3), round(c[1], 3)) in ends_at
    out = []
    for t in segs:
        w = mm(t.GetWidth()); net = t.GetNetCode(); layer = t.GetLayer()
        for which, E in (("start", t.GetStart()), ("end", t.GetEnd())):
            e = _xy(E); best = None
            for ref, p, poly in pads[net]:
                if not p.IsOnLayer(layer): continue
                c = _xy(p.GetPosition()); d = math.dist(e, c)
                inside = p.HitTest(E)
                if inside or (not has_centre(layer, c) and d < max(mm(p.GetSize().x), mm(p.GetSize().y)) / 2 + w / 2 and poly.Collide(E, int(MM(w / 2 * 0.98)))):
                    cand = dict(kind="pad", off=d, graze=not inside, centre=c, limit=min(mm(p.GetSize().x), mm(p.GetSize().y)), what=f"{ref}.{p.GetNumber()}")
                    if best is None or d < best["off"]: best = cand
            if best is None:
                for v in vias[net]:
                    if not v.IsOnLayer(layer): continue
                    c = _xy(v.GetPosition()); d = math.dist(e, c)
                    if d < mm(v.GetWidth()) / 2 or (not has_centre(layer, c) and d < mm(v.GetWidth()) / 2 + w / 2 * 0.5):
                        cand = dict(kind="via", off=d, graze=d > mm(v.GetWidth()) / 2, centre=c, limit=mm(v.GetWidth()), what="via")
                        if best is None or d < best["off"]: best = cand
            if best is None:
                # another segment of the net on this layer: a shared end point, or a T-joint on its body
                for o in bynet[(net, layer)]:
                    if o is t: continue
                    a, b_ = _xy(o.GetStart()), _xy(o.GetEnd()); L = math.dist(a, b_)
                    if min(math.dist(e, a), math.dist(e, b_)) < TOL:
                        best = dict(kind="track", off=0.0, graze=False, centre=e, limit=mm(o.GetWidth()), what="end"); break
                    if L < 1e-6: continue
                    u = ((e[0] - a[0]) * (b_[0] - a[0]) + (e[1] - a[1]) * (b_[1] - a[1])) / (L * L)
                    if 0.0 < u < 1.0:
                        foot = (a[0] + u * (b_[0] - a[0]), a[1] + u * (b_[1] - a[1])); d = math.dist(e, foot)
                        if d < mm(o.GetWidth()) / 2 + w / 2 * 0.5 and (best is None or d < best["off"]):
                            best = dict(kind="track", off=d, graze=d > mm(o.GetWidth()) / 2, centre=foot, limit=mm(o.GetWidth()), what="body")
            if best is None:
                best = dict(kind="free", off=0.0, graze=False, centre=e, limit=w, what="")
            best.update(track=t, which=which, at=e, width=w, net=t.GetNetname(), layer=board.GetLayerName(layer))
            out.append(best)
    # an off-centre end is RESOLVED when a segment runs from it to the centre (that is what tidy() adds)
    joined = set()
    for t in segs:
        a, b_ = _xy(t.GetStart()), _xy(t.GetEnd()); l = board.GetLayerName(t.GetLayer())
        ka, kb = (round(a[0], 3), round(a[1], 3)), (round(b_[0], 3), round(b_[1], 3))
        joined.add((l, ka, kb)); joined.add((l, kb, ka))
    for s in out:
        s["raw_off"] = s["off"]
        if s["off"] > TOL and (s["layer"], (round(s["at"][0], 3), round(s["at"][1], 3)), (round(s["centre"][0], 3), round(s["centre"][1], 3))) in joined:
            s["off"] = 0.0; s["graze"] = False
    return out

def summary(S):
    r = {}
    for kind in ("pad", "via", "track"):
        k = [s for s in S if s["kind"] == kind]
        off = [s for s in k if s["off"] > TOL]
        r[kind] = dict(ends=len(k), off_centre=len(off), max_off=round(max((s["off"] for s in off), default=0.0), 3),
                       graze=sum(1 for s in off if s["graze"]),
                       worst=[(s["what"], s["net"], round(s["off"], 2)) for s in sorted(off, key=lambda s: -s["off"])[:5]])
    r["free_ends"] = sum(1 for s in S if s["kind"] == "free")
    return r

def drc(pcb):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f: tmp = f.name
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", tmp, pcb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(tmp)); os.remove(tmp)
    bad = [(v["type"], [(i["pos"]["x"], i["pos"]["y"]) for i in v["items"]]) for v in d.get("violations", [])
           if v["severity"] == "error" or v["type"] in ("track_dangling", "via_dangling")]
    return len(d.get("unconnected_items", [])), bad

def tidy(pcb, verbose=True):
    """Add the centring stubs to the board FILE; returns (added, kept, before, after)."""
    from route_board import refill
    board = pcbnew.LoadBoard(pcb)
    before = summary(survey(board))
    unconn0, bad0 = drc(pcb)
    todo = [s for s in survey(board) if s["kind"] in ("pad", "via", "track") and s["off"] > TOL]
    seen = set(); stubs = []
    for s in todo:
        key = (s["layer"], round(s["at"][0], 4), round(s["at"][1], 4), round(s["centre"][0], 4), round(s["centre"][1], 4))
        if key in seen: continue
        seen.add(key)
        t = s["track"]
        n = pcbnew.PCB_TRACK(board)
        n.SetStart(pcbnew.VECTOR2I(MM(s["at"][0]), MM(s["at"][1]))); n.SetEnd(pcbnew.VECTOR2I(MM(s["centre"][0]), MM(s["centre"][1])))
        n.SetWidth(MM(min(s["width"], s["limit"]))); n.SetLayer(t.GetLayer()); n.SetNetCode(t.GetNetCode())
        board.Add(n); stubs.append((n, s))
    keep = open(pcb, "rb").read()
    removed = 0
    for rounds in range(4):
        refill(board); pcbnew.SaveBoard(pcb, board)
        unconn, bad = drc(pcb)
        new = [b for b in bad if b not in bad0]
        if not new and unconn <= unconn0:
            break
        # take out every stub that sits at a reported position
        pts = [(x, y) for _, items in new for (x, y) in items]
        board = pcbnew.LoadBoard(pcb)
        victims = []
        for t in board.GetTracks():
            if t.GetClass() != "PCB_TRACK": continue
            a, b_ = _xy(t.GetStart()), _xy(t.GetEnd())
            for (n_, s) in stubs:
                sa, sb = _xy(n_.GetStart()), _xy(n_.GetEnd())
                if math.dist(a, sa) < 1e-4 and math.dist(b_, sb) < 1e-4 and t.GetLayer() == n_.GetLayer():
                    mid = ((a[0] + b_[0]) / 2, (a[1] + b_[1]) / 2)
                    if any(math.dist(mid, q) < max(1.0, math.dist(a, b_)) for q in pts): victims.append(t)
                    break
        if not victims:
            open(pcb, "wb").write(keep); board = pcbnew.LoadBoard(pcb)       # could not pin it down: undo everything
            removed = len(stubs); stubs = []
            break
        for t in victims: board.Delete(t)
        removed += len(victims)
    else:
        open(pcb, "wb").write(keep); board = pcbnew.LoadBoard(pcb); removed = len(stubs); stubs = []
    after = summary(survey(pcbnew.LoadBoard(pcb)))
    if verbose:
        print(f"tidy: {len(todo)} off-centre ends, {len(seen)} centring stubs added, {removed} taken out again by DRC")
        for kind in ("pad", "via", "track"):
            print(f"  {kind:5s} ends {after[kind]['ends']:4d}: off-centre {before[kind]['off_centre']:3d} -> {after[kind]['off_centre']:3d} "
                  f"(max {before[kind]['max_off']} -> {after[kind]['max_off']} mm; grazing {before[kind]['graze']} -> {after[kind]['graze']})")
    return len(seen), len(seen) - removed, before, after

def prune_dangling(pcb, verbose=True):
    """The via escapes placed before routing (stitch.fanout_taps) are an OFFER. Where the
    router reached the pad on the component side instead, the via is left connected on one
    layer only: take it out. Its stub stays if the router ran on from it (it is then part
    of the trace); a stub or any other track left with a free end is a spur and goes too.
    Only non-ground vias and tracks; KiCad's DRC decides, and anything that breaks a
    connection or a rule is put back."""
    from route_board import refill
    vias = spurs = 0
    for _ in range(8):
        unconn0, bad0 = drc(pcb)
        vpts = [q for kind, items in bad0 if kind == "via_dangling" for q in items[:1]]
        tpts = [q for kind, items in bad0 if kind == "track_dangling" for q in items[:1]]
        if not vpts and not tpts: break
        keep = open(pcb, "rb").read(); board = pcbnew.LoadBoard(pcb); nv = nt = 0
        for (x, y) in vpts:
            via = next((t for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() != "GND" and math.dist(_xy(t.GetPosition()), (x, y)) < 0.01), None)
            if via is not None: board.Delete(via); nv += 1
        if not nv:                 # spurs only once no via is left to explain them
            for (x, y) in tpts:
                for t in [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() != "GND"
                          and min(math.dist(_xy(t.GetStart()), (x, y)), math.dist(_xy(t.GetEnd()), (x, y))) < 0.01][:1]:
                    board.Delete(t); nt += 1
        if not nv and not nt: break
        refill(board); pcbnew.SaveBoard(pcb, board)
        unconn, bad = drc(pcb)
        if unconn > unconn0 or [b_ for b_ in bad if b_[0] not in ("via_dangling", "track_dangling") and b_ not in bad0]:
            open(pcb, "wb").write(keep); break
        vias += nv; spurs += nt
    if verbose and (vias or spurs): print(f"unused via escapes removed: {vias} (and {spurs} spur track(s) they left)")
    return vias

def _segd(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)

def necks(board, limit):
    """Places where a zone fill necks down below `limit` between two bodies of copper:
    [(width, (x, y), layer name, zone)].

    KiCad prunes fill narrower than the zone's minimum width, but two bodies that part
    and meet again behind a pair of via antipads, or along the edge of a pour, can still be
    left joined by a strip a few 0.01 mm wide -- the "connection_width" warning of its DRC,
    which names the zone but not the place. This is the same test as KiCad's
    (drc_test_provider_connection_width.cpp), so that it finds what KiCad reports and no
    more: a vertex where the copper's edge is concave, another vertex closer than the
    limit with copper between the two, and on each side an edge that moves away by more
    than the limit in both x and y before it comes round (a long straight strip is not a
    neck)."""
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea(): continue
        for lid in z.GetLayerSet().Seq():
            ps = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid)); ps.Unfracture(pcbnew.SHAPE_POLY_SET.PM_FAST); rings = []
            for i in range(ps.OutlineCount()):
                o = ps.Outline(i); rings.append(([_xy(o.CPoint(k)) for k in range(o.PointCount())], False))
                for h in range(ps.HoleCount(i)):
                    hh = ps.Hole(i, h); rings.append(([_xy(hh.CPoint(k)) for k in range(hh.PointCount())], True))
            H = collections.defaultdict(list); sign = []
            for r, (ring, hole) in enumerate(rings):
                A2 = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1])); sign.append(1 if A2 > 0 else -1)
                for k, q in enumerate(ring): H[(int(q[0] // limit), int(q[1] // limit))].append((r, k))
            def concave(r, k):                  # is the COPPER's edge concave at this vertex?
                ring, hole = rings[r]; n = len(ring); p0, p1, p2 = ring[k - 1], ring[k], ring[(k + 1) % n]
                c = (p1[0] - p0[0]) * (p2[1] - p1[1]) - (p1[1] - p0[1]) * (p2[0] - p1[0])
                if abs(c) < 1e-12: return False
                return ((c > 0) == (sign[r] > 0)) == hole
            def substantial(r, k, r2, k2):
                ring = rings[r][0]; n = len(ring); x0, y0 = ring[k]
                for step in (1, -1):
                    xc = yc = False; j = k
                    for _ in range(n):
                        j = (j + step) % n
                        if r2 == r and j == k2: break
                        if abs(ring[j][0] - x0) > limit: xc = True
                        if abs(ring[j][1] - y0) > limit: yc = True
                        if xc and yc: break
                    if not (xc and yc): return False
                return True
            found = []
            for r, (ring, hole) in enumerate(rings):
                n = len(ring)
                for k, q in enumerate(ring):
                    if not concave(r, k): continue
                    gx, gy = int(q[0] // limit), int(q[1] // limit); best = None
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            for (r2, k2) in H.get((gx + dx, gy + dy), ()):
                                if r2 == r and min(abs(k2 - k), n - abs(k2 - k)) <= 1: continue
                                q2 = rings[r2][0][k2]; d = math.dist(q, q2)
                                if not (1e-6 < d < limit) or (best and d >= best[0]): continue
                                m = ((q[0] + q2[0]) / 2, (q[1] + q2[1]) / 2)
                                if not ps.Contains(pcbnew.VECTOR2I(MM(m[0]), MM(m[1]))): continue
                                if substantial(r, k, r2, k2) and substantial(r2, k2, r, k): best = (d, m)
                    if best: found.append((round(best[0], 4), best[1]))
            found.sort(); kept = []
            code = z.GetNetCode()
            def healed(m):                      # a pad, via or track of the same net lies across it: KiCad sees one piece of copper
                P = pcbnew.VECTOR2I(MM(m[0]), MM(m[1]))
                for tr in board.GetTracks():
                    if tr.GetNetCode() != code or not tr.IsOnLayer(lid): continue
                    if tr.GetClass() == "PCB_VIA":
                        if math.dist(m, _xy(tr.GetPosition())) <= mm(tr.GetWidth()) / 2: return True
                    elif _segd(m, _xy(tr.GetStart()), _xy(tr.GetEnd())) <= mm(tr.GetWidth()) / 2: return True
                return any(pd.GetNetCode() == code and pd.IsOnLayer(lid) and pd.HitTest(P) for fp in board.GetFootprints() for pd in fp.Pads())
            for d, m in found:
                if all(math.dist(m, m2) > 0.5 for _, m2 in kept) and not healed(m): kept.append((d, m))
            out += [(d, m, board.GetLayerName(lid), z) for d, m in kept]
    return sorted(out, key=lambda n: n[:3])

def _drc_width(pcb):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f: tmp = f.name
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", tmp, pcb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(tmp)); os.remove(tmp)
    return [v for v in d.get("violations", []) if v["type"] == "connection_width"]

def close_necks(pcb, verbose=True):
    """Copper necks narrower than the board's minimum connection width: an acid trap in
    the making and a strip that may or may not survive etching.
      - in a zone fill: a 0.6 mm no-pour dot on that layer joins the two openings beside it;
      - between a pad or via and a track of its own net that brushes past it: a short
        segment from the centre to the track makes the brush a joint.
    KiCad's DRC counts the warnings and vetoes anything that would cut a net."""
    from route_board import refill
    closed = 0
    for _ in range(6):
        W = _drc_width(pcb); n0 = len(W)
        if not n0: break
        unconn0, bad0 = drc(pcb)
        board = pcbnew.LoadBoard(pcb); keep = open(pcb, "rb").read()
        limit = board.GetDesignSettings().m_MinConn / 1e6 or 0.2
        notes = []
        # (a) pad / via against a track
        for v in W:
            its = v["items"]
            if len(its) != 2 or not any(i["description"].startswith("Track") for i in its) or all(i["description"].startswith("Track") for i in its): continue
            ti = next(i for i in its if i["description"].startswith("Track")); oi = next(i for i in its if i is not ti)
            trk = next((t for t in board.GetTracks() if t.m_Uuid.AsString() == ti["uuid"]), None)
            if trk is None: continue
            c = (oi["pos"]["x"], oi["pos"]["y"]); a, e = _xy(trk.GetStart()), _xy(trk.GetEnd())
            dx, dy = e[0] - a[0], e[1] - a[1]; L2 = dx * dx + dy * dy
            u = 0 if L2 == 0 else max(0, min(1, ((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / L2))
            f = (a[0] + u * dx, a[1] + u * dy)
            if math.dist(c, f) < 0.01 or math.dist(c, f) > 3.0: continue
            s = pcbnew.PCB_TRACK(board); s.SetStart(pcbnew.VECTOR2I(MM(c[0]), MM(c[1]))); s.SetEnd(pcbnew.VECTOR2I(MM(f[0]), MM(f[1])))
            s.SetWidth(trk.GetWidth()); s.SetLayer(trk.GetLayer()); s.SetNetCode(trk.GetNetCode()); board.Add(s)
            notes.append(f"narrow joint made solid: {trk.GetNetname()} on {board.GetLayerName(trk.GetLayer())} at ({c[0]:.2f}, {c[1]:.2f}), {math.dist(c, f):.2f} mm segment")
        # (b) zone fills
        if any(len(v["items"]) == 1 and v["items"][0]["description"].startswith("Zone") for v in W):
            k0 = sum(1 for z in board.Zones() if z.GetZoneName().startswith("neck_"))
            for k, (w, (x, y), layer, zone) in enumerate(necks(board, limit)):
                z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetZoneName(f"neck_{k0 + k + 1}")
                z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowCopperPour(True)
                z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
                ls = pcbnew.LSET(); ls.addLayer(board.GetLayerID(layer)); z.SetLayerSet(ls)
                sps = z.Outline(); sps.NewOutline()
                for i in range(16):
                    a = 2 * math.pi * i / 16
                    sps.Append(MM(x + 0.3 * math.cos(a)), MM(y + 0.3 * math.sin(a)))
                board.Add(z)
                notes.append(f"plane neck closed: {w:.3f} mm of {zone.GetNetname()} on {layer} at ({x:.2f}, {y:.2f})")
        if not notes:
            if verbose: print(f"close_necks: KiCad reports {n0} narrow connection(s) that the search does not find -- left alone")
            break
        refill(board); pcbnew.SaveBoard(pcb, board)
        unconn, bad = drc(pcb)
        if unconn > unconn0 or [b_ for b_ in bad if b_ not in bad0] or len(_drc_width(pcb)) >= n0:
            open(pcb, "wb").write(keep)
            if verbose: print(f"close_necks: {len(notes)} change(s) did not help -- taken out again: " + "; ".join(notes)[:300])
            break
        closed += len(notes)
        if verbose:
            for line in notes: print(line)
    return closed

def break_rings(pcb, verbose=True):
    """Open every closed loop in the routed copper: take out the higher-resistance branch of
    the ring (whole tracks, the stretch of a track between two junctions, and vias that only
    served it). A ring is a redundant connection -- and a shorted turn for any stray field.
    KiCad's DRC decides whether the board is still whole; if not, the branch goes back."""
    import loop_audit, ground_audit as ga
    from route_board import refill
    opened = 0; skip = set()
    for _ in range(30):
        board = pcbnew.LoadBoard(pcb)
        nets = sorted({p.GetNetname() for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() and p.GetNetname() != "GND"})
        job = None
        for net in nets:
            g = loop_audit.NetGraph(board, net)
            for poly, es, cyc in g.rings():
                key = (net, round(abs(loop_audit.poly_area(poly)), 1))
                if key in skip or g.hole(poly, es) < loop_audit.RING_MIN: continue
                job = (net, g, poly, es, cyc, key); break
            if job: break
        if job is None: break
        net, g, poly, es, cyc, key = job
        deg = {k: len({v for v, _ in g.uadj[k]}) for k in cyc}
        branchy = [i for i, k in enumerate(cyc) if deg[k] >= 3 or g.nodes[k][0] == "pad"]
        if not branchy: skip.add(key); continue
        # chains of the ring between consecutive branch points
        chains = []
        for a, b_ in zip(branchy, branchy[1:] + [branchy[0] + len(cyc)]):
            idx = [i % len(cyc) for i in range(a, b_ + 1)]
            ce = []
            for p, q in zip(idx, idx[1:]):
                kp, kq = cyc[p], cyc[q]
                n = next((n for v, n in g.uadj[kp] if v == kq), None)
                if n is not None: ce.append(n)
            if not ce: continue
            ohm = sum(ga.RHO * (g.edges[n][2] * 1e-3) / ((g.edges[n][3] * 1e-3) * ga.THICK[g.edges[n][4]] * 1e-6) for n in ce)
            locked = any(g.piece[n] is not None and g.tracks[g.piece[n][0]].IsLocked() for n in ce) or any(g.piece[n] is None for n in ce)
            chains.append((ohm, ce, [cyc[i] for i in idx[1:-1]], locked))
        keep = open(pcb, "rb").read(); unconn0, bad0 = drc(pcb); done = False
        for ohm, ce, inner, locked in sorted(chains, key=lambda c: -c[0]):
            if locked: continue
            board = pcbnew.LoadBoard(pcb); g2 = loop_audit.NetGraph(board, net)      # fresh objects, same indices
            cover = collections.defaultdict(list)
            for n in ce: cover[g.piece[n][0]].append((g.piece[n][1], g.piece[n][2]))
            for ti, spans in cover.items():
                t = g2.tracks[ti]; a, e = _xy(t.GetStart()), _xy(t.GetEnd()); L = math.dist(a, e)
                lo, hi = min(s_[0] for s_ in spans), max(s_[1] for s_ in spans)
                pt = lambda d: pcbnew.VECTOR2I(MM(a[0] + (e[0] - a[0]) * d / L), MM(a[1] + (e[1] - a[1]) * d / L))
                if lo <= 1e-6 and hi >= L - 1e-6: board.Delete(t)
                elif lo <= 1e-6: t.SetStart(pt(hi))
                elif hi >= L - 1e-6: t.SetEnd(pt(lo))
                else:
                    n2 = pcbnew.PCB_TRACK(board); n2.SetStart(pt(hi)); n2.SetEnd(t.GetEnd()); n2.SetWidth(t.GetWidth()); n2.SetLayer(t.GetLayer()); n2.SetNetCode(t.GetNetCode())
                    t.SetEnd(pt(lo)); board.Add(n2)
            for k in inner:
                if g.nodes[k][0] == "via":
                    v = next((v for kk, v in g2.vias.items() if abs(g2.nodes[kk][1] - g.nodes[k][1]) < 1e-4 and abs(g2.nodes[kk][2] - g.nodes[k][2]) < 1e-4), None)
                    if v is not None and not v.IsLocked(): board.Delete(v)
            refill(board); pcbnew.SaveBoard(pcb, board)
            unconn, bad = drc(pcb)
            if unconn <= unconn0 and not [b_ for b_ in bad if b_ not in bad0]:
                opened += 1; done = True
                if verbose: print(f"ring opened: {net}, {abs(loop_audit.poly_area(poly)):.1f} mm2 -- removed the {ohm * 1e3:.0f} mohm branch ({len(cover)} track(s))")
                break
            open(pcb, "wb").write(keep)
        if not done: skip.add(key)
    if verbose and skip: print(f"rings left closed (no branch could be removed cleanly): {sorted(skip)}")
    return opened

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="src", required=True); ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        r = summary(survey(pcbnew.LoadBoard(a.src)))
        for kind in ("pad", "via", "track"):
            print(f"{kind:5s} ends {r[kind]['ends']:4d}: {r[kind]['off_centre']} off-centre, max {r[kind]['max_off']} mm, {r[kind]['graze']} touching by the end cap only; worst {r[kind]['worst'][:3]}")
        print("free ends:", r["free_ends"])
        return
    prune_dangling(a.src)
    break_rings(a.src)
    tidy(a.src)
    close_necks(a.src)

if __name__ == "__main__":
    main()
