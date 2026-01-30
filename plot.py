import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random
import matplotlib.cm as cm

# Путь к файлу (захардкожен)
file_path = 'results/combined_results.csv'

# Загрузим данные
data = pd.read_csv(file_path)

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

# Отсортируем тесты по времени выполнения на самом медленном алгоритме
sorted_tests = data.sort_values(by=slowest_algorithm)

# Функция для генерации случайного цвета
def get_random_color():
    return cm.get_cmap('tab10')(random.random())
def get_random_green_color():
    r = random.uniform(0, 0.5)  # случайное значение для красного (в пределах от 0 до 0.5)
    g = random.uniform(0.5, 1)  # зеленая компонента всегда в пределах от 0.5 до 1 (чтобы была зеленой)
    b = random.uniform(0, 0.5)  # случайное значение для синего (в пределах от 0 до 0.5)
    return (r, g, b)
# Функция для построения графика с возможностью логарифмической шкалы
def plot_comparison(log_scale=False):
    plt.figure(figsize=(10, 6))
    
    for i, algorithm in enumerate(algorithms):
        if algorithm == fastest_algorithm:
            color = get_random_green_color()  # Случайный цвет для самого быстрого алгоритма
            linestyle = '-'  # Пунктирная линия для самого быстрого алгоритма
        else:
            color = 'black'  # Черный цвет для остальных алгоритмов
            linestyle = '--'  # Сплошная линия для остальных алгоритмов
        
        plt.plot([i+1 for i in range(len(sorted_tests[algorithm]))], sorted_tests[algorithm], 
                 label=algorithm_names[i], color=color, linestyle=linestyle, linewidth=2)

    # Подписи к осям
    plt.xlabel('Instances', fontsize=12)
    plt.ylabel('CPU time (ms)', fontsize=12)
    plt.xticks(rotation=90, fontsize=12)
    plt.yticks(fontsize=12)
    
    # Легенда с увеличенным шрифтом
    plt.legend(loc='upper left', fontsize=14)

    if log_scale:
        plt.yscale('log')

    plt.tight_layout()
    plt.show()

# Строим график без логарифмической шкалы
plot_comparison(log_scale=False)


