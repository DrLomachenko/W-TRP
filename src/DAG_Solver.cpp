#include "DAG_Solver.h"
#include "DAG.h"

long long DAG_Solver::ComputeSolution(const TestInstance& instance) {
    DAG dag = builder_.build_from_instance(instance, K_);
    return static_cast<long long>(dag.compute_max_flow_min_cost());
}
