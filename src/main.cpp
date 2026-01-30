#include <iostream>
#include <filesystem>
#include <vector>
#include <string>
#include <fstream>
#include <chrono>
#include <iomanip>
#include <memory>
#include <cstdlib> // для std::system

#include "GeneticSolver.cpp"
#include "HighsLPSolver.h"
#include "ISolver.h"
#include "Instance.h"
#include "DAG.h"
#include "IBuildGraph.h"
#include "BuilderPF.h"
#include "BuilderLC.h"
#include "BuilderLSG.h"
#include "KTNSSolver.h"
#include "HighsFlowSolver.h"
#include "DAG_Solver.h"
#include "HighsMCFSolver.h"

namespace fs = std::filesystem;

// Функция для логирования в консоль и файл одновременно
static void log_message(const std::string& message) {
    // Логируем в консоль
    std::cout << message << std::endl;

    // Логируем в файл
    std::ofstream log_file("log.txt", std::ios_base::app);
    if (log_file.is_open()) {
        log_file << message << std::endl;
    }
}

// Получение всех тестовых файлов
static std::vector<std::string> get_test_files(const std::string& directory) {
    std::vector<std::string> files;
    for (const auto& entry : fs::directory_iterator(directory)) {
        if (entry.is_regular_file() && entry.path().extension() == ".txt") {
            files.push_back(entry.path().string());
        }
    }
    std::sort(files.begin(), files.end());
    return files;
}

// Выполнение пайплайна с логированием в реальном времени и записью результатов после каждого теста
static void run_pipeline(const std::vector<std::string>& test_files,
                         const IBuildGraph& builder,
                         const std::string& csv_path,
                         int num_runs) {  // Добавлен параметр num_runs
    std::ofstream csv(csv_path, std::ios::trunc);  // Очищаем файл при каждом запуске
    csv << "builder,test,N,M,C,total_cost,millis\n";

    for (const auto& test_file : test_files) {
        try {
            TestInstance instance = TestInstance::load_from_file(test_file);

            double total_time = 0.0;
            long long total_cost = 0;

            for (int i = 0; i < num_runs; ++i) {  // Многократные запуски
                auto t0 = std::chrono::high_resolution_clock::now();
                DAG dag = builder.build_from_instance(instance);
                total_cost = dag.compute_max_flow_min_cost().first;
                auto t1 = std::chrono::high_resolution_clock::now();

                total_time += std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count() / 1000.0;
            }

            double avg_time = total_time / num_runs;  // Среднее время

            // Запись результатов после каждого теста
            csv << builder.name << ","
                << fs::path(test_file).filename().string() << ","
                << instance.N << "," << instance.M << "," << instance.C << ","
                << total_cost << ","
                << std::fixed << std::setprecision(3) << avg_time << "\n";

            // Логирование в реальном времени
            log_message("[" + builder.name + "] "
                        + fs::path(test_file).filename().string()
                        + " -> cost=" + std::to_string(total_cost)
                        + ", avg time=" + std::to_string(avg_time) + " ms");

        } catch (const std::exception& e) {
            log_message("[" + builder.name + "] ERROR " + test_file + ": " + e.what());
        }
    }
    log_message("Saved: " + csv_path);
}

// Запуск пайплайна для решателя с результатами после каждого теста
static void run_pipeline_solver(const std::vector<std::string>& test_files,
                                ISolver& solver,
                                const std::string& csv_path,
                                int num_runs) {  // Добавлен параметр num_runs
    std::ofstream csv(csv_path, std::ios::trunc);

    std::string text =  "algorithm,test,N,M,C,total_cost,millis\n";
    csv << text;
    for (const auto& test_file : test_files) {
        try {
            TestInstance instance = TestInstance::load_from_file(test_file);

            double total_time = 0.0;
            long long total_cost = 0;

            for (int i = 0; i < num_runs; ++i) {  // Многократные запуски
                auto t0 = std::chrono::high_resolution_clock::now();
                total_cost = solver.ComputeSolution(instance);
                auto t1 = std::chrono::high_resolution_clock::now();

                total_time += std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count() / 1000.0;
            }

            double avg_time = total_time / num_runs;  // Среднее время

            // Запись результатов после каждого теста
            csv << solver.name << "," << fs::path(test_file).filename().string() << ","
                << instance.N << "," << instance.M << "," << instance.C << total_cost << ","
                << std::fixed << std::setprecision(3) << avg_time << "\n";

            // Логирование в реальном времени
            log_message("[" + solver.name + "] "
                        + fs::path(test_file).filename().string()
                        + " -> cost=" + std::to_string(total_cost)
                        + ", avg time=" + std::to_string(avg_time) + " ms");

        } catch (const std::exception& e) {
            log_message("[" + solver.name + "] ERROR " + test_file + ": " + e.what());
        }
    }

    log_message("Saved: " + csv_path);
}

int main() {
    std::cout <<  std::filesystem::current_path() << " <- my dir" <<std::endl;
    std::ofstream log_file("log.txt", std::ios::trunc);
    log_file.close();
    log_message("=== Tool Switching Problem (PF vs LC) ===");

    const std::string tests_dir   = "tests_txt";
    const std::string results_dir = "results";
    std::filesystem::create_directory(results_dir);

    auto tests = get_test_files(tests_dir);

    PFBuilder pf;
    LSGBuilder cp;
    LCBuilder lc;

    int num_runs = 1;
    double timeLimit = 600; // seconds
    GeneticSolver Mecler(timeLimit * 0.8);
    HighsMCFSolver MCF(timeLimit);

    DAG_Solver LSG = DAG_Solver(cp);
    // Запуск пайплайна
    //run_pipeline_solver(tests, LSG, results_dir + "/resultsLSG.csv", num_runs);
    run_pipeline_solver(tests, Mecler, results_dir + "/resultsMecler.csv", num_runs);
    log_message(""); // Печатаем пустую строку для разделения
    run_pipeline_solver(tests, MCF, results_dir + "/resultsHiGHS_MCF.csv", num_runs);

    return 0;
}
