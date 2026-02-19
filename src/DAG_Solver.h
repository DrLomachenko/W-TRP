#pragma once

#include <string>

#include "ISolver.h"
#include "IBuildGraph.h"


class DAG_Solver: public ISolver {
public:
    const IBuildGraph& builder_;
    explicit DAG_Solver(const IBuildGraph& builder_, int K = 0)
            : builder_(builder_), K_(K) {}

    std::string name = std::string("FLOW_") + builder_.name;


    long long ComputeSolution(const TestInstance& instance) override;

private:

    int K_ = 0;
};
