import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random
import matplotlib.cm as cm

# Путь к файлу (захардкожен)
file_path = 'results/combined_results.csv'
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

# Функция для генерации случайного цвета
def get_random_color():
    return cm.get_cmap('tab10')(random.random())

def get_random_green_color():
    r = random.uniform(0, 0.5)  # случайное значение для красного (в пределах от 0 до 0.5)
    g = random.uniform(0.5, 1)  # зеленая компонента всегда в пределах от 0.5 до 1 (чтобы была зеленой)
    b = random.uniform(0, 0.5)  # случайное значение для синего (в пределах от 0 до 0.5)
    return (r, g, b)

# Функция для извлечения класса и категории из названия теста
def get_test_class_and_category(test_name):
    # Ищем первую заглавную букву в имени теста (это и будет класс)
    test_class = next((c for c in test_name if c.isupper()), '')
    
    # Если класс 'F', категория - это число сразу после буквы
    if test_class == 'F':
        category = int(test_name[test_name.index(test_class)+1])
        test_class += str(category)
    else:
        # Иначе, категория - это число после заглавной буквы до первого подчеркивания
        category = int(test_name[test_name.index(test_class)+1:].split('_')[0])
    
    return test_class

# Функция для сортировки по классу и категории
def sort_tests_by_class_and_category(test_names):
    return sorted(test_names, key=lambda x: (get_test_class_and_category(x), data.loc[x, fastest_algorithm]))

# Получаем имена тестов (индексы строк, которые теперь являются именами тестов)
test_names = data.index.tolist()

# Упорядочим все тесты по новому порядку (класс, категория)
sorted_test_names = sort_tests_by_class_and_category(test_names)

# Сортируем DataFrame по отсортированным именам тестов
sorted_tests = data.loc[sorted_test_names, algorithms]

# Функция для построения графика с возможностью логарифмической шкалы и вертикальными линиями на концах классов
def plot_comparison(log_scale=False):
    plt.figure(figsize=(10, 6))

    # Будем хранить метки для оси X
    xticks_labels = []
    xticks_positions = []

    prev_class = None  # Для отслеживания предыдущего класса
    group_start = None  # Начало группы
    group_end = None  # Конец группы
    group_positions = []  # Позиции точек в группе
    
    # Добавляем вертикальную линию в начало (перед первым тестом)
    plt.axvline(x=0, color='gray', linestyle=':', linewidth=1)

    for i, algorithm in enumerate(algorithms):
        if algorithm == fastest_algorithm:
            color = "#1E90FF"  # Случайный цвет для самого быстрого алгоритма
            linestyle = '-'  # Пунктирная линия для самого быстрого алгоритма
        else:
            color = '#FF8C00'  # Черный цвет для остальных алгоритмов
            linestyle = '-'  # Сплошная линия для остальных алгоритмов
        
        plt.plot([i+1 for i in range(len(sorted_tests[algorithm]))], sorted_tests[algorithm], 
                 label=algorithm_names[i], color=color, linestyle=linestyle, linewidth=2.2)

        # Подписи к точкам
        for j, test_name in enumerate(sorted_test_names):
            test_class = get_test_class_and_category(test_name)

            # Если класс изменился, сохраняем позиции группы и вычисляем среднее для метки
            if test_class != prev_class:
                if prev_class is not None:
                    # Добавляем вертикальную линию в конце предыдущего класса
                    plt.axvline(x=group_end, color='gray', linestyle=':', linewidth=1)

                    # Добавляем метку для предыдущего класса
                    middle_position = np.mean(group_positions)
                    xticks_labels.append(prev_class)
                    xticks_positions.append(middle_position)

                # Начинаем новую группу
                group_positions = [j + 1]  # Добавляем первую позицию новой группы
            else:
                # Обновляем позицию конца группы
                group_end = j + 1
                group_positions.append(j + 1)

            prev_class = test_class

    # Добавляем вертикальную линию в конце последнего класса
    if group_positions:
        plt.axvline(x=group_end, color='gray', linestyle=':', linewidth=1)

        # Добавляем метку для последней группы
        middle_position = np.mean(group_positions)
        xticks_labels.append(prev_class)
        xticks_positions.append(middle_position)
    
    # Подписи к осям
    plt.xlabel('Instances', fontsize=font)
    plt.ylabel('CPU time (ms)', fontsize=font)
    
    # На оси X будем отображать классы (только для средней точки каждой группы)
    plt.xticks(
        ticks=xticks_positions,  # Позиции меток
        labels=xticks_labels,  # Метки классов
        rotation=0, fontsize=font
    )
    
    plt.yticks(fontsize=font)
    
    # Легенда с увеличенным шрифтом
    plt.legend(loc='upper left', fontsize=font)

    if log_scale:
        plt.yscale('log')

    plt.tight_layout()
    plt.show()

# Строим график без логарифмической шкалы
plot_comparison(log_scale=False)

