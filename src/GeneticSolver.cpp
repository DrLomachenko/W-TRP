#include "GeneticSolver.h"

#include "Mecler/Population.h"
#include "Mecler/Parameters.h"
#include "Mecler/Genetic.h"

#define min2(a, b) ((a < b) ? a : b)



long long GeneticSolver::ComputeSolution(const TestInstance& instance) {
    double bestCost;
    double averageCost, averageTime;

    unsigned int runs = 1;
    Parameters *parameters;
    Population *population;
    clock_t nb_ticks_allowed;
    double cost, totalAvgCost = 0, totalBestCost = 0;
    double totalTime = 0;
    // Конвертируем TestInstance в параметры, необходимые для генетического алгоритма
    parameters = createParametersFromInstance(instance);


    parameters->setAuxiliaryParams();



    // Start population
    population = new Population(parameters);


    // Run genetic algorithm
    const clock_t startTime = clock();

    Genetic solver(parameters, population, timeLimit, false);
    solver.evolve(min2(parameters->numJobs * 20, 1000));
    //std::cout << parameters->numJobs << "," << parameters->numTools << "," << parameters->maxCapacity << "," << cost << ","  << totalTime << endl;
    cost = population->getBestIndividual()->solutionCost.evaluation;
    totalTime = (float(clock() - startTime) / CLOCKS_PER_SEC);





    // Освобождаем память
    delete population;
    delete parameters;

    return cost;
}
Parameters* GeneticSolver::createParametersFromInstance(const TestInstance& instance) {
    // Используем конструктор Parameters для инициализации параметров
    Parameters* parameters = new Parameters(
            0,  // seed, пусть будет 0, если не используется
            "", // instancesPaths, можно оставить пустым
            "", // instancesNames, можно оставить пустым
            "", // solutionPath, можно оставить пустым
            20, // populationSize
            40, // maxPopulationSize
            10, // numberElite
            3,  // numberCloseIndividuals
            1000 // maxDiversify
    );

    // Заполняем параметры из TestInstance
    parameters->numJobs = instance.N;
    parameters->numTools = instance.M;
    parameters->maxCapacity = instance.C;



    // Преобразуем job_requirements в формат, подходящий для алгоритма
    parameters->jobsToolsMatrix.clear();
    parameters->toolsCosts = instance.tool_costs;
    for (const auto& reqs : instance.job_requirements) {

        std::vector<unsigned int> job_tools(instance.M, 0);
        for (int tool : reqs) {
            //std::cout << tool << ",: ";
            job_tools[tool-1] = 1;  // Устанавливаем 1 для требуемых инструментов
        }
        parameters->jobsToolsMatrix.push_back(job_tools);
        //std::cout << std::endl;
    }
    //std::cout << parameters->jobsToolsMatrix[0].size();

    return parameters;
}