#include "validator.h"

void run(){
    int n = Int(1, Arg("n"));
	Endl();
    int m = Arg("m");
	int line = Arg("line", 0);
	long long sums = 0;
	for (int i = 0; i < n; i++) {
		set<int> vals;
		int s = Int(0, n-1);
		sums += s;
		for (int j = 0; j < s; j++) {
			Space();
			int x = (int)Int(1, n) - 1;
			assert(x != i);
			vals.insert(x);
		}
		assert((int)vals.size() == s);
		Endl();

		if (line) {
			vals.insert(i);
			int lo = *vals.begin();
			int hi = *--vals.end();
			assert(hi - lo + 1 == (int)vals.size());
		}
	}

	assert(sums <= m);
}
