#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd

# ========= НАСТРОЙКИ =========
INPUT_CSV = "3.csv"
DECIMAL_PRECISION = 3
GROUP_SIZE = 50
# ==============================


def find_millis_columns(df: pd.DataFrame):
    millis_cols = [c for c in df.columns if isinstance(c, str) and c.startswith("millis_")]
    if not millis_cols:
        raise ValueError("Не найдено ни одного столбца вида 'millis_<ALGO>'")
    return millis_cols


def dataframe_to_latex(df: pd.DataFrame, precision: int) -> str:
    return df.to_latex(
        index=False,
        float_format=lambda x: f"{x:.{precision}f}",
        escape=False,
    )


def main():
    df = pd.read_csv(INPUT_CSV)
    df = df.loc[:, ~df.columns.astype(str).str.match(r"^Unnamed")]

    required = {"test", "N"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Отсутствуют столбцы: {missing}. Найдены: {list(df.columns)}")

    millis_cols = find_millis_columns(df)

    # приведение типов
    df["N"] = pd.to_numeric(df["N"], errors="coerce")
    for c in millis_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # сортировка по N и нумерация строк (порядковые номера 1..)
    df_sorted = df.sort_values(by="N", kind="mergesort").reset_index(drop=True)
    df_sorted["_rownum"] = df_sorted.index + 1  # 1-based
    df_sorted["GROUP_ID"] = (df_sorted["_rownum"] - 1) // GROUP_SIZE

    # диапазоны порядковых номеров для каждой группы
    ranges = (
        df_sorted.groupby("GROUP_ID")["_rownum"]
        .agg(first="min", last="max")
        .reset_index()
    )
    ranges["INSTANCE_RANGE"] = ranges.apply(lambda r: f"{int(r['first'])}-{int(r['last'])}", axis=1)
    ranges = ranges[["GROUP_ID", "INSTANCE_RANGE"]]

    # агрегируем среднее время по группам
    grouped = (
        df_sorted.groupby("GROUP_ID", dropna=False)
        .agg(**{col: (col, "mean") for col in millis_cols})
        .reset_index()
        .merge(ranges, on="GROUP_ID", how="left")
        .drop(columns=["GROUP_ID"])
    )

    # округление
    grouped[millis_cols] = grouped[millis_cols].round(DECIMAL_PRECISION)

    # убрать millis_ из названий алгоритмов
    rename_map = {col: col.replace("millis_", "", 1) for col in millis_cols}
    grouped = grouped.rename(columns=rename_map)

    algo_cols = [rename_map[c] for c in millis_cols]

    # порядок колонок: RANGE, затем алгоритмы
    grouped = grouped[["INSTANCE_RANGE", *algo_cols]]

    # сохранение
    base, _ = os.path.splitext(INPUT_CSV)
    csv_out = f"{base}_grouped_by_sorted_index_{GROUP_SIZE}.csv"
    latex_out = f"{base}_grouped_by_sorted_index_{GROUP_SIZE}.tex.txt"

    grouped.to_csv(csv_out, index=False)

    latex_code = dataframe_to_latex(grouped, DECIMAL_PRECISION)
    with open(latex_out, "w", encoding="utf-8") as f:
        f.write(latex_code)

    print("Готово!")
    print("CSV:", csv_out)
    print("LaTeX:", latex_out)


if __name__ == "__main__":
    main()
