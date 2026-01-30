#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merger for tool-switching results (no CLI args).
Собирает ВСЕ CSV из папки 'results', у которых имя начинается с 'result':
  - например: resultsOriginal.csv, resultsOur.csv, resultThird.csv, ...

Логика:
  1) Читаем все такие CSV.
  2) Оставляем только общие тесты (inner join по 'test' по всем файлам).
  3) Для каждого файла:
     - 'total_cost'  -> total_cost_<algo>
     - 'millis'      -> millis_<algo>
     - N,M,C         -> N_<algo>, M_<algo>, C_<algo>
  4) В конце:
     - восстанавливаем общие N,M,C (предпочитая первые встретившиеся)
     - сохраняем:
         results/combined_results.csv
         results/combined_results_grouped.csv (агрегация по N,M,C)

Выходной combined_results.csv:
  test, N, M, C, total_cost_<algo1>, ..., millis_<algo1>, ...

Выходной combined_results_grouped.csv:
  group_id, N, M, C, test_count, avg_total_cost, avg_millis_<algo1>, ...
"""

from pathlib import Path
import pandas as pd

# ---- Hardcoded paths ----
CANDIDATE_ROOTS = [Path(".").resolve(), Path("/mnt/data").resolve()]
OUTPUT_NAME = "combined_results.csv"
OUTPUT_GROUPED_NAME = "combined_results_grouped.csv"

def find_results_dir():
    for root in CANDIDATE_ROOTS:
        res = root / "results"
        if res.exists():
            return res
    # If none exist, create under the first root
    res = CANDIDATE_ROOTS[0] / "results"
    res.mkdir(parents=True, exist_ok=True)
    return res

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def algo_name_from_path(path: Path, idx: int) -> str:
    """
    Получаем имя алгоритма из имени файла.
    Примеры:
      resultsOriginal.csv -> Original
      results_our.csv     -> our
      resultX.csv         -> X
      result.csv          -> algo1 (по индексу)
    """
    stem = path.stem  # Оставляем регистр без изменений
    for prefix in ("results", "result"):
        if stem.lower().startswith(prefix):  # Преобразуем только для поиска
            stem = stem[len(prefix):]
            break
    stem = stem.lstrip("_-")
    if not stem:
        stem = f"algo{idx+1}"
    return stem

def load_one_results(path: Path, algo: str) -> pd.DataFrame:
    """
    Читает один CSV и переименовывает колонки так, чтобы они были
    уникальными для данного алгоритма.
    """
    df = norm_cols(pd.read_csv(path))

    # Переименуем стандартные колонки
    rename_map = {}
    if "total_cost" in df.columns:
        rename_map["total_cost"] = f"total_cost_{algo}"
    if "millis" in df.columns:
        rename_map["millis"] = f"millis_{algo}"  # тут по сути время, единицы — как в исходном CSV
    if "N" in df.columns:
        rename_map["N"] = f"N_{algo}"
    if "M" in df.columns:
        rename_map["M"] = f"M_{algo}"
    if "C" in df.columns:
        rename_map["C"] = f"C_{algo}"

    df = df.rename(columns=rename_map)

    if "test" not in df.columns:
        raise ValueError(f"Файл {path} не содержит колонку 'test'")

    return df

def main():
    results_dir = find_results_dir()
    out_csv = results_dir / OUTPUT_NAME
    out_grouped_csv = results_dir / OUTPUT_GROUPED_NAME

    # --- Находим все CSV, начинающиеся на 'result' ---
    csv_paths = sorted(
        p for p in results_dir.glob("*.csv")
        if p.name.lower().startswith("result")
    )

    if not csv_paths:
        raise FileNotFoundError(
            f"Не найдено ни одного CSV в {results_dir}, имя которого начинается с 'result'"
        )
    if len(csv_paths) == 1:
        raise FileNotFoundError(
            f"Найден только один файл ({csv_paths[0]}). "
            f"Для мерджа нужно минимум два."
        )

    # --- Читаем все файлы и готовим их к мерджу ---
    dfs = []
    algo_names = []
    for idx, path in enumerate(csv_paths):
        algo = algo_name_from_path(path, idx)
        algo_names.append(algo)
        print(f"[load] {path.name} -> algo='{algo}'")
        dfs.append(load_one_results(path, algo))

    # --- Мерджим все по 'test' (inner join по цепочке) ---
    merged = dfs[0]
    for df in dfs[1:]:
        merged = pd.merge(
            merged, df,
            on="test",
            how="inner",
            validate="one_to_one"
        )

    print(f"[merge] rows after intersecting all tests = {len(merged)}")

    # --- Восстанавливаем общие N, M, C из N_<algo>, M_<algo>, C_<algo> ---
    for col in ["N", "M", "C"]:
        # собираем все варианты этого параметра из разных файлов
        algo_cols = [c for c in merged.columns if c.startswith(f"{col}_")]
        if not algo_cols:
            merged[col] = None
            continue

        # берём значение из первого столбца и (опционально) можно проверить,
        # что в остальных совпадает — если хочешь, можно раскомментировать блок ниже
        first_col = algo_cols[0]
        merged[col] = merged[first_col]

        # --- при желании можно проверить консистентность
        #for other_col in algo_cols[1:]:
        #    if not (merged[first_col] == merged[other_col]).all():
        #        print(f"[warn] {col} не совпадает между {first_col} и {other_col}")

        # удаляем все N_*, M_*, C_* колонки
        merged.drop(columns=algo_cols, inplace=True)

    # --- Формируем порядок колонок ---
    # базовые
    base_cols = ["test", "N", "M", "C"]

    # все total_cost_* и millis_* в порядке алгоритмов
    cost_cols = [f"total_cost_{algo}" for algo in algo_names if f"total_cost_{algo}" in merged.columns]
    time_cols = [f"millis_{algo}" for algo in algo_names if f"millis_{algo}" in merged.columns]

    cols = [c for c in base_cols + cost_cols + time_cols if c in merged.columns]
    merged = merged[cols].sort_values("test").reset_index(drop=True)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_csv, index=False)

    print(f"[merge] written: {out_csv}")

    # --- Групповая версия по (N, M, C) ---
    if all(col in merged.columns for col in ["N", "M", "C"]):
        agg_dict = {}
        # усредняем все total_cost_* и millis_*
        for c in merged.columns:
            if c.startswith("total_cost_") or c.startswith("millis_"):
                agg_dict[c] = "mean"
        # считаем количество тестов
        agg_dict["test"] = "count"

        grouped = merged.groupby(["N", "M", "C"]).agg(agg_dict).reset_index()
        grouped = grouped.rename(columns={"test": "test_count"})

        # Вычисляем среднюю стоимость решения по всем алгоритмам
        total_cost_cols = [c for c in grouped.columns if c.startswith("total_cost_")]
        if total_cost_cols:
            grouped["avg_total_cost"] = grouped[total_cost_cols].mean(axis=1)
            # можно удалить индивидуальные cost-колонки
            grouped.drop(columns=total_cost_cols, inplace=True)
        else:
            grouped["avg_total_cost"] = None

        # Переименуем колонки времени в avg_*
        millis_cols = [c for c in grouped.columns if c.startswith("millis_")]
        rename_time = {c: f"avg_{c}" for c in millis_cols}
        grouped = grouped.rename(columns=rename_time)

        # Округляем числовые колонки
        numeric_cols = ["avg_total_cost"] + list(rename_time.values())
        for col in numeric_cols:
            if col in grouped.columns:
                grouped[col] = grouped[col].round(4)

        # Финальный порядок колонок:
        # group_id, N, M, C, test_count, avg_total_cost, avg_millis_<algo1>, ...
        grouped.insert(0, "group_id", range(1, len(grouped) + 1))

        avg_time_cols = [c for c in grouped.columns if c.startswith("avg_millis_")]
        final_cols = ["group_id", "N", "M", "C", "test_count", "avg_total_cost"] + sorted(avg_time_cols)
        final_cols = [c for c in final_cols if c in grouped.columns]
        grouped = grouped[final_cols]

        grouped.to_csv(out_grouped_csv, index=False)
        print(f"[merge] grouped rows={len(grouped)}")
        print(f"[merge] written: {out_grouped_csv}")
    else:
        print("[merge] Warning: Cannot create grouped version - missing N, M, or C columns")

if __name__ == "__main__":
    main()
