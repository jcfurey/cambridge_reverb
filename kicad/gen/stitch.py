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

def fanout(board, pcb, only=None):
    """A via to the planes for every SMD ground pad (or just the refs in `only`)."""
    if board.FindNet("GND") is None:
        return 0
    rules = fr.Rules(pcb); fr.configure(board); grid = fr.Grid(board, rules)
    code = board.FindNet("GND").GetNetCode()
    pads = [(fp.GetReference(), p) for fp in board.GetFootprints() for p in fp.Pads()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetNetname() == "GND" and (only is None or fp.GetReference() in only)]
    if not pads:
        return 0
    w = min(rules.width("GND"), 0.5)
    vb = grid.via_blocked("GND", None); blk = grid.blocked("GND", w)["F.Cu"]
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
