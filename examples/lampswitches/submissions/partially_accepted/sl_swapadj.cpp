#include <bits/stdc++.h>
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
	int N;
	cin >> N;
	vector<vi> ed(N), ed2(N);
	rep(i,0,N) {
		int s;
		cin >> s;
		rep(j,0,s) {
			int b;
			cin >> b;
			--b;
			ed[i].push_back(b);
			ed2[b].push_back(i);
		}
	}

	const int inf = 1000000;

	vector<vi> dists(N);
	vi seen(N);
	priority_queue<pii> q;
	rep(start,0,N) {
		dists[start].assign(N, inf);
		seen.assign(N, 0);

		q.push(pii(0, start));
		while (!q.empty()) {
			auto pa = q.top();
			q.pop();
			int dist = -pa.first;
			int x = pa.second;
			if (seen[x]++) continue;
			dists[start][x] = dist;
			trav(y, ed[x]) {
				int dist2 = dist + 1;
				q.push(pii(-dist2, y));
			}
		}
	}

	if (dists[0][N-1] == inf || dists[N-1][0] == inf) {
		cout << "nej" << endl;
		return 0;
	}

	vector<vi> seen2(N, vi(N));
	vector<vector<pii>> qs(N + 10);
	qs[0].push_back(pii(0, 0));
	rep(dist,0,sz(qs)) {
		rep(qi,0,sz(qs[dist])) {
			pii pa = qs[dist][qi];
			if (seen2[pa.first][pa.second]) continue;
			seen2[pa.first][pa.second] = 1;
			if (pa.first == N-1 && pa.second == N-1) {
				cout << dist << endl;
				return 0;
			}

			auto add = [&](int a, int b, int d) {
				if (dist + d > sz(qs)) return;
				qs[dist + d].emplace_back(a, b);
			};

			trav(a, ed[pa.first]) {
				add(a, pa.second, (a != pa.second));
			}
			trav(b, ed2[pa.second]) {
				add(pa.first, b, (b != pa.first));
			}
			if (pa.first != pa.second && dists[pa.first][pa.second] == 1) { // (bug)
				add(pa.second, pa.first, dists[pa.first][pa.second] - 1);
			}
		}
	}

	assert(false);
}
