#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Random text generator (no source folder).
Generates random Tool Switching instances for given (M, N, C) triples and
emits our TEXT format:

  M N C
  COST c1..cM
  JOBS N
  k  t1 .. tk
"""

import random
import shutil
from pathlib import Path

OUT_DIR = r"../tests_txt"
SEED    = random.randint(1, 1000)
CMIN    = 1
CMAX    = 5

# Список наборов инстансов:
# для каждой строки (M, N, C, count) будет создано `count` случайных инстансов
INSTANCE_SPECS = [
    # (M, N, C, count)
    
    # добавляй сюда свои наборы
    # (M, N, C, count),
]
for i in range(4, 25):
    k = 2
    adds = (int(i), int(k * i), int(i**0.5), 1)
    #adds = (2, 3, 2)
    for i in range (1):
        INSTANCE_SPECS.append(adds)
    

def clean_output_directory(out_dir: Path):
    """Полностью удалить и пересоздать директорию вывода"""
    if out_dir.exists():
        shutil.rmtree(out_dir)
        print(f"Removed existing directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created clean directory: {out_dir}")


def generate_random_jobs(M, N, C):
    """
    Генерирует список работ.
    Для каждой работы j выбираем случайное число инструментов:
      k ∈ [1, min(M, C)],
    инструменты выбираются без повторов из {1, ..., M}.
    """
    jobs = []
    max_k = min(M, C)
    for _ in range(N):
        k = random.randint(1, max_k)
        tools = random.sample(range(1, M + 1), k)
        tools.sort()
        jobs.append(tools)
    return jobs


def dump_text(M, N, C, jobs, cvec):
    lines = []
    lines.append("# Tool Switching Instance (random)")
    lines.append(f"{M} {N} {C}")
    lines.append("COST " + " ".join(str(x) for x in cvec))
    lines.append(f"JOBS {N}")
    for tools in jobs:
        lines.append(str(len(tools)) + " " + " ".join(str(t) for t in tools))
    return "\n".join(lines) + "\n"


def main():
    random.seed(SEED)

    out_path = Path(OUT_DIR)
    clean_output_directory(out_path)

    total = 0
    for (M, N, C, count) in INSTANCE_SPECS:
        for idx in range(count):
            jobs = generate_random_jobs(M, N, C)
            cvec = [random.randint(CMIN, CMAX) for _ in range(M)]

            out_name = f"rand_M{M}_N{N}_C{C}_id{idx:03d}.txt"
            out_file_path = out_path / out_name

            with open(out_file_path, "w", encoding="utf-8") as f:
                f.write(dump_text(M, N, C, jobs, cvec))

            total += 1

    print(f"Wrote {total} random instances to {OUT_DIR}")


if __name__ == "__main__":
    main()
