#!/usr/bin/env python3
"""Ground vias: the copper that makes four layers behave as one ground.

Stack (errata #31): F.Cu signal + GND pour / In1 solid GND plane / In2 signal / B.Cu
solid GND plane. Through-hole ground pins reach the In1 plane through their own holes;
everything else is tied together here.

  fanout(board, pcb)   before routing: every SMD ground pad gets a short track to a via
                       beside it (never in the pad, never under a part), locked so the
                       autorouter works around it. Two pads may share a via.
  stitch(board, pcb)   after routing: ground vias on a regular grid wherever all layers
                       are free, so no piece of the top pour and no region of the two
                       planes is further than a fraction of a wavelength from a tie
                       (7.5 mm = lambda/10 at 1.9 GHz in FR4).
  split_ct / join_ct   before / after routing: the rectifier's side of power ground is a
                       net of its own while the routers work, with a locked run from the
                       centre tap to the reservoir pad (errata #43).
  nfp(board)           non-functional pads off the inner layers (pads and vias keep
                       copper only where something connects): a plane's opening around
                       a foreign pin is then set by the hole, not by the pad, and the
                       web between 2.54 mm pins survives.

    python3 kicad/gen/stitch.py --in kicad/smd/cambridge_reverb_smd.kicad_pcb   # stitch + nfp a routed board
"""
import sys, os, math, argparse
import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import finish_routes as fr

STITCH_PITCH = 7.5        # mm
STITCH_REACH = 2.5        # a grid node may slide this far to find a free spot
FILL_FROM = 6.0           # mm: after the grid pass, no free spot stays further than this from a ground via
STITCH_PAD_CLEAR = 1.0    # a stitching via stays this far from ANY pad: most of them are soldered by hand
FANOUT_REACH = 3.0        # an SMD ground pad's via is at most this far from the pad centre
VIA_D, VIA_DRILL = 0.8, 0.4

