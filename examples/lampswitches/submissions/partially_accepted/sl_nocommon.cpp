#include <bits/stdc++.h>
using namespace std;

#define rep(i, a, b) for(int i = a; i < (b); ++i)
#define trav(a, x) for(auto& a : x)
#define all(x) x.begin(), x.end()
#define sz(x) (int)(x).size()
typedef long long ll;
typedef pair<int, int> pii;
typedef vector<int> vi;

struct Bits {
	vector<uint64_t> words;
	Bits(int N) : words(N / 64 + 1) {}
	void set(int ind) {
		words[ind >> 6] |= 1ULL << (ind & 63);
	}
	void reset() {
		trav(x, words) x = 0;
	}
	void operator|=(const Bits& other) {
		rep(i,0,sz(words)) words[i] |= other.words[i];
	}
};

int main() {
	cin.sync_with_stdio(0); cin.tie(0);
	cin.exceptions(cin.failbit);
	int N;
	cin >> N;
	vector<Bits> ed(N, Bits(N));
	rep(i,0,N) {
		int s;
		cin >> s;
		rep(j,0,s) {
			int b;
			cin >> b;
			--b;
			ed[i].set(b);
		}
	}

	const int inf = 1000000;

	vector<vi> dists(N, vi(N, inf));
	rep(start,0,N) {
		vi& dist = dists[start];
		Bits currentb(N), nextb(N);
		currentb.set(start);
		vi todo = {start}, next;
		int d = 0;
		while (!todo.empty()) {
			nextb = currentb;
			trav(x, todo) {
				dist[x] = d;
				nextb |= ed[x];
			}
			d++;
			rep(i,0,sz(nextb.words)) {
				uint64_t w = nextb.words[i] & ~currentb.words[i];
				while (w) {
					int index = __builtin_ctzll(w);
					w &= w-1;
					next.push_back(index + 64 * i);
				}
			}
			currentb = nextb;
			todo = next;
			next.clear();
		}
	}

	vector<vi> dists2 = dists;
	rep(i,0,N) rep(j,0,N) {
		dists[i][j] = i == j ? 0 : min(inf, dists2[i][j] + dists2[j][i] - 1);
	}

	vi dist(N, inf);
	vi done(N);
	dist[0] = 0;
	for (;;) {
		pii best(inf, -1);
		rep(i,0,N) if (!done[i]) {
			best = min(best, pii(dist[i], i));
		}
		if (best.first == inf) break;
		int i = best.second;
		done[i] = 1;
		rep(j,0,N) dist[j] = min(dist[j], dist[i] + dists[i][j]);
	}

	if (dist[N-1] == inf) {
		cout << "nej" << endl;
	} else {
		cout << dist[N-1] << endl;
	}
}
