#pragma once
#include "IBuildGraph.h"

class LCBuilder final : public IBuildGraph {
public:
    DAG build_from_instance(const TestInstance& instance, int K = 0) const override;
    const std::string name()  { return "LC"; }
};
