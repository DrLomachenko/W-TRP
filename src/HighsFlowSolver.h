#pragma once

#include "ISolver.h"
#include "Instance.h"

// Подключение HiGHS (путь может отличаться в зависимости от установки)
#include <Highs.h>


class HighsFlowSolver : public ISolver {
public:
    std::string name = "FLOW_HiGHS";


    long long ComputeSolution(const TestInstance& instance) override;
};