def _via(board, x, y, code, locked=True):
    v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(fr.mm(x), fr.mm(y)))
    v.SetWidth(fr.mm(VIA_D)); v.SetDrill(fr.mm(VIA_DRILL)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(code); v.SetLocked(locked)
    board.Add(v)
    return v

def _free_cells(vb, grid, cx, cy, reach):
    """Free via cells within `reach` of (cx, cy), nearest first."""
    iy, ix = grid.cell(cx, cy); r = int(reach / fr.RES)
    y0, y1 = max(0, iy - r), min(grid.H, iy + r + 1); x0, x1 = max(0, ix - r), min(grid.W, ix + r + 1)
    sub = ~vb[y0:y1, x0:x1]
    ys, xs = np.nonzero(sub)
    if len(ys) == 0:
        return []
    d2 = (ys + y0 - iy) ** 2 + (xs + x0 - ix) ** 2
    order = np.argsort(d2, kind="stable")
    return [(int(ys[k] + y0), int(xs[k] + x0)) for k in order if d2[k] <= r * r]

def _line_free(blk, grid, a, b, own):
    (y0, x0), (y1, x1) = a, b
    n = max(abs(y1 - y0), abs(x1 - x0), 1) * 2
    for k in range(n + 1):
        y = int(round(y0 + (y1 - y0) * k / n)); x = int(round(x0 + (x1 - x0) * k / n))
        if blk[y, x] and not own[y, x]:
            return False
    return True

# ---- the charging pulses get power-ground copper of their own (errata #43) -----------------
CT_GROUP = ("T1.2", "C103.2", "C104.2", "JP_BR.2")   # the rectifier's side of power ground: centre tap, snubbers, bridge link
CT_NET, CT_HUB = "PGND_CT", "C_main.2"                # ... and where it meets the rest: the reservoir's minus pad
CT_WIDTHS = (2.5, 2.0)                                # mm, tried in turn before the class width (the run is on 0.5 oz inner copper)

def _pads(board):
    return {f"{fp.GetReference()}.{p.GetNumber()}": p for fp in board.GetFootprints() for p in fp.Pads()}

def split_ct(board, pcb):
    """Before routing: put the rectifier's power-ground pads on a net of their own
    (PGND_CT) and lay its one run from the transformer centre tap to the reservoir, locked.

    PGND is one net, and an autorouter joins the pads of a net in whatever order is
    shortest. Twice out of three routings on 2026-11-12 it hung the star link, or the
    LM1875's ground pin, on the trace that carries the reservoir's charging pulses from
    the centre tap -- 36 to 51 mohm of shared copper. As built that is harmless (the star
    is still one point). It is what turns a punctured heatsink insulator from a fault
    worth 80 uV of hum into one worth 20 mV: the tab is then a second ground at a place
    that moves by tens of millivolts with every charging pulse.

    With two nets the routers cannot share anything. The run stops one clearance short
    of the reservoir pad; join_ct() adds the last 2 mm and makes it PGND again, so the
    finished board has the netlist of the schematic and a power ground that is a star AT
    the reservoir: charging pulses on one arm, everything else on the others.
    Returns (pads moved, run length mm, width mm) or None if the board has no such group."""
    pads = _pads(board); hub, src = pads.get(CT_HUB), pads.get(CT_GROUP[0])
    if hub is None or src is None or hub.GetNetname() != "PGND" or src.GetNetname() != "PGND":
        return None
    ni = pcbnew.NETINFO_ITEM(board, CT_NET); board.Add(ni); n = 0
    for k in CT_GROUP:
        if k in pads and pads[k].GetNetname() == "PGND": pads[k].SetNet(ni); n += 1
    # Nothing is routed yet, so no through-hole pad has copper on the inner layers (errata #31) --
    # but any of them may get it back once a router connects there. The run has to clear the
    # PADS, not the holes: show every pad at full size while the grid is read. The two ends of
    # the run keep their copper on every layer for good.
    bare = [p for p in pads.values() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetRemoveUnconnected()]
    for p in bare: p.SetRemoveUnconnected(False)
    rules = fr.Rules(pcb); fr.configure(board); grid = fr.Grid(board, rules)
    for p in bare:
        if p not in (hub, src): p.SetRemoveUnconnected(True); p.SetKeepTopBottom(True)
    for p in (hub, src): p.SetRemoveUnconnected(False)
    inner = [l for l in fr.ROUTE_LAYERS if l.startswith("In")]
    layer = inner[0] if inner else fr.ROUTE_LAYERS[0]
    sx, sy = fr.to_mm(src.GetPosition().x), fr.to_mm(src.GetPosition().y)
    for w in [w for w in CT_WIDTHS if w > rules.width(CT_NET)] + [rules.width(CT_NET)]:
        blk = grid.blocked(CT_NET, w)[layer]
        halo = np.zeros((grid.H, grid.W), bool)
        grid.pad_shape(halo, hub, w / 2 + rules.clearance(CT_NET, "PGND", False) + fr.SAFETY + fr.PAINT + 2 * fr.RES)
        dst = {(int(y), int(x)) for y, x in zip(*np.nonzero(halo & ~blk))}
        if not dst: continue
        full = np.ones((grid.H, grid.W), bool)
        path = fr.astar(grid, {l: (blk if l == layer else full) for l in fr.ROUTE_LAYERS}, full, {grid.cell(sx, sy)}, [layer], dst, [layer])
        if not path: continue
        before = {id(t) for t in board.GetTracks()}
        fr.add_path(board, grid, rules, CT_NET, w, path, (sx, sy), grid.pos(*path[-1][1:]))
        length = 0.0
        for t in board.GetTracks():
            if t.GetClass() == "PCB_TRACK" and t.GetNetname() == CT_NET: t.SetLocked(True); length += fr.to_mm(t.GetLength())
        return n, round(length, 1), w
    print(f"  split_ct: no way from {CT_GROUP[0]} to {CT_HUB} on {layer} -- the rectifier group stays on PGND")
    pg = board.FindNet("PGND")
    for k in CT_GROUP:
        if k in pads and pads[k].GetNetname() == CT_NET: pads[k].SetNet(pg)
    board.Remove(ni)
    return None

def join_ct(pcb):
    """After routing: the last stretch of the centre-tap run, into the centre of the
    reservoir pad, and PGND_CT becomes PGND again. The stretch is as wide as the run if
    KiCad's DRC lets it be -- a trace that hugs the waist between the run's end and the pad
    can be a few 0.01 mm too close to a 2.5 mm stretch -- else the next narrower width
    (3 mm of it: 1 mm wide is still under 3 mohm). Returns a line for the log, or None if the
    board has no split."""
    if pcbnew.LoadBoard(pcb).FindNet(CT_NET) is None: return None
    keep = open(pcb, "rb").read(); _, errs0 = fr.unconnected(pcb); last = None
    for k in range(4):
        board = pcbnew.LoadBoard(pcb); ni = board.FindNet(CT_NET)
        pg = board.FindNet("PGND"); hub = _pads(board)[CT_HUB]
        hx, hy = fr.to_mm(hub.GetPosition().x), fr.to_mm(hub.GetPosition().y)
        ends = [(math.dist((fr.to_mm(q.x), fr.to_mm(q.y)), (hx, hy)), t, q) for t in board.GetTracks()
                if t.GetClass() == "PCB_TRACK" and t.GetNetname() == CT_NET and t.IsLocked() for q in (t.GetStart(), t.GetEnd())]
        if not ends:
            raise SystemExit(f"join_ct: {CT_NET} has no pre-routed run -- the board was not generated with split_ct()")
        d, t, q = min(ends, key=lambda e: e[0])
        reach = fr.to_mm(max(hub.GetSize().x, hub.GetSize().y)) / 2 + fr.to_mm(t.GetWidth()) + 1.5
        if d > reach:
            raise SystemExit(f"join_ct: the {CT_NET} run ends {d:.1f} mm from {CT_HUB} (expected within {reach:.1f} mm)")
        widths = [fr.to_mm(t.GetWidth())] + [w for w in (2.0, 1.5, 1.0) if w < fr.to_mm(t.GetWidth())]
        if k >= len(widths): break
        w = widths[k]
        s = pcbnew.PCB_TRACK(board); s.SetStart(pcbnew.VECTOR2I(q.x, q.y)); s.SetEnd(hub.GetPosition())
        s.SetWidth(fr.mm(w)); s.SetLayer(t.GetLayer()); s.SetNet(ni); s.SetLocked(True); board.Add(s)
        n = 0
        for it in list(board.GetTracks()) + [p for fp in board.GetFootprints() for p in fp.Pads()]:
            if it.GetNetname() == CT_NET: it.SetNet(pg); n += 1
        board.Remove(ni)
        fr.refill(board); pcbnew.SaveBoard(pcb, board)
        todo, errs = fr.unconnected(pcb)
        last = f"centre-tap return joined to PGND at {CT_HUB}: the last {d:.1f} mm, {w:g} mm wide ({n} items back on PGND)"
        if not todo and len(errs) <= len(errs0): return last
        if k + 1 < len(widths): open(pcb, "wb").write(keep)
    return (last or "join_ct: nothing done") + " -- DRC still objects, see below"

def fanout_taps(board, pcb):
    """A via escape for every SMD pad of a small part that only TAPS a high-current net.

    The LM1875's bias divider hangs on +33V5, the feedback resistor on PA_OUT, the star link
    on the speaker return, the bridge snubbers on the secondary: 0805 pads on nets the
    routers treat as 1.5 mm traces with 0.4 mm of clearance. The autorouter leaves several
    of them for last, and twice in three runs it had by then run a fat trace round the bias
    divider's +33V5 pad -- no way in on the component side, and none through the board
    because nothing may put a via beside an SMD pad afterwards (2026-11-12). With the via
    and a 0.5 mm stub in place BEFORE routing the pad is reachable from the inner layer
    whatever happens around it. Returns the number of pads fanned out."""
    rules = fr.Rules(pcb); fr.configure(board)
    n = 0
    nets = sorted({p.GetNetname() for fp in board.GetFootprints() for p in fp.Pads()
                   if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetNetname() and rules.klass(p.GetNetname()) == "HighCurrent" and fr.light_ref(fp.GetReference())})
    for net in nets:
        only = {fp.GetReference() for fp in board.GetFootprints() if fr.light_ref(fp.GetReference())}
        n += fanout(board, pcb, only=only, net=net)
    return n

def fanout(board, pcb, only=None, net="GND"):
    """A via to the planes for every SMD ground pad (or just the refs in `only`); with
    `net`, the same via + stub for the SMD pads of another net (see fanout_taps)."""
    if board.FindNet(net) is None:
        return 0
    rules = fr.Rules(pcb); fr.configure(board); grid = fr.Grid(board, rules)
    code = board.FindNet(net).GetNetCode()
    pads = [(fp.GetReference(), p) for fp in board.GetFootprints() for p in fp.Pads()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetNetname() == net and (only is None or fp.GetReference() in only)]
    if not pads:
        return 0
    w = min(rules.width(net), 0.5)
    vb = grid.via_blocked(net, None); blk = grid.blocked(net, w)["F.Cu"]
    placed = []; n = 0
    for ref, p in pads:
        c = p.GetPosition(); px, py = fr.to_mm(c.x), fr.to_mm(c.y); start = grid.cell(px, py)
        own = np.zeros((grid.H, grid.W), bool); grid.pad_shape(own, p, 0.05)
        # an existing fan-out via within reach (a neighbour's) is the first choice
        cands = [grid.cell(vx, vy) for vx, vy in placed if math.dist((vx, vy), (px, py)) <= FANOUT_REACH] + _free_cells(vb, grid, px, py, FANOUT_REACH)
        for cell in cands:
            if not _line_free(blk, grid, start, cell, own):
                continue
            vx, vy = grid.pos(*cell)
            if not any(math.dist((vx, vy), q) < 0.01 for q in placed):
                _via(board, vx, vy, code); placed.append((vx, vy))
                grid.seg(vb, vx, vy, vx, vy, VIA_DRILL + rules.hole_hole + fr.SAFETY)      # next via: hole-to-hole
            t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(fr.mm(px), fr.mm(py))); t.SetEnd(pcbnew.VECTOR2I(fr.mm(vx), fr.mm(vy)))
            t.SetWidth(fr.mm(w)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code); t.SetLocked(True); board.Add(t)
            n += 1
            break
        else:
            print(f"  fan-out: no via site within {FANOUT_REACH} mm of {ref} pad {p.GetNumber()} (it still sits solid in the top pour)")
    return n

