#include "validate.h"

// Example validator for the task:
// Given an undirected graph, is there an even-length cycle?
// If so, find one

#include <bits/stdc++.h>
using namespace std;

#define rep(i, a, b) for(int i = a; i < (b); ++i)
#define all(x) begin(x), end(x)
#define sz(x) (int)(x).size()
using ll = long long;
using pii = pair<int, int>;
using vi = vector<int>;

int main(int argc, char **argv) {
    init_io(argc, argv);

    int n, m;
    judge_in >> n >> m;

    set<pii> edges;
    rep(i,0,m) {
        int a, b;
        judge_in >> a >> b;
        edges.emplace(a,b);
        edges.emplace(b,a);
    }

    auto check = [&](istream& sol, feedback_function feedback) {
        string ans;
        if (!(sol >> ans)) feedback("Expected more output");
        for (char& c : ans) c = (char)tolower(c);
        if (ans != "no" && ans != "yes") {
            feedback("Answer is not {yes|no}");
        }

        if (ans == "no") {
            string trailing;
            if (sol >> trailing) feedback("Trailing output");
            return false;
        }

        int k;
        if (!(sol >> k)) feedback("Expected more output");
        if (k < 4 || k > n) feedback("Cycle length is out of range");
        if (k % 2 != 0) feedback("Cycle length is odd");

        vi seen(n+1,0);
        vi c;
        rep(i,0,k) {
            int x;
            if(!(sol >> x)) feedback("Expected more output");
            if(x < 1 || x > n) feedback("Vertex index is out of range");
            if(seen[x]) feedback("Duplicate vertex in cycle");
            c.emplace_back(x);
            seen[x] = 1;
        }

        rep(i,0,k) if (!edges.count(pii(c[i], c[(i+1)%k]))) {
            feedback("Edge used in cycle does not exist");
        }

        string trailing;
        if(sol >> trailing) feedback("Trailing output");
        return true;
    };

    bool judge_found_sol = check(judge_ans, judge_error);
    bool author_found_sol = check(author_out, wrong_answer);

    if(!judge_found_sol && author_found_sol) {
        judge_error("NO! Solution found a cycle, but judge says none exists");
    }

    if(judge_found_sol && !author_found_sol) {
        wrong_answer("Cycle exists, but solution did not find it");
    }

    accept();
}
