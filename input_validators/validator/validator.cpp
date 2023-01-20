#include "validator.h"

// Example validator for the format:
// n m k
// a_1 a_2 ... a_n (1 <= a_i <= k)
// u_1 v_1
// ...
// u_m v_m

void run() {
	int n = Int(1, Arg("n"));
	Space();
	int m = Int(1, Arg("m"));
	Space();
	int k = Int(1, Arg("k"));
	Endl();

	bool require_connected = Arg("connected", 0);

	vector<int> colors = SpacedInts(n, 1, k);

	vector<vector<int>> ed(n);
	for (int i = 0; i < m; i++) {
		int a = Int(1, n);
		Space();
		int b = Int(1, n);
		Endl();
		assert(a != b);
		ed[a-1].push_back(b-1);
		ed[b-1].push_back(a-1);
	}

	for (int i = 0; i < n; i++) {
		assert(set<int>(ed[i].begin(), ed[i].end()).size() == ed[i].size());
	}

	if (require_connected) {
		vector<int> stack = {0}, seen(n);
		while (!stack.empty()) {
			int x = stack.back(); stack.pop_back();
			if (seen[x]++) continue;
			for (int y : ed[x]) stack.push_back(y);
		}
		assert(count(seen.begin(), seen.end(), 0) == 0);
	}
}
