// original.cpp
// PF1995-style: cp(i) -> req(j) для всех будущих работ j; стоимость берём из D[t_i-1][t_j-1].
// CSV: test, N, M, C, total_cost, millis
// Читает ТЕКСТОВЫЙ формат:
//   M N C
//   COST c1..cM   ИЛИ   MATRIX \n M строк по M чисел
//   JOBS N
//   k  t1 ... tk   (N строк)

#include <iostream>
#include <vector>
#include <string>
#include <deque>
#include <algorithm>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <tuple>
#include <unordered_map>
#include <chrono>
#include <dirent.h>
#include <sys/stat.h>

using namespace std;

struct Instance {
    int M=0, N=0, C=0;
    vector<vector<int> > jobs;           // 1..M
    vector<vector<long long> > D;        // MxM, если MATRIX
    vector<long long> c;                 // если COST
};

static inline bool is_comment(const string& s){
    for(size_t i=0;i<s.size();++i){
        unsigned char ch=(unsigned char)s[i];
        if(!isspace(ch)) return s[i]=='#';
    }
    return true; // пустая строка — пропускаем
}
static vector<string> split_tokens(const string& s){
    vector<string> r; string tok; istringstream in(s);
    while(in >> tok) r.push_back(tok);
    return r;
}

static Instance read_instance_text(istream& in){
    Instance inst; string line;
    // получить следующую «значимую» строку (не комментарий/пустую)
    struct NL {
        static bool next_line(istream& in, string& out){
            while (std::getline(in, out)){
                if(!is_comment(out)) return true;
            }
            return false;
        }
    };

    // M N C
    if(!NL::next_line(in, line)) throw runtime_error("Unexpected EOF before M N C");
    {
        vector<string> tok = split_tokens(line);
        if(tok.size()!=3) throw runtime_error("Expected: M N C");
        inst.M = atoi(tok[0].c_str());
        inst.N = atoi(tok[1].c_str());
        inst.C = atoi(tok[2].c_str());
    }
    // COST ...  ИЛИ  MATRIX + M строк
    if(!NL::next_line(in, line)) throw runtime_error("Unexpected EOF before COST/MATRIX");
    {
        vector<string> tok = split_tokens(line);
        if(tok.empty()) throw runtime_error("Empty line where COST/MATRIX expected");
        if(tok[0]=="COST"){
            if((int)tok.size()!=1+inst.M) throw runtime_error("COST line must have M values");
            inst.c.assign(inst.M, 0);
            for(int j=0;j<inst.M;++j) inst.c[j] = atoll(tok[1+j].c_str());
        }else if(tok[0]=="MATRIX"){
            inst.D.assign(inst.M, vector<long long>(inst.M, 0));
            for(int i=0;i<inst.M;++i){
                if(!NL::next_line(in, line)) throw runtime_error("Unexpected EOF in MATRIX block");
                vector<string> row = split_tokens(line);
                if((int)row.size()!=inst.M) throw runtime_error("MATRIX row length mismatch");
                for(int j=0;j<inst.M;++j) inst.D[i][j] = atoll(row[j].c_str());
            }
        }else{
            throw runtime_error("Expected 'COST' or 'MATRIX'");
        }
    }
    // JOBS N
    if(!NL::next_line(in, line)) throw runtime_error("Unexpected EOF before JOBS");
    {
        vector<string> tok = split_tokens(line);
        if(tok.size()!=2 || tok[0]!="JOBS") throw runtime_error("Expected 'JOBS N'");
        int n2 = atoi(tok[1].c_str());
        if(n2 != inst.N) throw runtime_error("JOBS N mismatch");
    }
    inst.jobs.clear();
    inst.jobs.reserve(inst.N);
    for(int r=0;r<inst.N;++r){
        if(!NL::next_line(in, line)) throw runtime_error("Unexpected EOF reading job line");
        vector<string> tok = split_tokens(line);
        if(tok.empty()) throw runtime_error("Empty job line");
        int k = atoi(tok[0].c_str());
        if((int)tok.size()!=1+k) throw runtime_error("Job line wrong token count");
        vector<int> tools; tools.reserve(k);
        for(int i=0;i<k;++i){
            int t = atoi(tok[1+i].c_str());
            if(t<1 || t>inst.M) throw runtime_error("Tool id out of range");
            tools.push_back(t);
        }
        sort(tools.begin(), tools.end());
        tools.erase(unique(tools.begin(), tools.end()), tools.end());
        inst.jobs.push_back(tools);
    }
    return inst;
}

