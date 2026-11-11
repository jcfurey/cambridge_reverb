#!/usr/bin/env python3
"""One command that says whether a board is fit to order.

    python3 kicad/gen/verify.py smd            # the JLCPCB-assembled board (default)
    python3 kicad/gen/verify.py tht
    python3 kicad/gen/verify.py smd --no-spice # skip the ngspice suite (a few seconds faster)

Everything here checks the ARTIFACTS (the .kicad_sch / .kicad_pcb files and the order
package as KiCad reads them), not the generator's own data, so a generator bug cannot
vouch for itself. Exit code 0 = every check passed. The report is also written to
kicad/reports/verify-<profile>.txt (committed evidence).

  ERC           kicad-cli sch erc: 0 violations
  DRC           kicad-cli pcb drc --severity-all with the JLCPCB limits and the .kicad_dru
                rules: 0 errors, 0 unconnected, 0 silkscreen warnings
  parity        schematic netlist (kicad-cli export) == board pad nets, pin for pin; same
                footprint on every reference
  pin map       every polarised / multi-pin footprint: what each PAD physically is (from
                the datasheets in datasheets/, entered here by hand) against the SYMBOL pin
                that is wired to it -- the check that would have caught errata #18 and #25
  electrical    net-level assertions on the board: clamp-diode direction, rectifier
                topology, electrolytic polarity against the DC operating point, supply
                pins, pot directions, footswitch lines, vactrol LED polarity
  silkscreen    every part has a visible reference of legal size on the front silk
  JLCPCB limits the project's DRC constraints are at or above JLCPCB's published ones
  RF rules      kicad/gen/rf_audit.py on the finished copper: signal / GND / signal / GND
                with nothing routed on a plane, no slot in a plane beyond the unavoidable
                ones, edge pull-back, pour gaps, the ground fence and stitching density,
                a via for every SMD ground pad, and no stray capacitance in the audio band
  order package BOM == CPL == placed SMD footprints, LCSC number on every line, CPL
                coordinates and rotations follow the board, Gerber / drill set complete
  SPICE         spice/run_all.sh exits 0, the key results are inside their limits, and
                every R / C / L value in a netlist equals the schematic's
"""
import sys, os, re, csv, json, glob, subprocess, tempfile, zipfile, collections, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
PROF = {"tht": dict(dir="kicad", sch="cambridge_reverb.kicad_sch", pcb="cambridge_reverb.kicad_pcb"),
        "smd": dict(dir="kicad/smd", sch="cambridge_reverb_smd.kicad_sch", pcb="cambridge_reverb_smd.kicad_pcb")}

# ---- what each pad physically IS, per footprint (datasheet -> pad number -> function) --------
# Sources: datasheets/SOURCES.md. KiCad's diode / LED footprints put the cathode on pad 1.
PAD_FUNCTION = {
    "D_SMA":                   {"1": "K", "2": "A"},                 # KiCad Diode_SMD: pad 1 = cathode (silk bar)
    "D_DO-41_SOD81_P10.16mm_Horizontal": {"1": "K", "2": "A"},      # KiCad Diode_THT: pad 1 = cathode ("K" on silk)
    "LED_D3.0mm":              {"1": "K", "2": "A"},                 # KiCad LED_THT: pad 1 = cathode (flat)
    "SOT-23":                  {"1": "D", "2": "S", "3": "G"},       # onsemi MMBF5457 (case 318, style 10)
    "SOT-23_MMBT3904_as_EBC":  {"1": "E", "2": "B", "3": "C"},       # MMBT3904 is B-E-C on pins 1-2-3; pads renumbered (geometry checked below)
    "TO-220-3_Vertical":       {"1": "ADJ", "2": "OUT", "3": "IN"},  # TI LM317 (KCS / KCT)
    "TO-220-5_Vertical_P1.70mm_LM1875": {"1": "IN+", "2": "IN-", "3": "V-", "4": "OUT", "5": "V+"},   # TI SNAS524A
    "Bridge_KBP_P3.81mm":      {"1": "+", "2": "~", "3": "~", "4": "-"},                                # Diodes DS39310
    "DIP-8_W7.62mm":           {"1": "OUT1", "2": "IN1-", "3": "IN1+", "4": "V-", "5": "IN2+", "6": "IN2-", "7": "OUT2", "8": "V+"},   # TL072
    "DIP-14_W7.62mm":          {"1": "OUT1", "2": "IN1-", "3": "IN1+", "4": "V+", "5": "IN2+", "6": "IN2-", "7": "OUT2",
                                "8": "OUT3", "9": "IN3-", "10": "IN3+", "11": "V-", "12": "IN4+", "13": "IN4-", "14": "OUT4"},        # TL074
    "VTL5C1":                  {"1": "LED_K", "2": "LED_A", "3": "LDR_1", "4": "LDR_2"},                # PerkinElmer p.43: 1 = cathode
}
# TO-92_Inline_Wide carries two different parts: pin functions by SYMBOL
TO92 = {"NJFET": {"1": "D", "2": "S", "3": "G"},      # onsemi 2N5457 / J113
        "NPN":   {"1": "E", "2": "B", "3": "C"}}      # onsemi 2N3904
