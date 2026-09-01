#!/usr/bin/env python3
"""Rewrite every (model "...") path in controlcarreta.kicad_pcb to point at the
project-local, organised 3d_models/ tree ( ${KIPRJMOD}/3d_models/<cat>/<file> ).

Run this AFTER "Update PCB from Schematic" in Pcbnew, then reload the board.
It is idempotent — safe to run repeatedly. A .bak is written next to the PCB.

    python3 scripts/relink_3d.py
"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PCB = os.path.join(PROJ, "controlcarreta.kicad_pcb")
MAN = os.path.join(PROJ, "3d_models", "manifest.json")

manifest = json.load(open(MAN))
# footprint-id -> "${KIPRJMOD}/3d_models/<cat>/<file>"   (first model only)
fp2model = {}
for fp, e in manifest.items():
    mods = e.get("models") or []
    if mods:
        fp2model[fp] = "${KIPRJMOD}/" + mods[0].replace(os.sep, "/")

if not os.path.isfile(PCB):
    sys.exit("PCB not found: " + PCB)
src = open(PCB, encoding="utf-8").read()
shutil.copy2(PCB, PCB + ".bak")

out = []
pos = 0
n_fixed = n_fp = n_skip = 0
for m in re.finditer(r'\(footprint "([^"]+)"', src):
    fpid = m.group(1)
    nxt = src.find('(footprint "', m.start() + 12)
    end = nxt if nxt > 0 else len(src)
    blk = src[m.start():end]
    n_fp += 1
    new_model = fp2model.get(fpid)
    if new_model:
        blk2, k = re.subn(r'(\(model )"[^"]*"', lambda _m: _m.group(1) + '"' + new_model + '"', blk, count=1)
        if k:
            blk = blk2
            n_fixed += 1
        else:
            n_skip += 1  # footprint has no (model) line (e.g. MountingHole)
    else:
        n_skip += 1
    out.append(src[pos:m.start()])
    out.append(blk)
    pos = end
out.append(src[pos:])
open(PCB, "w", encoding="utf-8").write("".join(out))

print("footprints seen : %d" % n_fp)
print("model paths fixed: %d" % n_fixed)
print("skipped (no model / not in manifest): %d" % n_skip)
print("backup: %s" % (PCB + ".bak"))
un = sorted(f for f, e in manifest.items() if not (e.get("models")))
if un:
    print("\nStill without a local model (assign by hand in Pcbnew):")
    for f in un:
        print("  -", f, "->", manifest[f].get("note", ""))