// --------- Min-Cost Max-Flow (SPFA) ----------
struct Edge {
    int to, rev, cap;
    long long cost;
    Edge(int _to,int _rev,int _cap,long long _cost):to(_to),rev(_rev),cap(_cap),cost(_cost){}
};
struct MinCostMaxFlow {
    int n;
    vector<vector<Edge> > g;
    MinCostMaxFlow(int n):n(n),g(n){}
    int add_edge(int u,int v,int cap,long long cost){
        Edge a(v,(int)g[v].size(),cap,cost);
        Edge b(u,(int)g[u].size(),0,-cost);
        g[u].push_back(a); g[v].push_back(b);
        return (int)g[u].size()-1;
    }
    pair<int,long long> min_cost_flow(int s,int t,int maxf){
        const long long INF = (long long)1e18;
        int flow=0; long long cost=0;
        vector<long long> dist(n);
        vector<char> inq(n, 0);
        vector<int> pv_v(n), pv_e(n);
        while(flow<maxf){
            for(int i=0;i<n;++i){ dist[i]=INF; inq[i]=0; }
            dist[s]=0;
            deque<int> dq; dq.push_back(s); inq[s]=1;
            while(!dq.empty()){
                int u=dq.front(); dq.pop_front(); inq[u]=0;
                for(int i=0;i<(int)g[u].size();++i){
                    Edge &e=g[u][i];
                    if(e.cap>0 && dist[e.to] > dist[u]+e.cost){
                        dist[e.to] = dist[u]+e.cost;
                        pv_v[e.to]=u; pv_e[e.to]=i;
                        if(!inq[e.to]){
                            inq[e.to]=1;
                            if(!dq.empty() && dist[e.to] < dist[dq.front()]) dq.push_front(e.to);
                            else dq.push_back(e.to);
                        }
                    }
                }
            }
            if(dist[t]==INF) break;
            int addf = maxf - flow;
            for(int v=t; v!=s; v=pv_v[v]) addf = min(addf, g[pv_v[v]][pv_e[v]].cap);
            for(int v=t; v!=s; v=pv_v[v]){
                Edge &e = g[pv_v[v]][pv_e[v]];
                e.cap -= addf; g[v][e.rev].cap += addf;
            }
            flow += addf; cost += dist[t]*addf;
        }
        return pair<int,long long>(flow, cost);
    }
};

static vector<vector<long long> > build_cost_matrix(const Instance& inst){
    int M = inst.M;
    if(!inst.D.empty()){
        if((int)inst.D.size()!=M) throw runtime_error("D size mismatch");
        for(size_t i=0;i<inst.D.size();++i)
            if((int)inst.D[i].size()!=M) throw runtime_error("D row size mismatch");
        return inst.D;
    }
    if(!inst.c.empty()){
        if((int)inst.c.size()!=M) throw runtime_error("c size mismatch");
        vector<vector<long long> > D(M, vector<long long>(M, 0));
        for(int i=0;i<M;++i) for(int j=0;j<M;++j) D[i][j] = (i==j?0:inst.c[j]);
        return D;
    }
    vector<vector<long long> > D(M, vector<long long>(M, 0));
    for(int i=0;i<M;++i) for(int j=0;j<M;++j) D[i][j] = (i==j?0:1);
    return D;
}

