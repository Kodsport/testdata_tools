#include <bits/stdc++.h>
using namespace std;

#define rep(i, a, b) for(int i = a; i < (b); ++i)
#define trav(a, x) for(auto& a : x)
#define all(x) x.begin(), x.end()
#define sz(x) (int)(x).size()
#define hash dhsjakhd
typedef long long ll;
typedef pair<int, int> pii;
typedef pair<ll, ll> pll;
typedef vector<int> vi;
typedef vector<ll> vl;
typedef long double ld;

ll n,m,T,k,q;
const ll big = 1000000007;
const ll big2 = 998244353;

const ll MAXN = 500;

vector<vi> C(MAXN, vi());
vector<vi> C2(MAXN, vi());

unordered_map<int,int> M;
int ans = big;

int has(int i, int j, int checkpoint){
    return MAXN*(MAXN*i+j)+checkpoint;
}

queue<int> Q1;
queue<int> Q2;

void add_edge(int d, int b, int w){
    if(M.find(b) == M.end()){
        M[b] = d+w;
        if(w == 0){
            Q1.push(b);
        }
        else{
            Q2.push(b);
        }
    }
    else{
        int d2 = M[b];
        if(d+w < d2){
            M[b] = d+w;
            if(w == 0){
                Q1.push(b);
            }
            else{
                Q2.push(b);
            }
        }
    }
}

void bfs(){
    M[0] = 0;
    Q1.push(0);
    while(!(Q1.empty() && Q2.empty())){
        int a;
        if(Q1.empty()){
            a = Q2.front();
            Q2.pop();
        }
        else{
            a = Q1.front();
            Q1.pop();
        }
        int d = M[a];
        int checkpoint = a%MAXN;
        a/=MAXN;
        int j = a%MAXN;
        a/=MAXN;
        int i = a;
        if(i == n-1 && j == n-1){
            ans = d;
            return;
        }

        if(i != j){
            int b = has(i,j,i);
            add_edge(d,b,0);
        }

        if(i == j){
            int b = has(i,checkpoint,i);
            add_edge(d,b,0);
        }

        for(int c1 = 0; c1 < sz(C[i]); c1++){
            int i2 = C[i][c1];
            int b = has(i2,j,checkpoint);
            add_edge(d,b,i2!=j);
        }
        for(int c1 = 0; c1 < sz(C2[j]); c1++){
            int j2 = C2[j][c1];
            int b = has(i,j2,checkpoint);
            add_edge(d,b,i!=j2);
        }
    }
}

int main() {
    ios_base::sync_with_stdio(0);
    cin.tie(0);
    //freopen("input.txt","r",stdin);
    //freopen("autput.txt","w",stdout);
    ll a,b,c,e;

    cin >> n;
    for(int c1 = 0; c1 < n; c1++){
        cin >> a;
        for(int c2 = 0; c2 < a; c2++){
            cin >> b;
            b--;
            C[c1].push_back(b);
            C2[b].push_back(c1);
        }
    }
    assert(n <= 100);
    bfs();
    if(ans == big){
        cout << "nej\n";
    }
    else{
        cout << ans << "\n";
    }
    return 0;
}
