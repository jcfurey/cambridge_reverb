#!/usr/bin/env python3
"""JLCPCB / LCSC part selection for the SMD side of the mixed board -- the one table
that says WHICH real part goes on every SMD pad.

Every entry was looked up in JLCPCB's assembly parts library on SNAPSHOT (stock,
basic / extended class, package, rating, dielectric); nothing here is a guessed
number. Stock moves, so re-check right before ordering:

    python3 kicad/gen/jlc_parts.py            # print the table (offline)
    python3 kicad/gen/jlc_parts.py --check    # query JLCPCB live: stock, class, package

`--check` exits non-zero if a part is out of stock, has less than MIN_STOCK, or
changed class (basic <-> extended changes the price: extended parts cost a one-off
loading fee per part TYPE per order; "preferred" extended parts do not).

Dielectric policy (why eleven capacitor lines are extended): C0G / NP0 wherever the
capacitor is in the signal path at high impedance or sets a frequency -- the preamp
and reverb-recovery coupling caps (a DC-biased X7R on a 1 M node in a combo cabinet is
a microphone), the tone stack, the MRB tank, the RF stoppers, the power-amp feedback
cap. X7R only for supply bypass, the bridge snubbers (100 V) and the 1 uF coupling /
LFO caps, where no C0G exists in 1206. Of the values this board needs, JLCPCB's basic
library holds two 1206 capacitors (100 nF and 1 uF X7R 50 V); the C0G values above
100 pF came back as extended parts in 0603, 0805 and 1206 alike, so a different
footprint would not have saved the loading fees.
"""
import sys, json, time, argparse

SNAPSHOT = "2026-11-11"
MIN_STOCK = 100            # --check warns below this (five boards need at most 70 of one line)

# ---- which capacitor references are C0G (signal path / frequency-setting) ------------
C0G_REFS = {
    "C_in_pre", "C_rf1", "C_pres", "C_cpl12",                       # preamp
    "C_j1", "C_j2", "C_j3", "C_j4", "C_res", "C_gg", "C_treble",    # tone stack
    "C_drvin", "C_rev2", "C_rf2", "C_rev4",                         # reverb
    "C_mrb_in", "C_mrb_600", "C_mrb_out",                           # MRB
    "C_fb_hf",                                                      # power-amp HF roll-off
}
# 100 nF X7R that sits on / swings to the 33.5 V rail: 100 V parts for all four bypass /
# Zobel caps (one line; a 50 V part on a rail that reaches 37-40 V unloaded is too close)
X7R_100V_REFS = {"C_byp1", "C_zobel", "C_byp3", "C_reg_out2", "C101", "C102", "C103", "C104"}

def P(lcsc, mpn, mfr, cls, comment, stock):
    return dict(lcsc=lcsc, mpn=mpn, mfr=mfr, cls=cls, comment=comment, stock=stock)

