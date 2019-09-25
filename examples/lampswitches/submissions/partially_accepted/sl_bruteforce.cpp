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
	vector<vi> ed(N);
	rep(i,0,N) {
		int s;
		cin >> s;
		ed[i].resize(s);
		rep(j,0,s) cin >> ed[i][j], --ed[i][j];
	}

	auto reach = [&](int bi, int from, int to) -> bool {
		if (!(bi & (1 << from))) return false;
		if (!(bi & (1 << to))) return false;
		vi seen(N);
		vi q = {from};
		rep(qi,0,sz(q)) {
			int x = q[qi];
			if (seen[x]++) continue;
			if (x == to) return true;
			if (!(bi & (1 << x))) continue;
			trav(y, ed[x]) q.push_back(y);
		}
		return false;
	};

	int res = INT_MAX;
	rep(bi,0,(1 << N)) {
		if (reach(bi, 0, N-1) && reach(bi, N-1, 0)) {
			int r = (int)bitset<32>(bi).count();
			res = min(r - 1, res);
		}
	}

	if (res == INT_MAX) cout << "nej" << endl;
	else cout << res << endl;
}
