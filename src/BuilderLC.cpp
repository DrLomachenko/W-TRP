#include "BuilderLC.h"
#include <vector>
#include <utility>
#include <algorithm>
#include <cassert>
using namespace std;

DAG LCBuilder::build_from_instance(const TestInstance& instance, int K) const {
    DAG dag;

    const int M = instance.M;
    const int N = instance.N;
    const int C = instance.C;
    const auto& jobs = instance.job_requirements;

    vector<pair<int,int>> reqs;
    for (int r = 0; r < N; ++r) {
        vector<int> tools(jobs[r].begin(), jobs[r].end());
        sort(tools.begin(), tools.end());
        for (int t : tools) reqs.emplace_back(r+1, t);
    }
    const int R = (int)reqs.size();

    if (K <= 0) {
        long long mx = 0;
        for (auto v: instance.tool_costs) mx = max(mx, v);
        long long KK = 1LL * R * max(1LL, mx) + 1;
        if (KK > INT_MAX/2) KK = INT_MAX/2;
        K = (int)KK;
    }
    auto c_ins = [&](int tool)->int { return (int)instance.tool_costs[tool-1]; };

    const int S = dag.add_vertex();
    vector<int> BOX(N+1);
    for (int r = 0; r <= N; ++r) BOX[r] = dag.add_vertex();
    vector<int> RIN(R), ROUT(R);
    for (int i = 0; i < R; ++i) { RIN[i] = dag.add_vertex(); ROUT[i] = dag.add_vertex(); }
    const int T = dag.add_vertex();

    dag.set_source(S);
    dag.set_sink(T);

    // S -> BOX_0
    dag.add_edge(S, BOX[0], 0, C);
    // перенос емкости BOX_{r-1} -> BOX_r
    for (int r = 1; r <= N; ++r) dag.add_edge(BOX[r-1], BOX[r], 0, C);

    vector<int> job_of(R), tool_of(R);
    for (int i = 0; i < R; ++i) { job_of[i]=reqs[i].first; tool_of[i]=reqs[i].second; }

    // вставки/сплит/выпуск
    for (int i = 0; i < R; ++i) {
        int r = job_of[i], t = tool_of[i];

        dag.add_edge(BOX[r-1], RIN[i], c_ins(t), 1); // вставка инструмента t перед job r
        dag.add_edge(RIN[i], ROUT[i], -K, 1, false);        // обязательность запроса
        dag.add_edge(ROUT[i], BOX[r], 0, 1);         // «возврат» слота в коробку после r
    }

    // carry-over: rout(i) -> rin(next same tool)
    vector<int> last_pos(M+1, -1);
    for (int i = R-1; i >= 0; --i) {
        int t = tool_of[i];
        int j = last_pos[t];
        if (j != -1) dag.add_edge(ROUT[i], RIN[j], 0, 1);
        last_pos[t] = i;
    }

    // BOX_N -> T
    dag.add_edge(BOX[N], T, 0, C);
    return dag;
}