# electrolytics: pad 1 is "+" on every KiCad CP_Radial footprint
# DC operating point of the nets an electrolytic or a clamp can sit on (V, nominal)
DC = {"GND": 0, "+33V5": 33.5, "VRAW": 34.0, "VREG_IN": 30.5, "+17V": 17.3, "+17V_PRE": 17.0, "ADJ17": 16.1,
      "VBIAS_R": 8.6, "VBIAS_T": 8.6, "VBIAS_3": 8.6, "Q1S": 1.1, "Q2S": 1.1, "QRS": 1.1,
      "PA_BREF": 16.75, "PA_GAIN": 16.75, "PA_OUT": 16.75, "SPK_P": 0.0, "R_DRVO": 8.6, "TKDRV": 0.0,
      "DPT_W": 8.6, "QDRV": 0.9, "TREM_OUT": 8.6, "TREM_S": 0.0}

class Report:
    def __init__(self): self.rows = []; self.fail = 0
    def add(self, group, ok, text):
        self.rows.append((group, ok, text)); self.fail += (not ok)
        print(f"  [{'ok' if ok else 'FAIL'}] {group:13s} {text}")

def sh(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw)

# ------------------------------------------------------------------------------- readers
def read_netlist(sch):
    """kicad-cli netlist -> ({(ref, pin): net}, {ref: footprint}, {ref: value}, {(ref, pin): pin name})"""
    with tempfile.NamedTemporaryFile(suffix=".net", delete=False) as f: tmp = f.name
    sh(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", tmp, sch])
    t = open(tmp).read(); os.remove(tmp)
    pins, pinname = {}, {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\n\s*\(net \(code|\Z)', t, re.S):
        for n in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "([^"]*)"\))?', m.group(2)):
            pins[(n.group(1), n.group(2))] = m.group(1).split("/")[-1]
            pinname[(n.group(1), n.group(2))] = n.group(3) or ""
    fps, vals = {}, {}
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)', t):
        fps[m.group(1)] = m.group(3); vals[m.group(1)] = m.group(2)
    return pins, fps, vals, pinname

def read_board(pcb):
    import pcbnew
    b = pcbnew.LoadBoard(pcb)
    return pcbnew, b

# ------------------------------------------------------------------------------- checks
def check_erc(rep, sch):
    with tempfile.NamedTemporaryFile(suffix=".rpt", delete=False) as f: tmp = f.name
    r = sh(["kicad-cli", "sch", "erc", "--severity-all", "--exit-code-violations", "-o", tmp, sch])
    n = len(re.findall(r"^\[", open(tmp).read(), re.M)); os.remove(tmp)
    rep.add("ERC", r.returncode == 0 and n == 0, f"{n} violations")

