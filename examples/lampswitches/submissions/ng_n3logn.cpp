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

int ans = big;

int has(int i, int j, int mode){
    return 2*(MAXN*i+j)+mode;
}

ll DIST[MAXN][MAXN] = {0};
bool mark[MAXN] = {0};

void bfs2(int i){
    for(int c1 = 0; c1 < n; c1++){
        DIST[i][c1] = big;
        mark[c1] = 0;
    }
    DIST[i][i] = 0;
    queue<int> Q;
    Q.push(i);
    while(!Q.empty()){
        int a = Q.front();
        Q.pop();
        if(!mark[a]){
            mark[a] = 1;
            for(int c1 = 0; c1 < sz(C[a]); c1++){
                int b = C[a][c1];
                if(DIST[i][b] == big){
                    DIST[i][b] = DIST[i][a]+1;
                    Q.push(b);
                }
            }
        }
    }
}


bool mark2[MAXN][MAXN][2] = {0};
int DIST2[MAXN][MAXN][2] = {0};
priority_queue<pii> pq;

void add_edge(int i, int j, int mode, int d){
    if(d < DIST2[i][j][mode]){
        DIST2[i][j][mode] = d;
        pq.push({-d,has(i,j,mode)});
    }
}

void dijkstra(){
    for(int c1 = 0; c1 < n; c1++){
        for(int c2 = 0; c2 < n; c2++){
            for(int c3 = 0; c3 < 2; c3++){
                DIST2[c1][c2][c3] = big;
            }
        }
    }
    DIST2[0][0][0] = 0;

    pq.push({0,0});
    while(!pq.empty()){
        int a = pq.top().second;
        pq.pop();
        int mode = a%2;
        a/=2;
        int j = a%MAXN;
        a/=MAXN;
        int i = a;
        if(i == n-1 && j == n-1){ans = DIST2[i][j][mode];return;}
        if(!mark2[i][j][mode]){
            mark2[i][j][mode] = 1;
            for(int c1 = 0; c1 < n; c1++){
                if(mode == 0){
                    int d = DIST2[i][j][mode] + DIST[i][c1];
                    add_edge(c1,j,1,d);
                }
                else{
                    int d = DIST2[i][j][mode] + DIST[c1][j] + DIST[i][c1] - 1;
                    add_edge(c1,i,0,d);
                }
            }
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

    for(int c1 = 0; c1 < n; c1++){
        bfs2(c1);
    }
    if(DIST[0][n-1] == big || DIST[n-1][0] == big){
        cout << "nej\n";
        return 0;
    }
    dijkstra();
    cout << ans << "\n";
    return 0;
}