static pair<long long,int> solve_pf1995(const Instance& inst, int K){
    int M = inst.M, N = inst.N, C = inst.C;
    const vector<vector<int> >& jobs = inst.jobs;
    vector<vector<long long> > D = build_cost_matrix(inst);

    vector<pair<int,int> > reqs;
    for(int r=1; r<=N; ++r)
        for(size_t it=0; it<jobs[r-1].size(); ++it)
            reqs.push_back(pair<int,int>(r, jobs[r-1][it]));
    int R = (int)reqs.size();

    int s = 0;
    int slot_base = 1;
    int req_base  = slot_base + C;
    int cp_base   = req_base + R;
    int tnode     = cp_base + R;
    MinCostMaxFlow mcmf(tnode+1);

    // helpers
    // v_req(i), v_cp(i)
    // s -> slots
    for(int k=0;k<C;++k) mcmf.add_edge(s, slot_base+k, 1, 0);
    // slots -> every req
    for(int k=0;k<C;++k){
        int u = slot_base + k;
        for(int i=0;i<R;++i) mcmf.add_edge(u, req_base+i, 1, 0);
    }
    // req -> cp  (-K)
    for(int i=0;i<R;++i) mcmf.add_edge(req_base+i, cp_base+i, 1, -K);
    // cp -> sink
    for(int i=0;i<R;++i) mcmf.add_edge(cp_base+i, tnode, 1, 0);

    // cp(i) -> req(j) для всех будущих
    vector<int> job_of(R), tool_of(R);
    for(int i=0;i<R;++i){ job_of[i]=reqs[i].first; tool_of[i]=reqs[i].second; }
    for(int i=0;i<R;++i){
        int ji=job_of[i], ti=tool_of[i];
        int u = cp_base+i;
        for(int j=i+1;j<R;++j){
            int jj=job_of[j]; if(jj<=ji) continue;
            int tj=tool_of[j];
            mcmf.add_edge(u, req_base+j, 1, D[ti-1][tj-1]);
        }
    }

    pair<int,long long> res = mcmf.min_cost_flow(s, tnode, C);
    if(res.first != C) throw runtime_error("Could not push flow C");

    long long total_cost=0; int num_rep=0;
    for(int i=0;i<R;++i){
        int u = cp_base+i;
        int ti = tool_of[i], ji=job_of[i];
        for(size_t ie=0; ie<mcmf.g[u].size(); ++ie){
            const Edge &e = mcmf.g[u][ie];
            int v = e.to;
            if(!(req_base <= v && v < req_base+R)) continue;
            if(mcmf.g[v][e.rev].cap > 0){
                int j = v - req_base;
                int tj = tool_of[j], jj=job_of[j];
                if(jj<=ji) continue;
                if(ti != tj){
                    num_rep++;
                    total_cost += D[ti-1][tj-1];
                }
            }
        }
    }
    return pair<long long,int>(total_cost, num_rep);
}

static vector<string> list_text_files(const string& dir){
    vector<string> files;
    DIR* d = opendir(dir.c_str());
    if(!d) return files;
    dirent* ent;
    while((ent = readdir(d))){
        string name = ent->d_name;
        if(name=="." || name=="..") continue;
        string path = dir + "/" + name;
        struct stat stbuf; if(stat(path.c_str(), &stbuf)!=0) continue;
        if(S_ISREG(stbuf.st_mode)){
            if(path.size()>=4 && path.substr(path.size()-4)==".txt")
                files.push_back(path);
        }
    }
    closedir(d);
    sort(files.begin(), files.end());
    return files;
}

int main(int argc, char** argv){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string tests="tests_txt";
    string csvout="results/results_for_original.csv";
    int K=10000;

    for(int i=1;i<argc;++i){
        string a=argv[i];
        if(a=="--tests" && i+1<argc) tests=argv[++i];
        else if(a=="--csv" && i+1<argc) csvout=argv[++i];
        else if(a=="--K" && i+1<argc) K=atoi(argv[++i]);
    }

    vector<string> files = list_text_files(tests);
    ofstream fout(csvout.c_str());
    fout << "test,N,M,C,total_cost,millis\n";

    for(size_t fi=0; fi<files.size(); ++fi){
        const string& path = files[fi];
        ifstream f(path.c_str());
        Instance inst = read_instance_text(f);

        auto t0 = chrono::high_resolution_clock::now();
        pair<long long,int> ans = solve_pf1995(inst, K);
        auto t1 = chrono::high_resolution_clock::now();
        double ms = chrono::duration<double, std::milli>(t1-t0).count();

        // имя файла
        size_t slash = path.find_last_of("/\\");
        string fname = (slash==string::npos)? path : path.substr(slash+1);

        // CSV: test, N, M, C, total_cost, millis
        fout << fname << "," << inst.N << "," << inst.M << "," << inst.C << ","
             << ans.first << "," << fixed << setprecision(3) << ms << "\n";
    }
    cerr << "Wrote " << csvout << " with " << files.size() << " rows.\n";
    return 0;
}
