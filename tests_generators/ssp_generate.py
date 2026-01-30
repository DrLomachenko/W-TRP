from pathlib import Path
import pandas as pd
import shutil

# =========================
# НАСТРОЙКИ (ХАРДКОД)
# =========================

INPUT_FOLDER = Path("../raw_data_for_tests/ssp")      # папка с .xlsx тестами
OUTPUT_FOLDER = Path("../tests_txt")                  # папка куда сохраняем .txt
DEFAULT_INITIAL_COST = 0                              # если для инструмента нет initial load

# "осмысленные" имена
REQ_SHEET_NAME = "required tool"
INIT_SHEET_NAME = "initial loading"
SETUP_SHEET_NAME = "setup time"

# fallback порядок, если листы называются Sheet1/Sheet2/Sheet3
# (и вообще если "осмысленных" имён нет)
FALLBACK_INIT_IDX = 0   # первый лист
FALLBACK_SETUP_IDX = 1  # второй лист
FALLBACK_REQ_IDX = 2    # третий лист

# =========================
# ОЧИСТКА ВЫХОДНОЙ ПАПКИ
# =========================

if OUTPUT_FOLDER.exists():
    shutil.rmtree(OUTPUT_FOLDER)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


# =========================
# ОПРЕДЕЛЕНИЕ ЛИСТОВ
# =========================

def resolve_sheets(xlsx_path: Path):
    """
    Возвращает имена листов (req_sheet, init_sheet, setup_sheet) для конкретного файла.
    Логика:
      1) если есть "осмысленные" имена — берём их
      2) иначе берём по порядку листов: 0=init, 1=setup, 2=req
    """
    xl = pd.ExcelFile(xlsx_path)
    names = xl.sheet_names

    lower_map = {n.lower(): n for n in names}

    have_req = REQ_SHEET_NAME in lower_map
    have_init = INIT_SHEET_NAME in lower_map
    have_setup = SETUP_SHEET_NAME in lower_map

    if have_req and have_init and have_setup:
        req = lower_map[REQ_SHEET_NAME]
        init = lower_map[INIT_SHEET_NAME]
        setup = lower_map[SETUP_SHEET_NAME]
        return req, init, setup

    # fallback по индексам
    if len(names) < 3:
        raise ValueError(f"{xlsx_path.name}: ожидаю минимум 3 листа, а тут {len(names)}: {names}")

    init = names[FALLBACK_INIT_IDX]
    setup = names[FALLBACK_SETUP_IDX]
    req = names[FALLBACK_REQ_IDX]
    return req, init, setup


# =========================
# ПАРСИНГ
# =========================

def read_required_tools(xlsx_path: Path, req_sheet: str):
    df = pd.read_excel(xlsx_path, sheet_name=req_sheet, header=None)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df = df.apply(pd.to_numeric, errors="coerce")

    C = df.shape[0]
    n = df.shape[1]

    jobs = []
    max_tool = 0

    for j in range(n):
        tools = []
        for v in df.iloc[:, j].tolist():
            if pd.isna(v):
                continue
            v = int(v)
            if v != 0:
                tools.append(v)
                if v > max_tool:
                    max_tool = v
        jobs.append(tools)

    return jobs, n, C, max_tool


def read_initial_costs(xlsx_path: Path, init_sheet: str, m: int):
    df = pd.read_excel(xlsx_path, sheet_name=init_sheet, header=None)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    # один столбец: i-я строка = s0_i
    df = df.apply(pd.to_numeric, errors="coerce").dropna()

    values = [int(v) for v in df.iloc[:, 0].tolist()]

    if len(values) < m:
        values += [DEFAULT_INITIAL_COST] * (m - len(values))
    else:
        values = values[:m]

    return values


def infer_m_from_setup(xlsx_path: Path, setup_sheet: str, current_max: int):
    try:
        df = pd.read_excel(xlsx_path, sheet_name=setup_sheet, header=None)
        df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
        r, c = df.shape
        m_setup = min(r, c)
        return max(current_max, m_setup)
    except Exception:
        return current_max


# =========================
# ОСНОВНОЙ ЦИКЛ
# =========================

for xlsx_file in sorted(INPUT_FOLDER.glob("*.xlsx")):
    req_sheet, init_sheet, setup_sheet = resolve_sheets(xlsx_file)

    jobs, n, C, max_tool = read_required_tools(xlsx_file, req_sheet)
    m = infer_m_from_setup(xlsx_file, setup_sheet, max_tool)
    initial_costs = read_initial_costs(xlsx_file, init_sheet, m)

    lines = []
    lines.append(f"{m} {n} {C}")
    lines.append("COST " + " ".join(map(str, initial_costs)))
    lines.append(f"JOBS {n}") 
    for tools in jobs:
        line = str(len(tools))
        if tools:
            line += " " + " ".join(map(str, tools))
        lines.append(line)

    out_path = OUTPUT_FOLDER / (xlsx_file.stem + ".txt")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK -> {out_path.name}   (req={req_sheet}, init={init_sheet}, setup={setup_sheet})")
