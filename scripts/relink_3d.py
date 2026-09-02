#!/usr/bin/env python3
"""Rewrite every (model "...") path in controlcarreta.kicad_pcb to point at the
project-local, organised 3DSHAPES/ tree ( ${KIPRJMOD}/3DSHAPES/<cat>/<file> ).

Run this AFTER "Update PCB from Schematic" in Pcbnew, then reload the board.
It is idempotent — safe to run repeatedly. A .bak is written next to the PCB.

    python3 scripts/relink_3d.py
"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PCB = os.path.join(PROJ, "controlcarreta.kicad_pcb")
MAN = os.path.join(PROJ, "3DSHAPES", "manifest.json")

manifest = json.load(open(MAN))
# footprint-id -> "${KIPRJMOD}/3DSHAPES/<cat>/<file>"   (first model only)
fp2model = {}
for fp, e in manifest.items():
    mods = e.get("models") or []
    if mods:
        fp2model[fp] = "${KIPRJMOD}/" + mods[0].replace(os.sep, "/")

if not os.path.isfile(PCB):
    sys.exit("PCB not found: " + PCB)
src = open(PCB, encoding="utf-8").read()
shutil.copy2(PCB, PCB + ".bak")

def _sexpr_end(text, start):
    """index just past the s-expression that opens at text[start] == '('"""
    depth, i, in_str = 0, start, False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == '\\':
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def drop_dup_models(blk, keep_path):
    """remove extra (model ...) blocks that point at the same file as keep_path
    (old absolute paths left behind by earlier edits); keep the first one."""
    want = os.path.basename(keep_path).lower()
    seen = False
    while True:
        for m in re.finditer(r'\(model\s+"([^"]+)"', blk):
            if os.path.basename(m.group(1)).lower() != want:
                continue
            if not seen:
                seen = True
                continue
            beg = m.start()
            end = _sexpr_end(blk, beg)
            while beg > 0 and blk[beg - 1] in ' \t':
                beg -= 1
            if beg > 0 and blk[beg - 1] == '\n':
                beg -= 1
            return_blk = blk[:beg] + blk[end:]
            break
        else:
            return blk
        blk, seen = return_blk, False


out = []
pos = 0
n_fixed = n_fp = n_skip = n_dup = 0
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
            blk3 = drop_dup_models(blk, new_model)
            if blk3 != blk:
                n_dup += 1
                blk = blk3
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
print("duplicate model blocks removed: %d" % n_dup)
print("backup: %s" % (PCB + ".bak"))
un = sorted(f for f, e in manifest.items() if not (e.get("models")))
if un:
    print("\nStill without a local model (assign by hand in Pcbnew):")
    for f in un:
        print("  -", f, "->", manifest[f].get("note", ""))
