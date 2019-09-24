// Usage: ./validator .in-file .ans-file dir <in >out
#include <iostream>
#include <fstream>
#include <string>
#include <cassert>
#include <ctime>
#include <cstdlib>
#include <signal.h>
using namespace std;

const char* out_dir = nullptr;

void judge_message(const string& msg) {
	cerr << msg << endl;
	if (out_dir) {
		string fname = out_dir + string("/judgemessage.txt");
		ofstream fout(fname.c_str());
		fout << msg << endl;
	}
}

[[noreturn]]
void reject(const string& msg) {
	judge_message(msg);
	exit(43);
}

[[noreturn]]
void reject_line(const string& msg, const string& line) {
	judge_message(msg + ", with input " + line);
	exit(43);
}

[[noreturn]]
void accept(const string& msg) {
	judge_message(msg);
	exit(42);
}

[[noreturn]]
void judge_error2(const char* a, const char* b, const char* c) {
	string msg = string(a) + b + c;
	cerr << msg << endl;
	if (out_dir) {
		string fname = out_dir + string("/judgeerror.txt");
		ofstream fout(fname.c_str());
		fout << msg << endl;
	}
	abort();
}

#undef assert
#define STR2(x) #x
#define STR(x) STR2(x)
#define assert(x) do { if (!(x)) { judge_error2(__FILE__ ":" STR(__LINE__) ": ", __PRETTY_FUNCTION__, ": Assertion `" #x "' failed."); } } while (0)

int readnum(const char* str, int max, const string& line) {
	if (!str[0]) reject_line("invalid format (empty token)", line);
	int cur = 0;
	while (*str) {
		int dig = *str++ - '0';
		if (dig < 0 || dig > 9) reject_line("invalid format (not a digit)", line);
		cur *= 10;
		cur += dig;
		if (cur > max) reject_line("out of bounds (too large)", line);
	}
	if (cur < 1) reject_line("out of bounds (zero)", line);
	return cur;
}

int main(int argc, char** argv) {
	assert(argc >= 2);
	if (argc >= 4) out_dir = argv[3];
	ifstream fin(argv[1]);
	string strat;
	int seed;
	fin >> strat >> seed;
	assert(fin);
	// srand((int)time(0) + seed * 1000);
	srand(seed); // make the randomness static within a test case
	string dummy;
	assert(!(fin >> dummy));

	int num = 0;
	const int LIM = 99;
	string line;
	while (num < LIM) {
		if (!getline(cin, line)) reject("eof");
		int x = readnum(line.c_str(), 100000, line);
		if (x < num + 1 || x > num + 2) reject("didn't increase by 1 or 2");
		num = x;
		if (num > LIM) reject("overshot");
		if (num == LIM) {
			if (cin >> line) reject("expected eof");
			accept("won");
		}

		if (strat == "one") {
			num = num + 1;
		} else if (strat == "two") {
			num = min(num + 2, LIM);
		}
		else {
			num = min(num + 1 + rand() % 2, LIM);
		}
		if (num == LIM) {
			// Don't tell the program that it lost, to avoid race conditions.
			reject("lost");
		}
		cout << num << endl;
	}
}
