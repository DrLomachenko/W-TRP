#include "HighsFlowSolver.h"

#include <vector>
#include <stdexcept>
#include <cmath>    // std::llround
#include <limits>
#include <iostream>

struct Interval {
    int tool;      // 0-based tool index
    int startJob;  // 0-based job index (end of previous block)
    int endJob;    // 0-based job index (start of next block)
};

long long HighsFlowSolver::ComputeSolution(const TestInstance& inst) {
    const int numJobs  = inst.N;
    const int numTools = inst.M;
    const int C        = inst.C;

    if (numJobs <= 0 || numTools <= 0 || C <= 0) {
        throw std::invalid_argument("Invalid input parameters.");
    }

    const auto& T    = inst.job_requirements; // vector< set<int> >
    const auto& cost = inst.tool_costs;       // size M, indices 0..M-1

    // === 1. Считаем n_t и occ[t] ТАК ЖЕ, как в BuilderCP ===
    std::vector<int> n(numTools, 0);                   // 0-based по t
    std::vector<std::vector<int>> occ(numTools);       // occ[t] = список работ (0-based), где нужен t

    for (int j = 0; j < numJobs; ++j) {
        for (int t1based : T[j]) {
            int t = t1based - 1; // 0-based индекс инструмента

            occ[t].push_back(j);

            // считаем только "первое появление" блока:
            if (j == 0 || !T[j - 1].count(t1based)) {
                n[t]++;
            }
        }
    }

    // Ctot = sum_t c_t * n_t
    long long Ctot = 0;
    for (int t = 0; t < numTools; ++t) {
        Ctot += 1LL * cost[t] * n[t];
    }

    // === 2. Строим интервалы ===
    std::vector<Interval> intervals;
    intervals.reserve(numJobs * numTools);

    for (int t = 0; t < numTools; ++t) {
        const auto& v = occ[t];
        if (v.empty()) continue;

        for (size_t k = 1; k < v.size(); ++k) {
            int prevIdx = v[k - 1];
            int curIdx  = v[k];

            if (curIdx == prevIdx + 1) continue; // consecutive jobs, no gap

            Interval e;
            e.tool     = t;
            e.startJob = prevIdx;
            e.endJob   = curIdx;
            intervals.push_back(e);
        }
    }

    const int numVars = static_cast<int>(intervals.size());
    if (numVars == 0) {
        return Ctot; // No gaps, no savings
    }

    // === 3. Строим LP для HiGHS ===
    std::vector<double> col_cost(numVars);
    std::vector<double> col_lower(numVars, 0.0);
    std::vector<double> col_upper(numVars, 1.0);

    for (int e = 0; e < numVars; ++e) {
        int t = intervals[e].tool;
        col_cost[e] = static_cast<double>(cost[t]);
    }

    // Ограничения по работам
    const int numRows = numJobs;
    std::vector<double> row_lower(numRows);
    std::vector<double> row_upper(numRows);

    for (int i = 0; i < numJobs; ++i) {
        int freeCap = C - static_cast<int>(T[i].size());
        if (freeCap < 0) {
            throw std::runtime_error("HighsLPSolver: |T_i| > C, instance infeasible");
        }
        row_lower[i] = -std::numeric_limits<double>::infinity();
        row_upper[i] = static_cast<double>(freeCap);
    }

    // Матрица A
    std::vector<std::vector<int>> col_rows(numVars);
    for (int e = 0; e < numVars; ++e) {
        const Interval& in = intervals[e];
        for (int i = in.startJob + 1; i < in.endJob; ++i) {
            col_rows[e].push_back(i);
        }
    }

    std::vector<HighsInt> astart(numVars + 1);
    std::vector<HighsInt> aindex;
    std::vector<double>   avalue;

    aindex.reserve(numVars * 4);
    avalue.reserve(numVars * 4);

    HighsInt nnz = 0;
    for (int e = 0; e < numVars; ++e) {
        astart[e] = nnz;
        for (int row : col_rows[e]) {
            aindex.push_back(row);
            avalue.push_back(1.0);
            ++nnz;
        }
    }
    astart[numVars] = nnz;

    // === 4. Отдаём модель в HiGHS ===
    Highs highs;
    highs.setOptionValue("output_flag", false);
    highs.setOptionValue("log_to_console", false);

    HighsLp lp;
    lp.num_col_   = numVars;
    lp.num_row_   = numRows;
    lp.col_cost_  = col_cost;
    lp.col_lower_ = col_lower;
    lp.col_upper_ = col_upper;
    lp.row_lower_ = row_lower;
    lp.row_upper_ = row_upper;

    lp.a_matrix_.start_ = astart;
    lp.a_matrix_.index_ = aindex;
    lp.a_matrix_.value_ = avalue;

    lp.sense_ = ObjSense::kMaximize; // Максимизация экономии

    HighsStatus status = highs.passModel(lp);
    if (status != HighsStatus::kOk) {
        throw std::runtime_error("HiGHS: passModel failed");
    }

    status = highs.run();
    if (status != HighsStatus::kOk) {
        throw std::runtime_error("HiGHS: solve failed");
    }

    const HighsModelStatus model_status = highs.getModelStatus();
    if (model_status != HighsModelStatus::kOptimal) {
        throw std::runtime_error("HiGHS: model status is not optimal");
    }

    const double obj = highs.getObjectiveValue(); // maxSavings (double)
    long long maxSavings = std::llround(obj);
    long long totalCost  = Ctot - maxSavings;   // Общая стоимость = Ctot - максимальная экономия

    return totalCost;
}
