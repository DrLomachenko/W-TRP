#pragma once

#include "IBuildGraph.h"

// Графовая модель с переносом инструментов и финальной вершиной.
// Реализует описанную тобой формулировку.
class LSGBuilder final : public IBuildGraph {
public:
    LSGBuilder(){name ="LSG";}

    // K > 0 — штраф за обязательные рёбра требований.
    // Если K <= 0, он выбирается автоматически.
    DAG build_from_instance(const TestInstance& inst, int K = 0) const override;
};