# (kind, value) -> part.  kind: R0805 / R1206 / C0G / X7R / X7R100 / D_SMA / JFET / NPN
PARTS = {
    # --- resistors, 0805 1 % thick film (UNI-ROYAL 0805W8F...), 125 mW / 150 V
    ("R0805", "10R"):   P("C17415",  "0805W8F100JT5E",  "UNI-ROYAL", "basic",     "10R 1% 0805",  5135932),
    ("R0805", "100R"):  P("C17408",  "0805W8F1000T5E",  "UNI-ROYAL", "basic",     "100R 1% 0805", 7046027),
    ("R0805", "240R"):  P("C17572",  "0805W8F2400T5E",  "UNI-ROYAL", "preferred", "240R 1% 0805",  138734),
    ("R0805", "470R"):  P("C17710",  "0805W8F4700T5E",  "UNI-ROYAL", "basic",     "470R 1% 0805", 1865483),
    ("R0805", "1k"):    P("C17513",  "0805W8F1001T5E",  "UNI-ROYAL", "basic",     "1k 1% 0805",  40233399),
    ("R0805", "4.7k"):  P("C17673",  "0805W8F4701T5E",  "UNI-ROYAL", "basic",     "4.7k 1% 0805", 4271521),
    ("R0805", "10k"):   P("C17414",  "0805W8F1002T5E",  "UNI-ROYAL", "basic",     "10k 1% 0805", 49038635),
    ("R0805", "15k"):   P("C17475",  "0805W8F1502T5E",  "UNI-ROYAL", "basic",     "15k 1% 0805",   536585),
    ("R0805", "22k"):   P("C17560",  "0805W8F2202T5E",  "UNI-ROYAL", "basic",     "22k 1% 0805",  1323637),
    ("R0805", "68k"):   P("C17801",  "0805W8F6802T5E",  "UNI-ROYAL", "basic",     "68k 1% 0805",   270492),
    ("R0805", "100k"):  P("C149504", "0805W8F1003T5E",  "UNI-ROYAL", "basic",     "100k 1% 0805", 2544046),
    ("R0805", "180k"):  P("C17501",  "0805W8F1803T5E",  "UNI-ROYAL", "preferred", "180k 1% 0805",   88382),
    ("R0805", "220k"):  P("C17556",  "0805W8F2203T5E",  "UNI-ROYAL", "basic",     "220k 1% 0805",  488709),
    ("R0805", "1M"):    P("C17514",  "0805W8F1004T5E",  "UNI-ROYAL", "basic",     "1M 1% 0805",   1656683),
    # --- LM317 set resistor, E96, 85 mW -> 1206 (250 mW)
    ("R1206", "3.09k"): P("C2091788", "CRCW12063K09FKEA", "Vishay",  "extended",  "3.09k 1% 1206", 4950),
    # --- C0G / NP0, 1206
    ("C0G", "100pF"):   P("C107179",  "CC1206JRNPO9BN101", "YAGEO",  "extended",  "100pF 50V C0G 5% 1206",  34304),
    ("C0G", "470pF"):   P("C113880",  "CC1206JRNPO0BN471", "YAGEO",  "extended",  "470pF 100V C0G 5% 1206",  5650),
    ("C0G", "1nF"):     P("C113881",  "CC1206JRNPO9BN102", "YAGEO",  "extended",  "1nF 50V C0G 5% 1206",    13320),
    ("C0G", "2.2nF"):   P("C326631",  "CC1206JRNPO9BN222", "YAGEO",  "extended",  "2.2nF 50V C0G 5% 1206",  19543),
    ("C0G", "10nF"):    P("C326648",  "CC1206JKNPO9BN103", "YAGEO",  "extended",  "10nF 50V C0G 5% 1206",   23303),
    ("C0G", "22nF"):    P("C7500389", "CC1206JRNPO9BN223", "YAGEO",  "extended",  "22nF 50V C0G 5% 1206",   10978),
    ("C0G", "47nF"):    P("C5451690", "C1206N473J050T",    "HOLY STONE (IHHEC)", "extended", "47nF 50V C0G 5% 1206", 1184),
    ("C0G", "68nF"):    P("C711038",  "GRM31C5C2A683JA01L", "Murata", "extended", "68nF 100V C0G 5% 1206",    215),
    ("C0G", "100nF"):   P("C170182",  "1206N104J500CT",    "Walsin", "extended",  "100nF 50V C0G 5% 1206", 145451),
    # --- X7R, 1206
    ("X7R100", "10nF"): P("C107204",  "CC1206KRX7R0BB103", "YAGEO",  "extended",  "10nF 100V X7R 10% 1206",  16770),
    ("X7R100", "100nF"): P("C107181", "CC1206KKX7R0BB104", "YAGEO",  "extended",  "100nF 100V X7R 10% 1206", 63874),
    ("X7R", "1uF"):     P("C1848",    "CL31B105KBHNNNE",   "Samsung", "basic",    "1uF 50V X7R 10% 1206",   753353),
    # --- semiconductors
    ("D_SMA", "1N4007"): P("C95872",  "M7",                "MDD",    "basic",     "M7 (1N4007, 1 kV 1 A, SMA)", 5380312),
    ("JFET", "MMBF5457"): P("C2830807", "MMBF5457",        "onsemi", "extended",  "MMBF5457 N-JFET SOT-23",   40537),
    ("NPN", "2N3904"):  P("C20526",   "MMBT3904",          "Jiangsu Changjing (JSCJ)", "basic", "MMBT3904 NPN SOT-23", 4303491),
}
# what the live library must say about each part's package (checked by --check)
PKG = {"R0805": "0805", "R1206": "1206", "C0G": "1206", "X7R": "1206", "X7R100": "1206",
       "D_SMA": "SMA", "JFET": "SOT-23", "NPN": "SOT-23"}

