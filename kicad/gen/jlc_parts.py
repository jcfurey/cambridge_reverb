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

Dielectric policy: C0G / NP0 wherever the capacitor is in the signal path at high
impedance or sets a frequency -- the preamp and reverb-recovery coupling caps (a DC-biased
X7R on a 1 M node in a combo cabinet is a microphone), the tone stack, the MRB tank, the RF
stoppers, the power-amp input low-pass. X7R only for supply bypass, the bridge snubbers
(100 V) and the 1 uF coupling / LFO caps, where no C0G exists.

Cost policy (2026-11-12): an EXTENDED part costs a loading fee per part type per order
($3.07; basic and "preferred" parts none), so the circuit uses the values JLCPCB keeps as
basic parts wherever that costs nothing: C0G 33 pF, 100 pF and 2.2 nF and the 100 V X7R
100 nF are basic in 0805 (not in 1206, where the first version of this table looked), so
those footprints are 0805. What is left as extended is what has no basic equivalent:
the two large C0G values (22 nF, 100 nF) and the JFET. 14 extended lines became 3.
"""
import sys, json, time, argparse

SNAPSHOT = "2026-11-12"
MIN_STOCK = 500            # --check warns below this (five boards need at most 75 of one line)

# ---- which capacitor references are C0G (signal path / frequency-setting) ------------
C0G_REFS = {
    "C_in_pre", "C_rf1", "C_pres", "C_cpl12",                       # preamp
    "C_j1", "C_j2", "C_j3", "C_j4", "C_res", "C_gg",                # tone stack (the bright cap C_treble is fitted by hand)
    "C_drvin", "C_rev2", "C_rf2", "C_rev4", "C_mixfb",              # reverb
    "C_mrb_in", "C_mrb_600", "C_mrb_600b", "C_mrb_600c", "C_mrb_out",   # MRB
    "C_lp",                                                         # power-amp input low-pass
}
# every "100nF/100V" in the schematic: the rail bypass / Zobel caps (a 50 V part on a rail that
# reaches 37-40 V unloaded is too close) and the four bridge snubbers (reverse voltage 2 x Vpk)

def P(lcsc, mpn, mfr, cls, comment, stock):
    return dict(lcsc=lcsc, mpn=mpn, mfr=mfr, cls=cls, comment=comment, stock=stock)

# (kind, value) -> part.  kind: R0805 / C0G (1206) / C0G0805 / X7R (1206) / X7R100 (0805) / D_SMA / JFET / NPN
PARTS = {
    # --- resistors, 0805 1 % thick film (UNI-ROYAL 0805W8F...), 125 mW / 150 V
    ("R0805", "10R"):   P("C17415",  "0805W8F100JT5E",  "UNI-ROYAL", "basic",     "10R 1% 0805",  5060759),
    ("R0805", "100R"):  P("C17408",  "0805W8F1000T5E",  "UNI-ROYAL", "basic",     "100R 1% 0805", 6913131),
    ("R0805", "240R"):  P("C17572",  "0805W8F2400T5E",  "UNI-ROYAL", "preferred", "240R 1% 0805",  271123),
    ("R0805", "470R"):  P("C17710",  "0805W8F4700T5E",  "UNI-ROYAL", "basic",     "470R 1% 0805", 1798840),
    ("R0805", "1k"):    P("C17513",  "0805W8F1001T5E",  "UNI-ROYAL", "basic",     "1k 1% 0805",  39835633),
    ("R0805", "4.7k"):  P("C17673",  "0805W8F4701T5E",  "UNI-ROYAL", "basic",     "4.7k 1% 0805", 4040609),
    ("R0805", "10k"):   P("C17414",  "0805W8F1002T5E",  "UNI-ROYAL", "basic",     "10k 1% 0805", 48472575),
    ("R0805", "15k"):   P("C17475",  "0805W8F1502T5E",  "UNI-ROYAL", "basic",     "15k 1% 0805",   503718),
    ("R0805", "22k"):   P("C17560",  "0805W8F2202T5E",  "UNI-ROYAL", "basic",     "22k 1% 0805",  1293120),
    ("R0805", "68k"):   P("C17801",  "0805W8F6802T5E",  "UNI-ROYAL", "basic",     "68k 1% 0805",   257818),
    ("R0805", "100k"):  P("C149504", "0805W8F1003T5E",  "UNI-ROYAL", "basic",     "100k 1% 0805", 2440596),
    ("R0805", "180k"):  P("C17501",  "0805W8F1803T5E",  "UNI-ROYAL", "preferred", "180k 1% 0805",   81957),
    ("R0805", "220k"):  P("C17556",  "0805W8F2203T5E",  "UNI-ROYAL", "basic",     "220k 1% 0805",  484887),
    ("R0805", "10M"):   P("C26108",  "0805W8F1005T5E",  "UNI-ROYAL", "preferred", "10M 1% 0805",     56192),
    ("R0805", "1M"):    P("C17514",  "0805W8F1004T5E",  "UNI-ROYAL", "basic",     "1M 1% 0805",   1609832),
    ("R0805", "0R"):    P("C17477",  "0805W8F0000T5E",  "UNI-ROYAL", "basic",     "0R 0805 (jumper)", 3873967),
    ("R0805", "1.5k"):  P("C4310",   "0805W8F1501T5E",  "UNI-ROYAL", "basic",     "1.5k 1% 0805",  942696),
    # --- C0G / NP0 that JLCPCB keeps as BASIC (or preferred) parts: 0805
    ("C0G0805", "33pF"):  P("C107115", "CC0805JRNPO9BN330", "YAGEO",   "preferred", "33pF 50V C0G 5% 0805",  1008956),
    ("C0G0805", "100pF"): P("C1790",   "CL21C101JBANNNC",   "Samsung", "basic",     "100pF 50V C0G 5% 0805",  679953),
    ("C0G0805", "2.2nF"): P("C28260",  "CL21C222JBFNNNE",   "Samsung", "basic",     "2.2nF 50V C0G 5% 0805",  370139),
    # --- C0G / NP0, 1206: the two values with no basic equivalent in any size
    ("C0G", "22nF"):    P("C7500389", "CC1206JRNPO9BN223", "YAGEO",  "extended",  "22nF 50V C0G 5% 1206",   10952),
    ("C0G", "100nF"):   P("C170182",  "1206N104J500CT",    "Walsin", "extended",  "100nF 50V C0G 5% 1206", 143396),
    # --- X7R
    ("X7R100", "100nF"): P("C28233",  "CL21B104KCFNNNE",   "Samsung", "basic",    "100nF 100V X7R 10% 0805", 2960530),
    ("X7R", "2.2uF"):   P("C50254",   "CL31B225KBHNNNE",   "Samsung", "basic",    "2.2uF 50V X7R 10% 1206",  317676),
    ("X7R", "1uF"):     P("C1848",    "CL31B105KBHNNNE",   "Samsung", "basic",    "1uF 50V X7R 10% 1206",   725516),
    # --- semiconductors
    ("D_SMA", "1N4007"): P("C95872",  "M7",                "MDD",    "basic",     "M7 (1N4007, 1 kV 1 A, SMA)", 6489784),
    ("JFET", "MMBF5457"): P("C2830807", "MMBF5457",        "onsemi", "extended",  "MMBF5457 N-JFET SOT-23",   40507),
    ("NPN", "2N3904"):  P("C20526",   "MMBT3904",          "Jiangsu Changjing (JSCJ)", "basic", "MMBT3904 NPN SOT-23", 4181453),
}
# unit price in USD at the 1-piece tier on SNAPSHOT (jlc_cost.py; the quote decides)
PRICE = {
    "C26108": 0.0049, "C50254": 0.0609,
    "C107115": 0.0069, "C149504": 0.0059, "C170182": 0.1576, "C17408": 0.0042, "C17414": 0.0034,
    "C17415": 0.004, "C17475": 0.0041, "C17477": 0.0046, "C17501": 0.0032, "C17513": 0.0035,
    "C17514": 0.0044, "C17556": 0.0028, "C17560": 0.0048, "C17572": 0.0036, "C17673": 0.0034,
    "C17710": 0.0048, "C17801": 0.0029, "C1790": 0.0092, "C1848": 0.0506, "C20526": 0.0103,
    "C28233": 0.0161, "C28260": 0.0369, "C2830807": 0.3085, "C4310": 0.0028, "C7500389": 0.2523,
    "C95872": 0.0103,
}
# what the live library must say about each part's package (checked by --check)
PKG = {"R0805": "0805", "C0G": "1206", "C0G0805": "0805", "X7R": "1206", "X7R100": "0805",
       "D_SMA": "SMA", "JFET": "SOT-23", "NPN": "SOT-23"}

def base_value(value):
    """'10nF/100V' -> '10nF', '1uF film' -> '1uF' (rating / dielectric come from the table)."""
    return value.split("/")[0].split(" ")[0]

def kind_for(c):
    """Part kind for a gen_kicad component record on the SMD profile, or None if THT."""
    fp = (c["fp"] or "").split(":")[-1]; ref = c["ref"]
    if fp.startswith("R_0805"): return "R0805"
    if fp.startswith("C_0805"):
        return "C0G0805" if ref in C0G_REFS else "X7R100"
    if fp.startswith("C_1206"):
        return "C0G" if ref in C0G_REFS else "X7R"
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
    print(f"{'kind':8s} {'value':7s} {'LCSC':9s} {'class':9s} {'MPN':20s} {'stock@' + SNAPSHOT:>17s}" + ("   live" if a.check else ""))
    for (kind, value), p in sorted(PARTS.items()):
        line = f"{kind:8s} {value:7s} {p['lcsc']:9s} {p['cls']:9s} {p['mpn']:20s} {p['stock']:>17d}"
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
