#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alternative text generator (hardcoded source folder).
Reads instances from a matrix format (Tabela1), shuffles jobs, assigns random COST per tool,
and emits our TEXT format:
  M N C
  COST c1..cM
  JOBS N
  k  t1 .. tk
"""

import os, random
from pathlib import Path

SRC_DIR = r"Tabela1"
OUT_DIR = r"tests_txt"
SEED    = 12345
CMIN    = 1
CMAX    = 5

def read_tabela1(path: Path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        line1 = f.readline().strip()
        line2 = f.readline().strip()
        line3 = f.readline().strip()
        if not (line1 and line2 and line3):
            raise ValueError("Bad header in " + str(path))
        M = int(line1)  # tools
        N = int(line2)  # jobs
        C = int(line3)  # capacity
        rows = []
        while len(rows) < N:
            row = f.readline()
            if not row:
                break
            toks = [t for t in row.strip().split() if t]
            vals = []
            for t in toks:
                try:
                    vals.append(int(t))
                except:
                    pass
            while len(vals) < M:
                nxt = f.readline()
                if not nxt:
                    break
                toks2 = [t for t in nxt.strip().split() if t]
                for t in toks2:
                    try: vals.append(int(t))
                    except: pass
            if len(vals) == M:
                rows.append(vals[:M])
        if len(rows) != N:
            raise ValueError(f"Expected N={N} rows of M={M}, got {len(rows)} in {{path}}")
        return M, N, C, rows

def to_jobs(rows):
    jobs = []
    for r in rows:
        tools = [j+1 for j,bit in enumerate(r) if bit!=0]
        jobs.append(tools)
    return jobs

def dump_text(M, N, C, jobs, cvec):
    lines = []
    lines.append("# Tool Switching Instance")
    lines.append(f"{M} {N} {C}")
    lines.append("COST " + " ".join(str(x) for x in cvec))
    lines.append(f"JOBS {N}")
    for tools in jobs:
        lines.append(str(len(tools)) + " " + " ".join(str(t) for t in tools))
    return "\n".join(lines) + "\n"

def main():
    random.seed(SEED)
    os.makedirs(OUT_DIR, exist_ok=True)
    src = Path(SRC_DIR)
    files = sorted([p for p in src.iterdir() if p.is_file() and p.name.startswith("dat")])
    count = 0
    for p in files:
        try:
            M, N, C, rows = read_tabela1(p)
        except Exception as e:
            print("Skip", p.name, ":", e)
            continue
        jobs = to_jobs(rows)
        random.shuffle(jobs)
        cvec = [random.randint(CMIN, CMAX) for _ in range(M)]
        out_name = f"from_{p.name}_M{M}_N{N}_C{C}.txt"
        out_path = Path(OUT_DIR) / out_name
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(dump_text(M, N, C, jobs, cvec))
        count += 1
    print(f"Wrote {count} instances to {OUT_DIR}")

if __name__ == "__main__":
    main()
