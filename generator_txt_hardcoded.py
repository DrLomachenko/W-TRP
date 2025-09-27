#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text test generator for the Tool Switching Problem (PF1995-style).
This version uses HARD-CODED constants — no CLI arguments.
"""

import os, random

# =========================
# HARD-CODED PARAMETERS
# =========================
OUT_DIR = "tests_txt"
COUNT   = 10
M       = 110
N       = 90
C       = 70
FILL    = 0.7     # ~density factor for tools per job
SEED    = 42
CMIN    = 1
CMAX    = 10
MODE    = "cost"  # "cost" (column-constant) or "matrix" (full MxM)
# =========================

def make_instance(seed: int, M: int, N: int, C: int, fill_rate: float,
                  cmin: int, cmax: int, mode: str):
    rng = random.Random(seed)
    assert 1 <= C <= M, "C must be in [1..M]"
    # Generate jobs
    jobs = []
    for _ in range(N):
        # heuristic: ~0.2*M tools per job scaled by fill
        k = max(1, int(round(fill_rate * M * 0.2)))
        k = min(k, M)
        tools = sorted(rng.sample(range(1, M+1), k))
        jobs.append(tools)

    if mode == "cost":
        c = [rng.randint(cmin, cmax) for _ in range(M)]
        return {"M":M, "N":N, "C":C, "c":c, "jobs":jobs, "mode":"cost"}
    else:
        # Full matrix
        D = [[0]*M for _ in range(M)]
        for i in range(M):
            for j in range(M):
                if i==j:
                    D[i][j]=0
                else:
                    D[i][j]=rng.randint(cmin, cmax)
        return {"M":M, "N":N, "C":C, "D":D, "jobs":jobs, "mode":"matrix"}

def dump_text(inst) -> str:
    M, N, C = inst["M"], inst["N"], inst["C"]
    lines = []
    lines.append("# Tool Switching Instance")
    lines.append(f"{M} {N} {C}")
    if inst.get("mode") == "cost":
        c = inst["c"]
        lines.append("COST " + " ".join(str(x) for x in c))
    else:
        D = inst["D"]
        lines.append("MATRIX")
        for i in range(M):
            lines.append(" ".join(str(x) for x in D[i]))
    lines.append(f"JOBS {N}")
    for tools in inst["jobs"]:
        lines.append(str(len(tools)) + " " + " ".join(str(t) for t in tools))
    return "\n".join(lines) + "\n"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for k in range(COUNT):
        inst = make_instance(seed=SEED + k, M=M, N=N, C=C,
                             fill_rate=FILL, cmin=CMIN, cmax=CMAX,
                             mode=MODE)
        fname = os.path.join(OUT_DIR,
                f"pf1995_txt_M{M}_N{N}_C{C}_{MODE}_id{k:03d}.txt")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(dump_text(inst))
    print(f"Generated {COUNT} tests in {os.path.abspath(OUT_DIR)}")

if __name__ == "__main__":
    main()
