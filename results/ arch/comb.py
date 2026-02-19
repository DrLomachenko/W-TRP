#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import pandas as pd

# ========= НАСТРОЙКИ =========
INPUT_CSV = "3.csv"
DECIMAL_PRECISION = 3
# ==============================


def find_millis_columns(df: pd.DataFrame):
    millis_cols = [c for c in df.columns if isinstance(c, str) and c.startswith("millis_")]
    if not millis_cols:
        raise ValueError("Не найдено ни одного столбца вида 'millis_<ALGO>'")
    return millis_cols


def extract_class_letter(test_name: str) -> str:
    """Первая заглавная буква"""
    if not isinstance(test_name, str):
        return ""
    return next((c for c in test_name if c.isupper()), "")


def extract_tabel_after_first_underscore(test_name: str) -> int:
    """
    tabel = цифра сразу после первого '_' .
    Если '_' нет или после него не цифра -> 0.
    """
    if not isinstance(test_name, str):
        return 0

    pos = test_name.find("_")
    if pos == -1 or pos + 1 >= len(test_name):
        return 0

    ch = test_name[pos + 1]
    return int(ch) if ch.isdigit() else 0


def extract_F_category(test_name: str) -> int | None:
    """
    Категория для F — цифра сразу после F (одна цифра).
    """
    if not isinstance(test_name, str):
        return None
    try:
        idx = test_name.index("F")
        if idx + 1 < len(test_name) and test_name[idx + 1].isdigit():
            return int(test_name[idx + 1])
    except ValueError:
        pass
    return None


def build_dataset_name(test_name: str) -> str:
    cls = extract_class_letter(test_name)
    tabel = extract_tabel_after_first_underscore(test_name)
    if not cls:
        return ""

    if cls == "F":
        cat = extract_F_category(test_name)
        t = tabel if tabel > 0 else 1
        cat = str(cat) + "." + str(t)
        return f"F{cat}" if cat is not None else "F"

    tabel += 1
    return f"{cls}{tabel}"


def sort_key(name: str):
    """
    Твоя текущая сортировка (оставляю как есть).
    """
    m = re.fullmatch(r"([A-Z]+)(\d+)", str(name))
    if m:
        return (m.group(1), int(m.group(2)))
    return (str(name), -1)


def dataframe_to_latex(df: pd.DataFrame, precision: int) -> str:
    return df.to_latex(
        index=False,
        float_format=lambda x: f"{x:.{precision}f}",
        escape=False,
    )


def main():
    df = pd.read_csv(INPUT_CSV)
    df = df.loc[:, ~df.columns.astype(str).str.match(r"^Unnamed")]

    required = {"test", "N", "M", "C"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Отсутствуют столбцы: {missing}. Найдены: {list(df.columns)}")

    millis_cols = find_millis_columns(df)

    for c in millis_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # ключ группировки
    df["DATASET_NAME"] = df["test"].apply(build_dataset_name)

    grouped = (
        df.groupby("DATASET_NAME", dropna=False)
          .agg(
              N=("N", "first"),
              M=("M", "first"),
              C=("C", "first"),
              **{col: (col, "mean") for col in millis_cols},
          )
          .reset_index()
    )

    # округление времени
    grouped[millis_cols] = grouped[millis_cols].round(DECIMAL_PRECISION)

    # убрать millis_
    rename_map = {col: col.replace("millis_", "", 1) for col in millis_cols}
    grouped = grouped.rename(columns=rename_map)

    # сортировка
    grouped = grouped.sort_values(
        by="DATASET_NAME",
        key=lambda col: col.map(sort_key)
    )

    # порядок колонок
    algo_cols = [rename_map[c] for c in millis_cols]
    grouped = grouped[["DATASET_NAME", "N", "M", "C", *algo_cols]]

    # ---------- сохранение CSV (общий) ----------
    base, _ = os.path.splitext(INPUT_CSV)
    csv_out = f"{base}_grouped_by_rule.csv"
    grouped.to_csv(csv_out, index=False)

    # ---------- разбиение на две LaTeX-таблицы ----------
    grouped_f = grouped[grouped["DATASET_NAME"].astype(str).str.startswith("F")].copy()
    grouped_other = grouped[~grouped["DATASET_NAME"].astype(str).str.startswith("F")].copy()

    latex_out_f = f"{base}_grouped_F.tex.txt"
    latex_out_other = f"{base}_grouped_other.tex.txt"

    with open(latex_out_f, "w", encoding="utf-8") as f:
        f.write(dataframe_to_latex(grouped_f, DECIMAL_PRECISION))

    with open(latex_out_other, "w", encoding="utf-8") as f:
        f.write(dataframe_to_latex(grouped_other, DECIMAL_PRECISION))

    print("Готово!")
    print("CSV:", csv_out)
    print("LaTeX (F):", latex_out_f)
    print("LaTeX (other):", latex_out_other)


if __name__ == "__main__":
    main()