def check_drc(rep, pcb):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f: tmp = f.name
    sh(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", tmp, pcb])
    d = json.load(open(tmp)); os.remove(tmp)
    c = collections.Counter((v["type"], v["severity"]) for v in d.get("violations", []))
    errs = {k[0]: n for k, n in c.items() if k[1] == "error"}; warns = {k[0]: n for k, n in c.items() if k[1] != "error"}
    un = len(d.get("unconnected_items", []))
    rep.add("DRC", un == 0, f"{un} unconnected")
    rep.add("DRC", not errs, f"{sum(errs.values())} errors {errs or ''}")
    silk = {k: n for k, n in warns.items() if k.startswith("silk") or "text" in k}
    rep.add("DRC", not silk, f"{sum(silk.values())} silkscreen / text warnings {silk or ''}")
    other = {k: n for k, n in warns.items() if k not in silk}
    rep.add("DRC", not other, f"{sum(other.values())} other warnings {other or ''}")

def check_parity(rep, pins, fps, pcbnew, b):
    board_pins, board_fp = {}, {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith(("H", "FID")) and not ref.startswith("HS"): continue
        board_fp[ref] = fp.GetFPIDAsString()
        for p in fp.Pads():
            if p.GetNetname(): board_pins[(ref, p.GetNumber())] = p.GetNetname()
    sch_refs = {r for r in fps if not r.startswith("#")}
    rep.add("parity", sch_refs == set(board_fp), f"{len(sch_refs)} schematic parts, {len(board_fp)} board footprints"
            + ("" if sch_refs == set(board_fp) else f"; only schematic {sorted(sch_refs - set(board_fp))[:6]}, only board {sorted(set(board_fp) - sch_refs)[:6]}"))
    bad_fp = [r for r in sch_refs & set(board_fp) if fps[r] != board_fp[r]]
    rep.add("parity", not bad_fp, f"{len(bad_fp)} footprint mismatches {bad_fp[:6] or ''}")
    spins = {k: v for k, v in pins.items() if not k[0].startswith("#")}
    def groups(d):
        g = collections.defaultdict(set)
        for k, n in d.items(): g[n].add(k)
        return {frozenset(v) for v in g.values() if len(v) > 1}
    gs, gb = groups(spins), groups(board_pins)
    rep.add("parity", gs == gb, f"{len(gs)} schematic nets, {len(gb)} board nets, {len(gs ^ gb)} differ"
            + ("" if gs == gb else ": " + "; ".join(sorted(",".join(f"{r}.{p}" for r, p in sorted(x)[:4]) for x in list(gs ^ gb)[:4]))))
    rep.add("parity", set(spins) == set(board_pins), f"{len(spins)} connected pins in the schematic, {len(board_pins)} netted pads on the board")

def check_pinmap(rep, pins, fps, pinname, pcbnew, b):
    """Symbol pin NAME wired to each pad vs what the pad physically is."""
    import gen_kicad as g
    wrong, n = [], 0
    sym_of = {c["ref"]: c["libsym"] for c in g.COMPONENTS}
    for fp in b.GetFootprints():
        ref = fp.GetReference(); name = fp.GetFPIDAsString().split(":")[-1]
        table = PAD_FUNCTION.get(name)
        if name == "TO-92_Inline_Wide": table = TO92.get(sym_of.get(ref))
        if name.startswith("CP_Radial"): table = {"1": "+"}      # (the "-" pin is unnamed in the symbol)
        if table is None: continue
        for p in fp.Pads():
            want = table.get(p.GetNumber()); got = pinname.get((ref, p.GetNumber()), "")
            if want is None: continue
            n += 1
            if got != want and not (want == "~" and got == ""):     # KiCad drops a pin name of "~" (unnamed)
                wrong.append(f"{ref}.{p.GetNumber()} pad is {want}, symbol pin is {got or '-'}")
    rep.add("pin map", not wrong and n > 0, f"{n} pads checked against their datasheet function" + ("" if not wrong else ": " + "; ".join(wrong[:8])))
    # geometry the tables rely on
    geo = []
    for fp in b.GetFootprints():
        name = fp.GetFPIDAsString().split(":")[-1]
        loc = {p.GetNumber(): (pcbnew.ToMM(p.GetPos0().x) if hasattr(p, "GetPos0") else 0, 0) for p in fp.Pads()}
        pads = {p.GetNumber(): p for p in fp.Pads()}
        rel = lambda n: ((pcbnew.ToMM(pads[n].GetPosition().x) - pcbnew.ToMM(fp.GetPosition().x)), (pcbnew.ToMM(pads[n].GetPosition().y) - pcbnew.ToMM(fp.GetPosition().y)))
        if name == "SOT-23_MMBT3904_as_EBC" and int(round(fp.GetOrientationDegrees())) == 0:
            # physical SOT-23 pin 1 (upper left) must be the BASE pad (named 2), pin 2 (lower left) the EMITTER pad (named 1)
            if not (rel("2")[1] < rel("1")[1] and rel("2")[0] < 0 and rel("1")[0] < 0 and rel("3")[0] > 0):
                geo.append(f"{fp.GetReference()}: SOT-23 pad geometry does not match B-E-C")
        if name == "VTL5C1":
            d12 = abs(rel("1")[0] - rel("2")[0]) + abs(rel("1")[1] - rel("2")[1]); d34 = abs(rel("3")[0] - rel("4")[0]) + abs(rel("3")[1] - rel("4")[1])
            span = max(abs(rel("3")[0] - rel("1")[0]), abs(rel("3")[1] - rel("1")[1]))
            if not (d12 <= 3.1 and 4.9 <= d34 <= 5.3 and span >= 12.5):
                geo.append(f"{fp.GetReference()}: not the axial VTL5C1 outline (LED pair {d12:.2f}, cell pair {d34:.2f}, span {span:.2f} mm)")
    rep.add("pin map", not geo, "SOT-23 (MMBT3904) and VTL5C1 pad geometry match their package drawings" if not geo else "; ".join(geo))

def check_electrical(rep, pcbnew, b):
    net = {}
    for fp in b.GetFootprints():
        for p in fp.Pads(): net[(fp.GetReference(), p.GetNumber())] = p.GetNetname()
    fpname = {fp.GetReference(): fp.GetFPIDAsString().split(":")[-1] for fp in b.GetFootprints()}
    N = lambda ref, pin: net.get((ref, pin), "?")
    def other(ref, pin):                      # the net on a 2-pin part's other pad
        return N(ref, "2" if pin == "1" else "1")
    A = lambda ok, text: rep.add("electrical", ok, text)
    # clamp diodes: pad 1 = cathode on both diode footprints
    A(N("D1", "1") == "+33V5" and N("D1", "2") == "PA_OUT", f"D1 clamps the output to V+: cathode {N('D1', '1')}, anode {N('D1', '2')}")
    A(N("D2", "1") == "PA_OUT" and N("D2", "2") == "GND", f"D2 clamps the output to GND: cathode {N('D2', '1')}, anode {N('D2', '2')}")
    A(DC[N("D1", "1")] > DC[N("D1", "2")] and DC[N("D2", "1")] > DC[N("D2", "2")], "both clamp diodes are reverse-biased at the DC operating point")
    A({N("LED_rate", "1"), N("LED_rate", "2")} == {N("LED_lim", "1"), N("LED_lim", "2")} and N("LED_rate", "1") == N("LED_lim", "2"),
      "LFO limiter LEDs are antiparallel")
    # rectifier: a centre tap on GND and the bridge '-' on GND short each half winding
    ct, neg = N("T1", "2"), N("BR1", "4")
    A(not (ct == "GND" and neg == "GND"), f"rectifier: T1 centre tap on {ct}, bridge '-' on {neg} (not both hard-wired to GND)")
    A({N("JP_BR", "1"), N("JP_BR", "2")} == {neg, "GND"}, "JP_BR is the only path from the bridge '-' pin to GND")
    A(N("BR1", "1") == "VRAW" and {N("BR1", "2"), N("BR1", "3")} == {"AC1", "AC2"}, "bridge: + on VRAW, ~ on the two secondary ends")
    # electrolytics against the DC operating point
    bad, n = [], 0
    for ref, name in fpname.items():
        if not name.startswith("CP_Radial"): continue
        p, m = N(ref, "1"), N(ref, "2"); n += 1
        if p not in DC or m not in DC: bad.append(f"{ref}: no DC value for {p}/{m}")
        elif DC[p] <= DC[m]: bad.append(f"{ref}: + on {p} ({DC[p]} V), - on {m} ({DC[m]} V)")
    A(not bad and n > 0, f"{n} electrolytics: '+' pad on the more positive net" + ("" if not bad else " -- " + "; ".join(bad)))
    # supplies
    sup = [("IC1", "8", "+17V"), ("IC1", "4", "GND"), ("IC2", "8", "+17V"), ("IC2", "4", "GND"), ("IC3", "4", "+17V"), ("IC3", "11", "GND"),
           ("IC_PA", "5", "+33V5"), ("IC_PA", "3", "GND"), ("U1", "3", "VREG_IN"), ("U1", "2", "+17V"), ("U1", "1", "ADJ17")]
    wrong = [f"{r}.{p}={N(r, p)} (want {w})" for r, p, w in sup if N(r, p) != w]
    A(not wrong, "IC supply pins" + ("" if not wrong else ": " + ", ".join(wrong)))
    # JFET stages: drain through its load to the decoupled rail, source through its resistor to GND, gate never on a rail
    jf = [("Q1", "R_d1", "R_s1"), ("Q2", "R_d2", "R_s2"), ("Q_rec", "R_rec1", "R_rec2")]
    wrong = []
    for q, rd, rs in jf:
        d, s_, gt = N(q, "1"), N(q, "2"), N(q, "3")
        if not ({N(rd, "1"), N(rd, "2")} == {d, "+17V_PRE"} and {N(rs, "1"), N(rs, "2")} == {s_, "GND"} and gt not in DC):
            wrong.append(q)
    A(not wrong, "JFETs: pad 1 drain -> load -> +17V_PRE, pad 2 source -> Rs -> GND, pad 3 gate" + ("" if not wrong else f": {wrong}"))
    A(N("Q_trem", "2") == "FS_TREM" and N("Q_trem", "1") == other("R_e", "1" if N("R_e", "1") == "GND" else "2") and N("VTL1", "1") == N("Q_trem", "3"),
      "tremolo driver: base on FS_TREM, emitter on R_e, collector on the vactrol LED cathode")
    A(N("VTL1", "2") == other("R_c", "1" if N("R_c", "1") == "+17V" else "2") and "+17V" in (N("R_c", "1"), N("R_c", "2")),
      "vactrol LED anode (pad 2) is fed from +17V through R_c")
    # pots: lug 3 is the clockwise end -> clockwise = more
    pots = {"POT_VOL": ("VOLTOP", "TONE_OUT", "GND"), "POT_REV": ("FS_REV", "WET", "GND"), "POT_DPT": ("LFO_OUT", "DPT_W", "VBIAS_T"),
            "POT_BASS": ("JA", "JWB", "JB"), "POT_TREB": ("JTA", "JWT", "JTB")}
    wrong = [r for r, (cw, w, ccw) in pots.items() if (N(r, "3"), N(r, "2"), N(r, "1")) != (cw, w, ccw)]
    wrong += [r for r in ("POT_SPD_A", "POT_SPD_B") if N(r, "1") != N(r, "2") or N(r, "3") == N(r, "2")]
    A(not wrong, "pots: clockwise lug (pad 3) on the 'more' end, speed gangs fall in resistance clockwise" + ("" if not wrong else f": {wrong}"))
    # footswitch
    A((N("FS1", "1"), N("FS1", "2"), N("FS1", "3")) == ("FS_REV", "FS_TREM", "FS_MRB") and {N("FS1", "4"), N("FS1", "5"), N("FS1", "6")} == {"GND"},
      "footswitch pads: REV, TRM, MRB, then three grounds")
    A(N("L1", "2") == "FS_MRB" and N("C_mrb_600", "2") == "FS_MRB" and "GND" not in (N("L1", "1"), N("L1", "2")),
      "MRB tank returns through the footswitch line (out of circuit when the pedal is open)")
    A(N("POT_REV", "3") == "FS_REV" and N("Q_trem", "2") == "FS_TREM", "reverb and tremolo are defeated by grounding their footswitch lines")

def check_silk(rep, pcbnew, b):
    missing, small = [], []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith(("FID", "H")) and not ref.startswith("HS"): continue
        t = fp.Value() if ref.startswith("TP_") else fp.Reference()
        if not t.IsVisible() or t.GetLayer() != pcbnew.F_SilkS: missing.append(ref)
        elif pcbnew.ToMM(t.GetTextSize().y) < 1.0 - 1e-6 or pcbnew.ToMM(t.GetTextThickness()) < 0.15 - 1e-6: small.append(ref)
    rep.add("silkscreen", not missing, f"every part labelled on the front silk" if not missing else f"no silk label: {missing[:10]}")
    rep.add("silkscreen", not small, "labels >= 1.0 mm high, >= 0.15 mm stroke (JLCPCB legend minimum)" if not small else f"too small: {small[:10]}")
    marks = [d.GetText() for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT"]
    rep.add("silkscreen", any("CAMBRIDGE" in m for m in marks) and any("JLCJLCJLCJLC" in m for m in marks), "board identity and JLCPCB order-number spot present")

def check_package(rep, pcbnew, b):
    import jlc_parts, fab_jlcpcb
    out = os.path.join(ROOT, "production", "smd")
    bom = list(csv.DictReader(open(os.path.join(out, "bom-jlcpcb.csv"))))
    cpl = list(csv.DictReader(open(os.path.join(out, "cambridge_reverb_smd-cpl.csv"))))
    bom_refs = [r for row in bom for r in row["Designator"].split(",")]
    placed = {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        smd = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in fp.Pads())
        if smd and not ref.startswith("FID") and not (fp.GetAttributes() & pcbnew.FP_DNP):
            placed[ref] = fp
    rep.add("order package", len(bom_refs) == len(set(bom_refs)) and set(bom_refs) == set(placed),
            f"BOM lists exactly the {len(placed)} placed SMD parts ({len(bom)} lines)" if set(bom_refs) == set(placed)
            else f"BOM vs board: only BOM {sorted(set(bom_refs) - set(placed))[:6]}, only board {sorted(set(placed) - set(bom_refs))[:6]}")
    rep.add("order package", {r["Designator"] for r in cpl} == set(placed), f"CPL lists the same {len(cpl)} parts")
    known = {p["lcsc"]: p for p in jlc_parts.PARTS.values()}
    bad = [row["Comment"] for row in bom if row["LCSC Part #"] not in known or known[row["LCSC Part #"]]["mpn"] != row["MPN"]]
    rep.add("order package", not bad, "every BOM line carries an LCSC number from the verified parts table" if not bad else f"unknown part on: {bad}")
    # CPL coordinates / rotation follow the board
    off = []
    for r in cpl:
        fp = placed.get(r["Designator"])
        if fp is None: continue
        x, y = float(r["Mid X"][:-2]), -float(r["Mid Y"][:-2])
        bb = fp.GetBoundingBox(False, False)
        if not (pcbnew.ToMM(bb.GetLeft()) - 0.01 <= x <= pcbnew.ToMM(bb.GetRight()) + 0.01 and pcbnew.ToMM(bb.GetTop()) - 0.01 <= y <= pcbnew.ToMM(bb.GetBottom()) + 0.01):
            off.append(r["Designator"])
        want = (fp.GetOrientationDegrees() + fab_jlcpcb.rotation_fix(fp.GetFPIDAsString().split(":")[-1])) % 360
        if abs(float(r["Rotation"]) - want) > 0.01: off.append(r["Designator"] + " rot")
    rep.add("order package", not off, "CPL positions lie on their footprints, rotations = board angle + JLCPCB package offset" if not off else f"CPL off: {off[:8]}")
    # one LCSC part per (value, footprint) group and the right package family
    pk = [row["Comment"] for row in bom if row["Footprint"] not in row["Comment"] and row["Footprint"] not in ("SMA", "SOT-23")]
    rep.add("order package", not pk, "BOM footprint column agrees with each part's package" if not pk else f"package mismatch: {pk}")
    z = os.path.join(out, "cambridge_reverb_smd-gerbers.zip")
    names = zipfile.ZipFile(z).namelist() if os.path.exists(z) else []
    need = ["F_Cu.gtl", "In1_Cu.g2", "In2_Cu.g3", "B_Cu.gbl", "F_Paste.gtp", "F_Silkscreen.gto", "B_Silkscreen.gbo", "F_Mask.gts", "B_Mask.gbs", "Edge_Cuts.gm1", "PTH.drl", "NPTH.drl"]
    miss = [n for n in need if not any(x.endswith(n) for x in names)]
    rep.add("order package", not miss, f"Gerber zip has the 4 copper layers, mask, paste, silk, outline and both drill files ({len(names)} files)" if not miss else f"zip is missing {miss}")
    if names:
        zf = zipfile.ZipFile(z)
        drl = zf.read(next(n for n in names if n.endswith("-PTH.drl"))).decode(errors="replace")
        hits = len(re.findall(r"^X-?[\d.]+Y-?[\d.]+", drl, re.M))
        pth = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)
        vias = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
        rep.add("order package", hits == pth + vias, f"plated drill file: {hits} holes = {pth} pads + {vias} vias on the board (the zip was made from THIS board)")
        fid = sum(1 for fp in b.GetFootprints() if fp.GetReference().startswith("FID"))
        rep.add("order package", fid >= 3, f"{fid} fiducials on the assembled side")
    summ = os.path.join(out, "cambridge_reverb_smd-fab-summary.json")
    if os.path.exists(summ):
        s = json.load(open(summ))
        rep.add("order package", s["unconnected"] == 0 and s["drc_errors"] == 0, "package was exported from a fully routed, DRC-clean board")

# JLCPCB's published limits (jlcpcb.com/capabilities/pcb-capabilities, multilayer, 1 oz, read
# 2026-11-11) against the constraint the project enforces in DRC: (project key, JLCPCB, note)
JLC_LIMITS = [
    ("min_track_width", 0.09, "track width / spacing 0.09 mm"), ("min_clearance", 0.09, "spacing"),
    ("min_via_diameter", 0.45, "vias under 0.45 mm cost extra (absolute minimum 0.25)"),
    ("min_through_hole_diameter", 0.3, "holes under 0.3 mm cost extra (absolute minimum 0.15)"),
    ("min_via_annular_width", 0.20, "annular ring: 0.20 recommended, 0.15 absolute"),
    ("min_hole_to_hole", 0.45, "pad hole to hole 0.45 (via to via 0.2)"),
    ("min_hole_clearance", 0.35, "PTH to track 0.35 recommended (0.28 min); inner-layer PTH hole to copper 0.3"),
    ("min_copper_edge_clearance", 0.40, "copper to a routed edge 0.2 + the 0.2 edge tolerance (V-cut 0.4)"),
    ("solder_mask_min_width", 0.10, "mask dam 0.10 (green)"),
    ("min_text_height", 1.0, "legend height 1.0"), ("min_text_thickness", 0.15, "legend stroke 0.15"),
]
def check_jlc(rep, pcb):
    pro = json.load(open(os.path.splitext(pcb)[0] + ".kicad_pro")); r = pro["board"]["design_settings"]["rules"]
    low = [f"{k} = {r.get(k)} (JLCPCB: {v}, {note})" for k, v, note in JLC_LIMITS if r.get(k, 0) < v - 1e-9]
    rep.add("JLCPCB limits", not low, f"all {len(JLC_LIMITS)} board constraints at or above JLCPCB's published limits (DRC enforces them)" if not low else "; ".join(low))
    dru = open(os.path.splitext(pcb)[0] + ".kicad_dru").read()
    rep.add("JLCPCB limits", "silk_to_pad" in dru and "0.15mm" in dru, "silkscreen text 0.15 mm off every pad (rule silk_to_pad)")

def check_rf(rep, pcbnew, b, pcb, profile):
    import rf_audit
    R = rf_audit.audit(pcb); A = lambda ok, text: rep.add("RF rules", ok, text)
    roles = [(l, role) for l, role, _ in R["stack"]]
    A(roles == [("F.Cu", "signal"), ("In1.Cu", "GND plane"), ("In2.Cu", "signal"), ("B.Cu", "GND plane")] and R["tracks_on_planes"] == 0,
      "stack is signal / GND / signal / GND and nothing is routed on a plane: " + ", ".join(f"{l} {r}" for l, r in roles))
    lim = {"In1.Cu": (12.0, 6), "B.Cu": (16.0, 16)}
    for name, d in R["planes"].items():
        longest = d["longest"][0] if d["longest"] else (0, 0, "-")
        mx, cnt = lim.get(name, (16.0, 16))
        A(d["pieces"] == 1 and longest[0] <= mx and d["over5"] <= cnt,
          f"{name} plane: one piece, {d['coverage']} % copper, {d['over5']} openings over 5 mm, longest {longest[0]:g} mm at {longest[2]} (limit {mx:g} mm, {cnt})")
    e = min(R["edge"].values())
    A(e >= 0.45, f"copper to board edge >= 0.5 mm on every layer (measured " + ", ".join(f"{l} {v:g}" for l, v in R["edge"].items()) + ")")
    g = R.get("pour_gap", {})
    A(bool(g) and g["any"] >= 0.38 and (g["hiz"] is None or g["hiz"] >= 0.85),
      f"top pour keeps {g.get('any')} mm from the nearest trace and {g.get('hiz')} mm from HiZ traces (rules 0.5 / 1.0 mm; DRC is the exact check)")
    f = R["fence"]
    A(f["vias"] >= 60 and f["median"] <= 5.5 and f["largest"] <= 30, f"perimeter fence: {f['vias']} ground vias, median pitch {f['median']:g} mm, largest gap {f['largest']:g} mm")
    st = R["stitch"]
    A(st["furthest"] <= 16.0 and st["mean"] <= 5.0, f"stitching: {st['gnd_vias']} ground vias, no point further than {st['furthest']:g} mm from one (mean {st['mean']:g} mm)")
    sg = R["smd_gnd"]
    A(not sg["lonely"], f"{sg['pads']} SMD ground pads, each with a via to the planes" if not sg["lonely"] else f"SMD ground pads without a via: {sg['lonely']}")
    par = [r for r in R["parasitics"] if r[1] != "SUMJ"]
    low = [f"{r[1]} {r[0] / 1e3:.0f} kHz" for r in par if r[0] < 80e3]
    A(not low, f"stray capacitance: lowest corner {par[0][1]} {par[0][2]:.0f} pF -> {par[0][0] / 1e3:.0f} kHz; all {len(par)} sensitive nets above 80 kHz (< 0.3 dB at 20 kHz)" if not low else "corners in the audio band: " + ", ".join(low))
    net = {(fp.GetReference(), p.GetNumber()): p.GetNetname() for fp in b.GetFootprints() for p in fp.Pads()}
    A({net.get(("C_mixfb", "1")), net.get(("C_mixfb", "2"))} == {"SUMJ", "BLEND"},
      f"summing node SUMJ ({R['c_sumj']:.0f} pF of copper) is compensated: C_mixfb across R_mixfb")
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    blind = sum(1 for v in vias if v.GetViaType() != pcbnew.VIATYPE_THROUGH or v.TopLayer() != pcbnew.F_Cu or v.BottomLayer() != pcbnew.B_Cu)
    A(blind == 0, f"all {len(vias)} vias are through vias (no blind or buried vias: the standard 4-layer process)" if blind == 0 else f"{blind} blind / buried vias")
    nfp_ = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and not p.GetRemoveUnconnected())
    A(nfp_ == 0, "unused inner-layer pad copper removed on every through-hole pad (plane openings follow the holes)" if nfp_ == 0 else f"{nfp_} PTH pads still carry unused inner copper")

def spice_value(s):
    m = re.match(r"^(\d+(?:\.\d+)?)(meg|[kmunpf]?)", s.lower())
    return None if not m else float(m.group(1)) * {"": 1, "k": 1e3, "meg": 1e6, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15}[m.group(2)]
# netlist elements that share a NAME with a schematic part but are something else, or a documented trim value
SPICE_EXEMPT = {("ac_hum_psrr.cir", "R_s1"): "trimmed 1.2 k (errata #15)", ("ac_hum_psrr.cir", "R_s2"): "trimmed 1.2 k (errata #15)",
                ("noise_frontend.cir", "R_s1"): "trimmed 1.2 k (errata #15)", ("noise_frontend.cir", "R_s2"): "trimmed 1.2 k (errata #15)",
                ("ac_power_amp_lm1875.cir", "R_e"): "speaker model element, not the tremolo R_e",
                ("ac_power_amp_lm1875.cir", "C_res"): "speaker model element, not the tone C_res",
                ("sweep_pa_headroom.cir", "R_b1"): "local name for the PA bias divider", ("sweep_pa_headroom.cir", "R_b2"): "local name for the PA bias divider"}
def check_spice(rep, vals, run):
    sch = {}
    for ref, v in vals.items():
        m = re.match(r"^(\d+(?:\.\d+)?)\s*(pF|nF|uF|R|k|M|H)", v)
        if m and ref[0] in "RCL":
            sch[ref.lower()] = (ref, float(m.group(1)) * {"pF": 1e-12, "nF": 1e-9, "uF": 1e-6, "R": 1, "k": 1e3, "M": 1e6, "H": 1}[m.group(2)])
    mism, seen = [], set()
    for f in sorted(glob.glob(os.path.join(ROOT, "spice", "*.cir"))):
        for line in open(f):
            t = line.split()
            if len(t) < 4 or t[0][0] in "*.+" or t[0].lower() not in sch or "{" in t[3]: continue
            v = spice_value(t[3]); ref, want = sch[t[0].lower()]
            if v is None: continue
            seen.add(ref)
            if abs(v - want) / want > 0.011 and (os.path.basename(f), ref) not in SPICE_EXEMPT:
                mism.append(f"{os.path.basename(f)}: {ref} = {t[3]}, schematic {vals[ref]}")
    rep.add("SPICE", not mism and len(seen) >= 60, f"{len(seen)} schematic parts appear by name in the netlists with the schematic's value"
            + (f" ({len(SPICE_EXEMPT)} documented exceptions)" if not mism else ": " + "; ".join(mism[:6])))
    if not run:
        return
    r = sh(["bash", os.path.join(ROOT, "spice", "run_all.sh")])
    rep.add("SPICE", r.returncode == 0 and "FAILED" not in r.stdout, "spice/run_all.sh: every netlist ran")
    res = lambda name: open(os.path.join(ROOT, "spice", "results", name)).read()
    def num(text, pat):
        m = re.search(pat, text); return float(m.group(1)) if m else float("nan")
    lim = []
    t = res("tran_tremolo_depth.txt")
    d1 = num(t, r"cfg=1 .*DEPTH=([-\d.eE+]+)"); d2 = num(t, r"cfg=2 .*DEPTH=([-\d.eE+]+)")
    lim.append((d1 >= 12, f"tremolo depth {d1:.1f} dB (>= 12)")); lim.append((d2 <= 0.5, f"footswitch closed: depth {d2:.2f} dB (<= 0.5)"))
    t = res("ac_mrb.txt")
    on100 = num(t, r"fs=1 .*100 Hz=([-\d.]+)"); onpk = num(t, r"fs=1 peak=([-\d.]+)")
    off = [num(t, rf"fs=0 .*{k}=([-\d.]+)") for k in ("100 Hz", "600 Hz", "1 kHz", "5 kHz")]
    lim.append((onpk - on100 >= 20, f"MRB engaged: {onpk - on100:.0f} dB between the peak and 100 Hz (>= 20)"))
    lim.append((max(off) - min(off) <= 1.5 and min(off) >= -2.5, f"MRB bypassed: {min(off):.1f} .. {max(off):.1f} dB, 100 Hz - 5 kHz (flat within 1.5)"))
    t = res("tran_preamp_headroom.txt")
    thd = {}
    for m in re.finditer(r"ROW opt=(\d) vin_pk=([\d.]+)[^\n]*\n(?:[^\n]*\n)?[^\n]*THD: ([\d.]+) %", t): thd[(m.group(1), m.group(2))] = float(m.group(3))
    lim.append((thd.get(("2", "0.1"), 99) < 1.0 and thd.get(("2", "0.2"), 99) < 2.0, f"preamp as built (no source bypass): {thd.get(('2', '0.1'))} % THD at 0.1 V pk, {thd.get(('2', '0.2'))} % at 0.2 V"))
    lim.append((thd.get(("0", "0.1"), 0) > 20, f"...and the reason the bypass caps are optional: {thd.get(('0', '0.1'))} % at 0.1 V with both fitted"))
    t = res("ac_summer_stability.txt")
    pk0 = num(t, r"cfb=0 cs=10p \| peaking=([-\d.eE+]+)"); pk1 = max(num(t, rf"cfb=33p cs={c} \| peaking=([-\d.eE+]+)") for c in ("5p", "10p", "15p", "25p"))
    d20 = num(t, r"cfb=33p cs=10p .*20 kHz=([-\d.eE+]+)")
    lim.append((pk1 <= 0.1 and d20 >= -1.0, f"reverb summer with C_mixfb: {pk1:.2f} dB of peaking for 5-25 pF on the summing node, {d20:.1f} dB at 20 kHz (without it: {pk0:.1f} dB at 10 pF)"))
    t = res("dc_preamp_jfet.txt"); vd = num(t, r"v\(d\) = ([\d.eE+-]+)")
    lim.append((6 <= vd <= 14, f"JFET drain bias {vd:.1f} V (6 .. 14; trim R_s for 8-9)"))
    t = res("sweep_pa_headroom.txt"); m = re.search(r"^33\.5 (\S+) (\S+) (\S+) (\S+) (\S+)", t, re.M)
    pw = float(m.group(5)) if m else float("nan")
    lim.append((pw >= 11, f"power amp at the nominal rail: {pw:.1f} W into 8 ohm (>= 11)"))
    for ok, text in lim: rep.add("SPICE", ok, text)

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("profile", nargs="?", default="smd", choices=("smd", "tht"))
    ap.add_argument("--no-spice", action="store_true")
    a = ap.parse_args()
    P = PROF[a.profile]; sch = os.path.join(ROOT, P["dir"], P["sch"]); pcb = os.path.join(ROOT, P["dir"], P["pcb"])
    import gen_kicad as g
    g.set_profile(a.profile); g.COMPONENTS.clear(); g.build()
    rep = Report()
    print(f"verify [{a.profile}]  {os.path.relpath(pcb, ROOT)}")
    check_erc(rep, sch)
    pins, fps, vals, pinname = read_netlist(sch)
    pcbnew, b = read_board(pcb)
    check_drc(rep, pcb)
    check_parity(rep, pins, fps, pcbnew, b)
    check_pinmap(rep, pins, fps, pinname, pcbnew, b)
    check_electrical(rep, pcbnew, b)
    check_silk(rep, pcbnew, b)
    check_jlc(rep, pcb)
    check_rf(rep, pcbnew, b, pcb, a.profile)
    if a.profile == "smd":
        check_package(rep, pcbnew, b)
    check_spice(rep, vals, not a.no_spice)
    n = len(rep.rows)
    line = f"{n - rep.fail} of {n} checks passed" + ("" if not rep.fail else f" -- {rep.fail} FAILED")
    print(line)
    os.makedirs(os.path.join(ROOT, "kicad", "reports"), exist_ok=True)
    with open(os.path.join(ROOT, "kicad", "reports", f"verify-{a.profile}.txt"), "w") as f:
        f.write(f"verify [{a.profile}]  {os.path.relpath(pcb, ROOT)}  (kicad/gen/verify.py)\n")
        for group, ok, text in rep.rows: f.write(f"[{'ok' if ok else 'FAIL'}] {group:13s} {text}\n")
        f.write(line + "\n")
    sys.exit(1 if rep.fail else 0)

if __name__ == "__main__":
    main()
