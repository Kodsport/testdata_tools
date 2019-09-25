#include <bits/stdc++.h>
using namespace std;

#define rep(a, b, c) for(int a = (b); a < (c); a++)
#define all(v) v.begin(), v.end()

typedef long long int ll;
typedef pair<int, int> pii;
typedef vector<int> vi;

int n, k;
vi v;
vector<ll> dp;
vector<set<int> > nxt;

ll f(int i) {
  if (v[i] == k)
    return 0;
  if (dp[i] != -1)
    return dp[i];

  int j = *(nxt[v[i]+1].upper_bound(i));
  return dp[i] = j-i + f(j%n);
}

int main(){
  ios_base::sync_with_stdio(0);
  cin.tie(0);

  cin >> n >> k;
  dp.resize(n, -1);
  v.resize(n);
  nxt.resize(k + 1);

  rep(i, 0, n) {
    cin >> v[i];
    nxt[v[i]].insert(i);
    nxt[v[i]].insert(i + n);
  }

  ll ans = 1e18;
  rep(i, 0, n)
    if (v[i] == 1)
      ans = min(ans, f(i));
  cout << ans+1 << endl;

}
