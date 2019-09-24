#include "validator.h"

void run() {
	int ab_lim = Arg("ab");
	Int(1, ab_lim);
	Space();
	Int(1, ab_lim);
	Space();
	Int(1, Arg("c"));
	Endl();
}
