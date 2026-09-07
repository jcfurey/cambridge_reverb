#!/usr/bin/env python3
"""Headless autoroute of the placed board with Freerouting.

    kicad_pcb --(pcbnew ExportSpecctraDSN)--> .dsn --(freerouting CLI)--> .ses
              --(pcbnew ImportSpecctraSES)--> routed kicad_pcb (GND pour refilled)

KiCad has no headless autorouter, but Freerouting (Java, open source) routes a
Specctra DSN from the command line. Run from repo root, after gen_pcb.py:

    python3 kicad/gen/route_board.py [--passes N] [--threads N] [--out FILE]

Needs Java 17+ and a Freerouting jar (not committed). Put it at
kicad/gen/freerouting.jar (git-ignored) or point FREEROUTING_JAR at it:
    https://github.com/freerouting/freerouting/releases

  * **v1.9.0 is the one to use** (freerouting-1.9.0.jar, 5 MB): its `-mp` pass
    limit works, so the job always terminates and writes the .ses -- with the
    unrouted connections, if any, left as ratsnest for you to see. It needs a
    display: the script runs it under `xvfb-run` automatically when there is no
    DISPLAY (apt install xvfb).
  * v2.1.0 was tried too: in CLI mode it ignores `-mp`, `router.max_passes` AND
    `router.job_timeout`, and only ever writes output once *nothing* is unrouted
    -- on any board with a single hard connection it rips up forever (and its
    multi-threaded router crashed on this board). The script still writes its
    freerouting.json (GUI/telemetry off, router single-threaded) in case it is
    used, but do not expect a bounded run from it.

The DSN carries the project net classes (Default 0.5 / Power 1.5 / HighCurrent
2.5 mm + clearances), so the router uses the Part 4 widths. It may route on B.Cu
(through the GND pour, which is refilled around the tracks) -- the script reports
how much copper ended up on each layer and the via count so that trade-off is visible.
"""
import sys, os, json, time, argparse, subprocess
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_KI = os.path.abspath(os.path.join(HERE, ".."))
DEFAULT_IN = os.path.join(REPO_KI, "cambridge_reverb.kicad_pcb")
JAR = os.environ.get("FREEROUTING_JAR", os.path.join(HERE, "freerouting.jar"))
import shutil
def wrap_display(cmd):
    """Freerouting 1.9 needs an X display even in CLI mode: use xvfb-run when headless."""
    if os.environ.get("DISPLAY"):
        return cmd
    if shutil.which("xvfb-run"):
        return ["xvfb-run", "-a"] + cmd
    return cmd

def freerouting_settings(work, passes, threads, job_timeout):
    """Minimal freerouting.json: headless, no telemetry, bounded job.
    Freerouting 2.1.0 ignores max_passes (CLI -mp and JSON alike) and keeps
    ripping up as long as anything is unrouted, so the JOB TIMEOUT is the real
    bound: when it fires the best board so far is written out."""
    cfg = {
        "profile": {"allow_telemetry": False, "allow_contact": False},
        "gui": {"enabled": False, "dialog_confirmation_timeout": 0},
        # router.max_threads stays 1: Freerouting 2.1.0's multi-threaded router crashed
        # (NegativeArraySizeException in PullTightAlgo) on this board; the optimizer is parallel.
        "router": {"job_timeout": job_timeout, "max_passes": passes, "max_threads": 1,
                   "automatic_neckdown": True,
                   "optimizer": {"max_passes": 30, "max_threads": threads, "improvement_threshold": 0.005},
                   "scoring": {"via_costs": 50, "plane_via_costs": 5}},
        "usage_and_diagnostic_data": {"disable_analytics": True},
        "feature_flags": {"logging": True, "multi_threading": True},
        "api_server": {"enabled": False},
    }
    with open(os.path.join(work, "freerouting.json"), "w") as f:
        json.dump(cfg, f, indent=2)

def drop_planes(dsn, which):
    """which = "top": hide the F.Cu pour only (SMD ground pads get vias to the
    bottom pour). which = "all": hide both pours, so EVERY ground connection is
    routed in copper (Power-class traces) and pour continuity can never leave a
    pad on an island -- the pours become extra copper on refill. Costs routing room."""
    lines = open(dsn).read().split("\n")
    def is_plane(l):
        t = l.lstrip()
        return t.startswith("(plane ") and (which == "all" or "F.Cu" in l)
    keep = [l for l in lines if not is_plane(l)]
    if len(keep) != len(lines):
        open(dsn, "w").write("\n".join(keep))
        print(f"  dropped {len(lines) - len(keep)} plane(s) [{which}] from the DSN")

