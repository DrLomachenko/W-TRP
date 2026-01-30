

#include <string>
#include "ISolver.h"

// Реализация политики KTNS (Keep Tools Needed Soonest)
// для фиксированного порядка заданий (0,1,2,...,N-1).
class KTNSSolver : public ISolver {
public:
    std::string name ="KTNS";


    long long ComputeSolution(const TestInstance& instance) override;
};


