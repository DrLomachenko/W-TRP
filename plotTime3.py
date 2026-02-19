import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random
import matplotlib.cm as cm

# Путь к файлу (захардкожен)
file_path = 'results/combined_results.csv'
file_path = 'results/ arch/3.csv'#combined_results.csv'

font = 25
# Загрузим данные
data = pd.read_csv(file_path)

# Предполагаем, что имена тестов находятся в столбце 'test'
# Устанавливаем столбец 'test' как индекс
data.set_index('test', inplace=True)

# Идентифицируем все алгоритмы
algorithms = [col for col in data.columns if col.startswith('millis_')]

# Названия алгоритмов для отображения в легенде
algorithm_names = [algorithm.replace('millis_', '') for algorithm in algorithms]

# Рассчитаем среднее время для каждого алгоритма
average_times = data[algorithms].mean()

# Найдем алгоритм с наименьшим средним временем
fastest_algorithm = average_times.idxmin()

# Найдем алгоритм с наибольшим средним временем (для сортировки инстансов)
slowest_algorithm = average_times.idxmax()

# Сортируем тесты по значению в столбце 'N' (предполагается, что такой столбец существует в данных)
sorted_tests = data.sort_values(by='N', ascending=True)

# Функция для построения графика с возможностью логарифмической шкалы
def plot_comparison(log_scale=False, step=5):
    plt.figure(figsize=(10, 6))

    # Будем хранить метки для оси X
    xticks_labels = []
    xticks_positions = []

    # Строим графики для каждого алгоритма
    for i, algorithm in enumerate(algorithms):
        if algorithm == fastest_algorithm:
            color = "#1E90FF"  # Синий для самого быстрого алгоритма
            linestyle = '-'  # Сплошная линия для самого быстрого алгоритма
        else:
            color = '#FF8C00'  # Оранжевый для остальных алгоритмов
            linestyle = '-'  # Сплошная линия для остальных алгоритмов
        
        # Строим график для каждого алгоритма
        plt.plot(range(1, len(sorted_tests) + 1), sorted_tests[algorithm], 
                 label=algorithm_names[i], color=color, linestyle=linestyle, linewidth=2.2)

    # Подписи к осям
    plt.xlabel('Number of jobs', fontsize=font)
    plt.ylabel('CPU time (ms)', fontsize=font)

    # Создаем метки для оси X с шагом
    for i in range(0, len(sorted_tests), step):
        xticks_positions.append(i + 1)
        xticks_labels.append(sorted_tests['N'].iloc[i])

    # Устанавливаем метки на оси X
    plt.xticks(
        ticks=xticks_positions,  # Позиции меток
        labels=xticks_labels,  # Метки для параметра N
        rotation=0, fontsize=font
    )
    
    plt.yticks(fontsize=font)

    # Легенда с увеличенным шрифтом
    plt.legend(loc='upper left', fontsize=font)

    if log_scale:
        plt.yscale('log')

    plt.tight_layout()
    plt.show()

# Строим график без логарифмической шкалы с шагом 5
plot_comparison(log_scale=False, step=70)
