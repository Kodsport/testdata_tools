#include "validator.h"

void run() {
	int n = Int(1, Arg("n"));
	Space();
	int k = Int(1, Arg("k"));
	Endl();

	assert(k <= n);

	vector<int> x = SpacedInts(n, 1, k);

	if (Arg("kEqualsN", 0)) {
		assert(n == k);
	}

	set<int> st;
	for(int i : x)
		st.insert(i);
	for(int i = 1; i <= k; i++)
		assert(st.count(i));
}
