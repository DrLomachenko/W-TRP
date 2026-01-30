import os
import shutil
import random
from pathlib import Path
num = 0
# Директории для ввода и вывода
SRC_DIR = r"../raw_data_for_tests/SSP-NPM-II"  # Директория с исходными файлами
OUT_DIR = r"../tests_txt"  # Директория для вывода

def clean_output_directory(out_dir: Path):
    """Полностью удаляет и пересоздаёт выходную директорию"""
    if out_dir.exists():
        shutil.rmtree(out_dir)
        print(f"Удалена существующая директория: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Создана пустая директория: {out_dir}")

def read_instance(path: Path):
    """Чтение входных данных из файла"""
    
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        # Чтение первой строки, содержащей количество машин, работ и инструментов
        m, n, t = map(int, f.readline().split())
        
        # Считываем емкость магазина для каждой машины
        capacity = list(map(int, f.readline().split()))  # Емкость магазина каждой машины

        f.readline()
        f.readline()
        f.readline()
        
        # Считываем матрицу инструментов
        tool_matrix = []
        for _ in range(n):
            tool_matrix.append(list(map(int, f.readline().split())))
        
        return m, n, t, capacity, tool_matrix

def save_task(test_idx, m, n, capacity, tool_costs, jobs_order, tool_matrix, out_dir, machine_idx):
    global num
    """Сохранение задачи для каждой машины в файл"""
    # Формирование имени файла
    test_idx = num
    out_file = out_dir / f"test_{test_idx + 1}_{m}_{n}_{capacity[machine_idx]}.txt"
    num+=1
    with open(out_file, "w", encoding="utf-8") as f:
        # Первая строка: количество инструментов, количество работ и емкость машины
        f.write(f"{m} {n} {capacity[machine_idx]}\n")
        
        # Вторая строка: стоимости инструментов
        f.write("COST ")
        f.write(" ".join(map(str, tool_costs)) + "\n")
        
        # Третья строка: перечень работ
        f.write("JOBS " + str(n) + "\n")
        
        
        # Дальше для каждой работы
        for job_idx in jobs_order:
            # Получаем инструменты, необходимые для этой работы
            required_tools = [i + 1 for i, tool in enumerate(tool_matrix[job_idx]) if tool == 1]
            f.write(f"{len(required_tools)} " + " ".join(map(str, required_tools)) + "\n")

def process_files():
    """Основной процесс работы с файлами"""
    # Очищаем выходную директорию
    out_path = Path(OUT_DIR)
    clean_output_directory(out_path)

    # Считываем все файлы из исходной директории
    src = Path(SRC_DIR)
    files = sorted([p for p in src.iterdir() if p.is_file()])
    
    for test_idx, file_path in enumerate(files):
        try:
            m, n, t, capacity, tool_matrix = read_instance(file_path)
            
            # Просто выводим количество машин, работ, инструментов и емкости магазинов для каждой машины
            """print(f"Файл: {file_path.name}")
            print(f"Количество машин: {m}")
            print(f"Количество работ: {n}")
            print(f"Количество инструментов: {t}")"""
            
            # Для каждой машины создаём задачу
            for machine_idx in range(m):
                # Сначала генерируем случайные стоимости инструментов для текущей машины
                tool_costs = [random.choice([1, 2, 3, 4, 5]) for _ in range(t)]
                
                # Случайным образом перемешиваем работы
                jobs_order = list(range(n))
                random.shuffle(jobs_order)
                
                # Сохраняем задачу в файл с уникальным именем
                save_task(test_idx, t, n, capacity, tool_costs, jobs_order, tool_matrix, out_path, machine_idx)

            #print("-" * 40)
        except Exception as e:
            print(f"Ошибка при обработке файла {file_path.name}: {e}")


if __name__ == "__main__":
    process_files()
