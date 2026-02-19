#pragma once

#include "ISolver.h"
#include "Instance.h"
#include "Highs.h"
#include <string>

class HighsMCFSolver final : public ISolver {
public:
    HighsMCFSolver(){name = "MCF_ILP";}
    long long ComputeSolution(const TestInstance& instance) override;

    void setTimeLimit(double seconds) { time_limit_ = seconds; }

private:
    double time_limit_ = 600.0;  // секунды
};