#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_txt_only_robust.py
Читает ТОЛЬКО .txt, устойчив к разным форматам исходников.
Пропускает уже-конвертированные файлы.
Все пути жестко заданы в INPUT_DIR / OUTPUT_DIR.
"""

import os
import re
from pathlib import Path

# ===== ЖЁСТКИЕ ПУТИ =====
INPUT_DIR  = "../raw_data_for_tests/tux"   # сюда кладём ИСХОДНЫЕ txt
OUTPUT_DIR = "tests_txt"       # сюда пишем КОНВЕРТИРОВАННЫЕ txt
# ========================

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Регулярки
RE_N = re.compile(r'^\s*n\s*=\s*(\d+)\s*$', re.I)
RE_M = re.compile(r'^\s*m\s*=\s*(\d+)\s*$', re.I)
RE_K = re.compile(r'^\s*k\s*=\s*(\d+)\s*$', re.I)
RE_SETUP = re.compile(r'^\s*setup[_\s]*times\s*[:=]\s*(.*)$', re.I)
RE_PROC  = re.compile(r'^\s*processing[_\s]*times\s*[:=]\s*(.*)$', re.I)
RE_JOBS_HEADER = re.compile(r'^\s*jobs\s*[:=]?\s*$', re.I)
RE_JOB_LINE = re.compile(r'^\s*(?:\{([^}]*)\}|([\d\s,]+))\s*$')
RE_THREE_INTS = re.compile(r'^\s*(\d+)\s+(\d+)\s+(\d+)\s*$')
RE_CONVERTED_HEADER = re.compile(r'^\s*#\s*Converted instance', re.I)

def _split_ints(s: str):
    return [int(x) for x in re.split(r'[,\s]+', s.strip()) if x.strip()]

def _strip_comments(lines):
    """Удаляем комментарии (# ... или // ...) и пустые строки."""
    out = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        # обрежем коммент после #
        if '#' in s:
            # если это уже заголовок Converted, сохраняем — пусть решает внешний код
            if RE_CONVERTED_HEADER.match(s):
                out.append(s)
                continue
            s = s.split('#', 1)[0].strip()
        # обрежем // комментарий
        if '//' in s:
            s = s.split('//', 1)[0].strip()
        if s:
            out.append(s)
    return out

def parse_txt_instance(path: Path):
    raw_text = path.read_text(encoding='utf-8', errors='ignore')
    lines_all = raw_text.splitlines()

    # если это уже наш сконвертированный файл — пропускаем
    if lines_all and RE_CONVERTED_HEADER.match(lines_all[0]):
        raise RuntimeError("Already-converted file; skipping")

    lines = _strip_comments(lines_all)

    # Первичный проход по ключам
    M = C = N = None
    setup_times = []
    processing_times = []
    jobs = []
    in_jobs = False

    i = 0
    while i < len(lines):
        line = lines[i]

        m = RE_N.match(line)
        if m:
            M = int(m.group(1)); i += 1; continue

        m = RE_M.match(line)
        if m:
            C = int(m.group(1)); i += 1; continue

        m = RE_K.match(line)
        if m:
            N = int(m.group(1)); i += 1; continue

        m = RE_SETUP.match(line)
        if m:
            rest = m.group(1).strip()
            if rest:
                setup_times = _split_ints(rest)
                i += 1; continue
            # если на следующей строке просто числа — заберём
            if i + 1 < len(lines):
                cand = _split_ints(lines[i+1])
                if cand:
                    setup_times = cand
                    i += 2; continue
            i += 1; continue

        m = RE_PROC.match(line)
        if m:
            # processing_times нам не нужны для вывода, но считaем на всякий
            rest = m.group(1).strip()
            if rest:
                processing_times = _split_ints(rest)
                i += 1; continue
            if i + 1 < len(lines):
                cand = _split_ints(lines[i+1])
                if cand:
                    processing_times = cand
                    i += 2; continue
            i += 1; continue

        if RE_JOBS_HEADER.match(line):
            in_jobs = True
            i += 1
            continue

        if in_jobs:
            # Пытаемся читать до конца как job строки
            mj = RE_JOB_LINE.match(line)
            if mj:
                inside = mj.group(1) or mj.group(2) or ""
                nums = _split_ints(inside)
                if nums:
                    jobs.append(nums)
                i += 1
                continue
            # если пустая/непонятная — просто дальше
            i += 1
            continue

        i += 1

    # Если явного блока jobs не нашли — попробуем распарсить альтернативные форматы
    if not jobs:
        # 1) Проверка «тройка чисел» в первой непустой строке
        first_nonempty = next((s for s in lines if s.strip()), "")
        m3 = RE_THREE_INTS.match(first_nonempty)
        if m3:
            a, b, c = map(int, m3.groups())
            # две гипотезы: (n, m, k) или (k, m, n)
            # Дальше пробуем распарсить тело как jobs в count-prefixed формате
            body = " ".join(_strip_comments(lines[1:]))  # всё, кроме первой строки
            ints = _split_ints(body)

            def parse_jobs_count_prefixed(int_list, jobs_count):
                res = []
                idx = 0
                for _ in range(jobs_count):
                    if idx >= len(int_list):
                        return None
                    t = int_list[idx]; idx += 1
                    if idx + t - 1 >= len(int_list):
                        return None
                    job = int_list[idx: idx + t]; idx += t
                    res.append(job)
                return res

            # гипотеза 1: n=a, m=b, k=c
            cand1_M, cand1_C, cand1_N = a, b, c
            jobs1 = parse_jobs_count_prefixed(ints, cand1_N)
            ok1 = jobs1 is not None and all(jobs1)

            # гипотеза 2: k=a, m=b, n=c
            cand2_N, cand2_C, cand2_M = a, b, c
            jobs2 = parse_jobs_count_prefixed(ints, cand2_N)
            ok2 = jobs2 is not None and all(jobs2)

            if ok1 and not ok2:
                M, C, N = cand1_M, cand1_C, cand1_N
                jobs = jobs1
            elif ok2 and not ok1:
                M, C, N = cand2_M, cand2_C, cand2_N
                jobs = jobs2
            elif ok1 and ok2:
                # выберем тот, где max tool id <= M
                max1 = max((max(j) for j in jobs1 if j), default=0)
                max2 = max((max(j) for j in jobs2 if j), default=0)
                if max1 <= cand1_M and (max2 > cand2_M or cand1_M >= cand2_M):
                    M, C, N, jobs = cand1_M, cand1_C, cand1_N, jobs1
                else:
                    M, C, N, jobs = cand2_M, cand2_C, cand2_N, jobs2
            # если ни одна гипотеза не сработала — оставим jobs пустыми и ниже ещё попробуем

        # 2) Если «тройка чисел» не помогла — соберём все строки, похожие на job: {…} или «числа числа»
        if not jobs:
            possible_jobs = []
            for s in lines:
                mj = RE_JOB_LINE.match(s)
                if mj:
                    inside = mj.group(1) or mj.group(2) or ""
                    nums = _split_ints(inside)
                    if nums:
                        possible_jobs.append(nums)
            if possible_jobs:
                jobs = possible_jobs

    # Доопределяем параметры
    max_tool = max((max(j) for j in jobs if j), default=0)
    if M is None:
        M = max_tool if max_tool > 0 else (len(setup_times) if setup_times else 1)
    if C is None:
        C = max(1, min(M - 1, 10))
    if N is None:
        N = len(jobs)

    # Стоимости
    if setup_times:
        costs = (setup_times[:M] + [setup_times[-1]] * max(0, M - len(setup_times)))
    else:
        costs = [1] * M

    return {"M": M, "C": C, "N": N, "costs": costs, "jobs": jobs}

def write_converted(instance, out_path: Path):
    with out_path.open('w', encoding='utf-8') as f:
        f.write("# Converted instance (txt-only robust)\n")
        f.write(f"M={instance['M']}\n")
        f.write(f"C={instance['C']}\n")
        f.write(f"N={instance['N']}\n")
        f.write("costs: " + " ".join(map(str, instance['costs'])) + "\n")
        f.write("jobs:\n")
        for job in instance['jobs']:
            f.write(" ".join(map(str, job)) + "\n")

def main():
    in_dir = Path(INPUT_DIR)
    if not in_dir.exists():
        print(f"[ERR] Нет папки ввода: {INPUT_DIR}")
        return
    for p in sorted(in_dir.iterdir()):
        if not p.is_file() or p.suffix.lower() != ".txt":
            continue
        try:
            inst = parse_txt_instance(p)
            out_path = Path(OUTPUT_DIR) / (p.stem + ".txt")
            write_converted(inst, out_path)
            print(f"[OK] {p.name} -> {out_path.name}  (M={inst['M']}, C={inst['C']}, N={inst['N']}, jobs={len(inst['jobs'])})")
        except RuntimeError as e:
            # уже конвертированный файл
            print(f"[SKIP] {p.name}: {e}")
        except Exception as e:
            print(f"[ERR]  {p.name}: {e}")
    print(f"Готово: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