def base_value(value):
    """'10nF/100V' -> '10nF', '1uF film' -> '1uF' (rating / dielectric come from the table)."""
    return value.split("/")[0].split(" ")[0]

def kind_for(c):
    """Part kind for a gen_kicad component record on the SMD profile, or None if THT."""
    fp = (c["fp"] or "").split(":")[-1]; ref = c["ref"]
    if fp.startswith("R_0805"): return "R0805"
    if fp.startswith("R_1206"): return "R1206"
    if fp.startswith("C_1206"):
        if ref in C0G_REFS: return "C0G"
        return "X7R100" if ref in X7R_100V_REFS else "X7R"
    if fp.startswith("D_SMA"): return "D_SMA"
    if fp.startswith("SOT-23_MMBT3904"): return "NPN"
    if fp == "SOT-23": return "JFET"
    return None

def part_for(c):
    k = kind_for(c)
    if k is None or "(opt)" in c["value"]:       # THT part, or a do-not-place option
        return None
    key = (k, base_value(c["value"]))
    if key not in PARTS:
        raise KeyError(f"{c['ref']}: no JLCPCB part selected for {key} -- add it to jlc_parts.PARTS (look it up, do not guess)")
    return dict(PARTS[key], kind=k)

# ---- live check ----------------------------------------------------------------------
URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
def lookup(lcsc):
    import urllib.request
    req = urllib.request.Request(URL, data=json.dumps({"keyword": lcsc, "currentPage": 1, "pageSize": 10}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    err = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                rows = (json.load(r).get("data") or {}).get("componentPageInfo", {}).get("list") or []
            for c in rows:
                if c.get("componentCode") == lcsc:
                    return c
            return None
        except Exception as e:           # network hiccup: back off and retry
            err = e; time.sleep(2 * (attempt + 1))
    raise err

def live_class(c):
    if c.get("componentLibraryType") == "base": return "basic"
    return "preferred" if c.get("preferredComponentFlag") else "extended"

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="query JLCPCB for current stock / class / package")
    a = ap.parse_args()
    bad = 0
    print(f"{'kind':7s} {'value':7s} {'LCSC':9s} {'class':9s} {'MPN':20s} {'stock@' + SNAPSHOT:>17s}" + ("   live" if a.check else ""))
    for (kind, value), p in sorted(PARTS.items()):
        line = f"{kind:7s} {value:7s} {p['lcsc']:9s} {p['cls']:9s} {p['mpn']:20s} {p['stock']:>17d}"
        if a.check:
            c = lookup(p["lcsc"]); time.sleep(0.4)
            if c is None:
                line += "   ** NOT FOUND **"; bad += 1
            else:
                cls, stock, pkg, mpn = live_class(c), c.get("stockCount", 0), str(c.get("componentSpecificationEn")), str(c.get("componentModelEn"))
                flags = []
                if stock < MIN_STOCK: flags.append("LOW STOCK" if stock else "OUT OF STOCK")
                if cls != p["cls"]: flags.append(f"class now {cls}")
                if PKG[kind] not in pkg: flags.append(f"package {pkg}")
                if p["mpn"].split("(")[0].strip().lower() not in mpn.lower(): flags.append(f"MPN {mpn}")
                bad += bool(flags)
                line += f"   {stock:>9d} {cls:9s} {pkg:14s}" + ("  ** " + ", ".join(flags) + " **" if flags else "  ok")
        print(line)
    n = collections_count()
    print(f"{len(PARTS)} lines: {n['basic']} basic, {n['preferred']} preferred-extended (no fee), {n['extended']} extended")
    if a.check:
        print("live check:", "all parts in stock, classes unchanged" if not bad else f"{bad} line(s) need attention")
    sys.exit(1 if bad else 0)

def collections_count():
    n = {"basic": 0, "preferred": 0, "extended": 0}
    for p in PARTS.values():
        n[p["cls"]] += 1
    return n

if __name__ == "__main__":
    main()
