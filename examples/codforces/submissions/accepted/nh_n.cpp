#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

ll n,k;
long long inf = 1e18;

vector<ll> FindNextDiv(vector<ll>& divisions) {
  vector<unordered_set<ll>> seen(k);
  vector<ll> next_div(n, -1);
  for (ll i=0; i<n; ++i) {
    seen[divisions[i]].insert(i);
    if (divisions[i] == 0) continue;
    for (const auto comp : seen[divisions[i]-1]) {
    	next_div[comp] = i;
    }
    seen[divisions[i]-1].clear();
  }
  for (ll i=0; i<n; ++i) {
    seen[divisions[i]].insert(i);
    if (divisions[i] == 0) continue;
    for (const auto comp : seen[divisions[i]-1]) {
    	next_div[comp] = i;
    }
    seen[divisions[i]-1].clear();
  }
  return next_div;

}

ll GetFastestTime(vector<ll>& divisions) {
  vector<ll> next_div = FindNextDiv(divisions);
  vector<unordered_map<ll,ll>> dijkstra(k);
  for (ll i=0; i<n; ++i) {
  	dijkstra[divisions[i]][i] = inf;
  	if (divisions[i] == 0) dijkstra[0][i]=1;
  }
  for (ll i=0; i<k-1; ++i){
    for (const auto comp_time : dijkstra[i]) {
      ll next_comp = next_div[comp_time.first];
      ll time_step = next_comp - comp_time.first;
      if (time_step < 0) time_step += n;
      ll new_time = comp_time.second + time_step;
      dijkstra[i+1][next_comp] = min(dijkstra[i+1][next_comp], new_time);
    }
  }
  ll fastest_time = inf;
  for (const auto comp_time : dijkstra[k-1]) {
    fastest_time = min(fastest_time, comp_time.second);
  }
  return fastest_time;
}

int main() {
  cin >> n >> k;
  vector<ll> divisions(n);
  for (ll i=0; i<n; ++i) {
    cin >> divisions[i];
    --divisions[i];
  }
  cout << GetFastestTime(divisions) << endl;
}