def stitch(board, pcb, pitch=STITCH_PITCH):
    """Ground vias on a grid, wherever a via fits on every layer."""
    if board.FindNet("GND") is None:
        return 0
    rules = fr.Rules(pcb); fr.configure(board); grid = fr.Grid(board, rules)
    code = board.FindNet("GND").GetNetCode()
    vb = grid.via_blocked("GND", None)
    from scipy import ndimage
    g = np.zeros((grid.H, grid.W), bool)
    for fp in board.GetFootprints():
        for p in fp.Pads(): grid.pad_shape(g, p)
    vb |= ndimage.distance_transform_edt(~g) * fr.RES < (VIA_D / 2 + STITCH_PAD_CLEAR)
    have = [(fr.to_mm(t.GetPosition().x), fr.to_mm(t.GetPosition().y)) for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
    W, H = grid.W * fr.RES, grid.H * fr.RES
    nx, ny = int(W // pitch), int(H // pitch); n = 0
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = grid.x0 + (W - nx * pitch) / 2 + i * pitch; y = grid.y0 + (H - ny * pitch) / 2 + j * pitch
            if any(math.dist((x, y), q) < pitch * 0.6 for q in have):
                continue                                   # this neighbourhood is tied already
            cells = _free_cells(vb, grid, x, y, STITCH_REACH)
            if not cells:
                continue
            vx, vy = grid.pos(*cells[0])
            _via(board, vx, vy, code); have.append((vx, vy)); n += 1
            grid.seg(vb, vx, vy, vx, vy, VIA_DRILL + rules.hole_hole + fr.SAFETY)
    # fill pass: a grid node that found no free spot within its reach leaves a hole in the
    # stitching (traces of the routed power ground, a dense row of parts). Wherever a FREE
    # cell is still further than FILL_FROM from every ground via, put a via on the one that
    # is furthest -- largest hole first -- until none is left.
    nfill = 0
    for _ in range(400):
        m = np.ones((grid.H, grid.W), bool)
        for (x, y) in have:
            iy, ix = grid.cell(x, y)
            if 0 <= iy < grid.H and 0 <= ix < grid.W: m[iy, ix] = False
        far = ndimage.distance_transform_edt(m) * fr.RES
        far[vb] = 0.0
        if far.max() < FILL_FROM:
            break
        iy, ix = np.unravel_index(int(far.argmax()), far.shape)
        vx, vy = grid.pos(int(iy), int(ix))
        _via(board, vx, vy, code); have.append((vx, vy)); nfill += 1
        grid.seg(vb, vx, vy, vx, vy, VIA_DRILL + rules.hole_hole + fr.SAFETY)
    return n + nfill

def nfp(board):
    """Remove unconnected pad / via copper on the inner layers (keep the outer ends)."""
    n = 0
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                p.SetRemoveUnconnected(True); p.SetKeepTopBottom(True); n += 1
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            t.SetRemoveUnconnected(True); t.SetKeepStartEnd(True); n += 1
    return n

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="src", required=True)
    a = ap.parse_args()
    board = pcbnew.LoadBoard(a.src)
    nb = fr.through_vias(board)                     # (belt and braces: route_board.py already does this)
    if nb:
        print(f"{nb} blind via(s) made through vias")
    n = stitch(board, a.src); m = nfp(board)
    fr.refill(board)
    pcbnew.SaveBoard(a.src, board)
    total = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND")
    print(f"stitching: {n} ground vias added on a {STITCH_PITCH} mm grid and in the gaps it left ({total} ground vias in all); unused inner-layer copper removed from {m} pads / vias")

if __name__ == "__main__":
    main()