def drop_top_plane(dsn):
    """Hide an F.Cu GND pour from the router. Freerouting treats every exported
    (plane ...) as *the* connection for that net and routes nothing to pads that
    touch it; with pours on both layers that leaves SMD ground pads sitting on
    islands once KiCad refills around the traces (20 of them in one trial). With
    only the B.Cu plane visible the router must drop a via from every SMD ground
    pad to the bottom pour -- real copper connectivity -- and the top pour is
    just extra ground copper on refill."""
    lines = open(dsn).read().split("\n")
    keep = [l for l in lines if not (l.lstrip().startswith("(plane ") and "F.Cu" in l)]
    if len(keep) != len(lines):
        open(dsn, "w").write("\n".join(keep))
        print(f"  dropped {len(lines) - len(keep)} F.Cu plane(s) from the DSN: SMD GND pads get vias to the bottom pour")

def inject_autoroute_settings(dsn, a):
    """Freerouting reads its own (autoroute_settings ...) block from the DSN
    structure; KiCad does not write one, so we add it: per-layer active flags and
    trace costs, plus via costs. This is how the 'bottom = GND pour' intent is
    expressed to the router (KiCad's exporter has no such knob)."""
    bc = a.bottom_cost
    block = f"""    (autoroute_settings
      (fanout off)
      (autoroute on)
      (postroute on)
      (vias {'off' if a.top_only else 'on'})
      (via_costs {a.via_cost})
      (plane_via_costs 5)
      (start_ripup_costs 100)
      (start_pass_no 1)
      (layer_rule F.Cu
        (active on)
        (preferred_direction horizontal)
        (preferred_direction_trace_costs 1.0)
        (against_preferred_direction_trace_costs 1.5)
      )
      (layer_rule B.Cu
        (active {'off' if a.top_only else 'on'})
        (preferred_direction vertical)
        (preferred_direction_trace_costs {bc:.1f})
        (against_preferred_direction_trace_costs {bc * 1.5:.1f})
      )
    )
"""
    txt = open(dsn).read()
    key = "    (boundary\n"          # after the (layer ...) definitions, which the block refers to
    assert key in txt, "unexpected DSN: no (boundary"
    txt = txt.replace(key, block + key, 1)
    open(dsn, "w").write(txt)
    print(f"  autoroute_settings: B.Cu {'OFF' if a.top_only else f'cost x{bc:g}'}, via cost {a.via_cost}")

