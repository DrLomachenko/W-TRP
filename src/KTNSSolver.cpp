#include "KTNSSolver.h"

#include <vector>
#include <limits>
#include <numeric>   // std::iota

long long KTNSSolver::ComputeSolution(const TestInstance& inst) {
    const unsigned int numJobs  = static_cast<unsigned int>(inst.N);
    const unsigned int numTools = static_cast<unsigned int>(inst.M);
    const unsigned int maxCap   = static_cast<unsigned int>(inst.C);

    if (numJobs == 0 || numTools == 0 || maxCap == 0) {
        return 0;
    }

    // jobsToolsMatrix[job][tool]
    std::vector<std::vector<unsigned int>> jobsToolsMatrix(
            numJobs, std::vector<unsigned int>(numTools, 0)
    );

    for (unsigned int j = 0; j < numJobs && j < inst.job_requirements.size(); ++j) {
        for (int t1based : inst.job_requirements[j]) {
            if (t1based >= 1 && t1based <= static_cast<int>(numTools)) {
                unsigned int t = static_cast<unsigned int>(t1based - 1);
                jobsToolsMatrix[j][t] = 1;
            }
        }
    }

    // порядок работ: 0..N-1
    std::vector<unsigned int> chromosome(numJobs);
    std::iota(chromosome.begin(), chromosome.end(), 0);

    std::vector<std::vector<unsigned int>> L(
            numTools, std::vector<unsigned int>(numJobs, 0)
    );
    std::vector<bool> used(numTools, false);
    std::vector<unsigned int> W_n(numTools, 0);

    unsigned int switches = 0;

    // 1) заполняем L
    for (int ip = static_cast<int>(numJobs) - 1; ip >= 0; --ip) {
        unsigned int i = static_cast<unsigned int>(ip);
        for (unsigned int j = 0; j < numTools; ++j) {
            if (jobsToolsMatrix[chromosome[i]][j] == 1u) {
                L[j][i] = i;
            } else if (i < numJobs - 1) {
                L[j][i] = L[j][i + 1];
            } else {
                L[j][i] = numJobs;
            }
        }
    }

    // 2) инициализация для n = 0
    unsigned int capacity = 0;
    unsigned int tool     = 0;

    for (unsigned int i = 0; i < numTools; ++i) {
        if (L[i][0] == 0u) {
            W_n[i]  = 1;
            used[i] = true;
            capacity++;
        }
    }

    while (capacity < maxCap) {
        unsigned int bestTool = 0;
        unsigned int bestPos  = numJobs;
        for (unsigned int i = 0; i < numTools; ++i) {
            if (!used[i] && L[i][0] < bestPos) {
                bestPos  = L[i][0];
                bestTool = i;
            }
        }
        used[bestTool] = true;
        W_n[bestTool]  = 1;
        capacity++;
    }

    // 3) основной цикл
    for (unsigned int n = 1; n < numJobs; ++n) {
        for (unsigned int i = 0; i < numTools; ++i) {
            if (W_n[i] == 0u && L[i][n] == n) {
                W_n[i] = 1;
                capacity++;
            }
        }

        while (capacity > maxCap) {
            unsigned int worstTool = 0;
            unsigned int worstPos  = n;
            for (unsigned int i = 0; i < numTools; ++i) {
                if (W_n[i] == 1u && L[i][n] > worstPos) {
                    worstPos  = L[i][n];
                    worstTool = i;
                }
            }
            W_n[worstTool] = 0;
            capacity--;
            switches++;
        }
    }

    // === НОВОЕ: добавляем min(#различных инструментов, maxCap) ===
    std::vector<bool> toolUsed(numTools, false);
    for (unsigned int j = 0; j < numJobs; ++j) {
        if (j >= inst.job_requirements.size()) break;
        for (int t1based : inst.job_requirements[j]) {
            if (t1based >= 1 && t1based <= static_cast<int>(numTools)) {
                unsigned int t = static_cast<unsigned int>(t1based - 1);
                toolUsed[t] = true;
            }
        }
    }

    unsigned int distinctTools = 0;
    for (unsigned int t = 0; t < numTools; ++t) {
        if (toolUsed[t]) {
            distinctTools++;
        }
    }

    unsigned int initialCost = std::min(distinctTools, maxCap);

    return static_cast<long long>(switches) + static_cast<long long>(initialCost);
}

