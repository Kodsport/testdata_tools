#include <bits/stdc++.h>
#include <random>
using namespace std;

#define rep(i, a, b) for(int i = a; i < (b); ++i)
#define trav(a, x) for(auto& a : x)
#define all(x) x.begin(), x.end()
#define sz(x) (int)(x).size()
typedef long long ll;
typedef pair<int, int> pii;
typedef vector<int> vi;

int main() {
	cin.sync_with_stdio(0); cin.tie(0);
	cin.exceptions(cin.failbit);
	mt19937 rng(2);
	int N;
	cin >> N;
	vector<vi> ed(N);
	rep(i,0,N) {
		int s;
		cin >> s;
		rep(j,0,s) {
			int b;
			cin >> b;
			--b;
			ed[i].push_back(b);
		}
	}

	vi prio(N);
	iota(all(prio), 0);
	int best = INT_MAX;
	rep(it1,0,10) {
		vi onpath[2] = {vi(N), vi(N)};
		vi sqcost(N);
		vi pre(N);
		priority_queue<tuple<int, int, int, int>> q;
		bool first = true;
		rep(it,(it1&1),40) {
			int which = it&1;

			shuffle(all(prio), rng);
			pre.assign(N, -2);
			onpath[which].assign(N, 0);
			sqcost.assign(N, 1);

			int other = !which;
			int start = which == 0 ? 0 : N-1;
			int end = which == 0 ? N-1 : 0;

			int gocost = (it1 & 1) && (it < 20) ? 2 : 1;
			if (first && it1 < 5) {
				rep(i,0,N) sqcost[i] = rand() % 10 + 10;
			}
			first = false;

			q.push(make_tuple(0, -1, -1, start));
			while (!q.empty()) {
				auto [dist, _, pr, x] = q.top();
				q.pop();
				dist = -dist;
				if (pre[x] != -2) continue;
				pre[x] = pr;
				trav(y, ed[x]) {
					int dist2 = dist + (gocost - onpath[other][y]) * sqcost[y];
					q.push(make_tuple(-dist2, prio[x], x, y));
				}
			}

			if (pre[end] == -2) {
				cout << "nej" << endl;
				return 0;
			}

			int at = end;
			while (at != start) {
				onpath[which][at] = 1;
				at = pre[at];
			}
		}

		int res = 0;
		rep(i,1,N) res += onpath[0][i] | onpath[1][i];
		best = min(best, res);
	}

	cout << best << endl;
}