def stats(board):
    segs = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    top = sum(pcbnew.ToMM(t.GetLength()) for t in segs if t.GetLayer() == pcbnew.F_Cu)
    bot = sum(pcbnew.ToMM(t.GetLength()) for t in segs if t.GetLayer() == pcbnew.B_Cu)
    board.BuildConnectivity()
    try:
        unrouted = board.GetConnectivity().GetUnconnectedCount(True)
    except Exception:
        unrouted = -1
    return len(segs), len(vias), top, bot, unrouted

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=DEFAULT_IN)
    ap.add_argument("--out", dest="dst", default=None, help="default: overwrite the input board")
    ap.add_argument("--passes", type=int, default=150, help="max router passes (-mp; honoured by v1.9.0)")
    ap.add_argument("--threads", type=int, default=4, help="optimizer threads")
    ap.add_argument("--timeout", default="00:10:00", help="v2.x job timeout HH:MM:SS (written to freerouting.json; v2.1.0 ignores it in CLI mode)")
    ap.add_argument("--work", default=os.path.join(REPO_KI, "routing"), help="DSN/SES/log dir (git-ignored)")
    ap.add_argument("--top-only", action="store_true",
                    help="B.Cu inactive for routing: all signal traces on F.Cu, bottom stays a solid "
                         "GND pour (the Part 4 rule). Expect more unrouted connections.")
    ap.add_argument("--bottom-cost", type=float, default=6.0,
                    help="trace-cost multiplier for B.Cu (default 6: the bottom is used only for short "
                         "jumpers, so the GND pour stays whole; a sweep of 3/4/6 on this board gave "
                         "7/3/1 unrouted); 1.0 = both layers equal")
    ap.add_argument("--via-cost", type=int, default=60, help="Freerouting via cost (default 60; both committed boards used 60)")
    ap.add_argument("--drop-planes", choices=("top", "all", "none"), default="top",
                    help="pours hidden from the router: top (default; SMD GND pads get vias to the bottom pour), "
                         "all (route every GND link in copper), none")
    a = ap.parse_args()
    dst = a.dst or a.src
    if not os.path.exists(JAR):
        sys.exit(f"Freerouting jar not found at {JAR} (see docstring)")
    os.makedirs(a.work, exist_ok=True)
    dsn = os.path.join(a.work, "board.dsn"); ses = os.path.join(a.work, "board.ses")
    for p in (ses,):
        if os.path.exists(p): os.remove(p)

    pro = os.path.splitext(a.src)[0] + ".kicad_pro"
    if not os.path.exists(pro):
        # Without the project file next to the board, pcbnew falls back to the
        # default net class (0.2 mm everywhere): the router then ignores the
        # Part 4 widths / clearances and the result fails DRC by the hundreds.
        sys.exit(f"no project file {pro} next to the board -- route the board in place "
                 f"(--in kicad/cambridge_reverb.kicad_pcb), not a copy")
    board = pcbnew.LoadBoard(a.src)                 # also loads the .kicad_pro net classes
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        sys.exit("DSN export failed")
    print(f"exported {dsn} ({os.path.getsize(dsn)//1024} kB)")
    inject_autoroute_settings(dsn, a)
    if a.drop_planes != "none":
        drop_planes(dsn, a.drop_planes)

    freerouting_settings(a.work, a.passes, a.threads, a.timeout)
    cmd = wrap_display(["java", "-Djava.awt.headless=false", "-jar", JAR, "-de", dsn, "-do", ses,
                        "-mp", str(a.passes), "-dct", "0"])
    print(" ".join(cmd[:4]), "... -mp", a.passes)
    t0 = time.time()
    with open(os.path.join(a.work, "freerouting.log"), "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=a.work)
    print(f"freerouting exit {rc} after {time.time()-t0:.0f} s")
    if not os.path.exists(ses):
        sys.exit("no SES produced -- see routing/freerouting.log")

    board = pcbnew.LoadBoard(a.src)
    if not pcbnew.ImportSpecctraSES(board, ses):
        sys.exit("SES import failed")
    z = prune_zero_length(board)
    if z:
        print(f"  removed {z} zero-length track segment(s) left by the SES import")
    d, t = tidy_stubs(board)
    if d or t:
        print(f"  removed {d} duplicate segment(s), trimmed {t} locked stub(s) at the router's T-junction")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(dst, board)
    n, v, top, bot, unrouted = stats(board)
    print(f"routed board -> {dst}")
    print(f"  {n} track segments: F.Cu {top:.0f} mm, B.Cu {bot:.0f} mm; {v} vias; "
          f"unrouted connections: {unrouted}")
    print("  now run: kicad-cli pcb drc --severity-all kicad/cambridge_reverb.kicad_pcb")

def prune_zero_length(board, eps_mm=0.001):
    """The SES import occasionally leaves a degenerate (< 1 um) track segment where
    two of Freerouting's wires met on a pad; DRC flags it as `track_dangling`.
    It carries no copper -- drop it."""
    dead = [t for t in board.GetTracks()
            if t.GetClass() == "PCB_TRACK" and pcbnew.ToMM(t.GetLength()) < eps_mm]
    for t in dead:
        board.Delete(t)
    return len(dead)

def tidy_stubs(board):
    """Two more SES-import artefacts around the locked escape stubs: Freerouting
    hands the fixed wire back as a routed wire too (an exact DUPLICATE of the
    locked stub), and it may join the stub from the side instead of at its end,
    leaving the end hanging (`track_dangling`). Drop exact duplicates; then trim a
    locked stub whose far end touches nothing back to the last T-junction on it."""
    segs = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    seen, dups = set(), []
    for t in segs:                                   # locked original wins over the copy
        a, b = t.GetStart(), t.GetEnd()
        key = (t.GetLayer(), t.GetNetCode(), t.GetWidth(), tuple(sorted([(a.x, a.y), (b.x, b.y)])))
        if key in seen and not t.IsLocked():
            dups.append(t)
        else:
            seen.add(key)
    for t in dups:
        board.Delete(t)
    segs = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    ends = {}
    for t in segs:
        for pt in (t.GetStart(), t.GetEnd()):
            ends.setdefault((t.GetLayer(), t.GetNetCode()), []).append((pt, t))
    trimmed = 0
    for stub in [t for t in segs if t.IsLocked()]:
        s0, s1 = stub.GetStart(), stub.GetEnd()
        pts = [(pt, t) for pt, t in ends.get((stub.GetLayer(), stub.GetNetCode()), []) if t is not stub]
        def on_stub(pt):                             # point on the stub's centre line?
            dx, dy = s1.x - s0.x, s1.y - s0.y
            L2 = dx * dx + dy * dy
            u = ((pt.x - s0.x) * dx + (pt.y - s0.y) * dy) / L2
            if u < 0.02 or u > 1.02:
                return None
            px, py = s0.x + u * dx, s0.y + u * dy
            return u if ((pt.x - px) ** 2 + (pt.y - py) ** 2) ** 0.5 < stub.GetWidth() / 2 else None
        far_end_used = any(((pt.x - s1.x) ** 2 + (pt.y - s1.y) ** 2) ** 0.5 < pcbnew.FromMM(0.01) for pt, _ in pts)
        if far_end_used:
            continue
        us = [u for u in (on_stub(pt) for pt, _ in pts) if u is not None and u < 0.98]
        if us:
            u = max(us)
            stub.SetEnd(pcbnew.VECTOR2I(int(s0.x + u * (s1.x - s0.x)), int(s0.y + u * (s1.y - s0.y))))
            trimmed += 1
    return len(dups), trimmed

if __name__ == "__main__":
    main()
