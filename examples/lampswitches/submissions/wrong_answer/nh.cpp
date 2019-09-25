#include <bits/stdc++.h>
using namespace std;

const int inf=1e9;

void FloydWarshall(const vector<vector<int>>& edges, vector<vector<int>>& dist) {
	int n = (int)dist.size();
	for (int i=0; i<n; ++i) {
		dist[i][i] = 0;
		for (int j=0; j<edges[i].size(); ++j) {
			dist[i][edges[i][j]] = 1;
		}
	}
	for (int i=0; i<n; ++i) {
		for (int j=0; j<n; ++j) {
			for (int k=0; k<n; ++k) {
				if (dist[i][j] > dist[i][k] + dist[k][j]) {
					dist[i][j] = dist[i][k] + dist[k][j];
				} 
			}
		}
	}
}

int dijkstra(int start, int goal, const vector<vector<int>> &pseudo_graph) {
	priority_queue<pair<int,int>> dijkstra_queue;
	vector<bool> vis(pseudo_graph.size(), false);
	dijkstra_queue.push(make_pair(0,start));
	vis[start] = true;
	while (!dijkstra_queue.empty()) {
		auto dist_node = dijkstra_queue.top();
		dijkstra_queue.pop();
		if (dist_node.second == goal) return dist_node.first;
		if (vis[dist_node.second]) continue;
		vis[dist_node.second] = true;
		for (int i=0; i<pseudo_graph.size(); ++i) {
			if (!vis[i]) {
				int dist = dist_node.first + pseudo_graph[dist_node.second][i];
				dijkstra_queue.push(make_pair(dist, i));
			}
		}
	}
	return -1;
}

int main() {
	int N; cin >> N;
	vector<vector<int>> edges(N);
	for (int i=0; i<N; ++i) {
		int s; cin >> s;
		edges[i].resize(s);
		for (int j=0; j<s; ++j) {
			cin >> edges[i][j];
			--edges[i][j];
		}
	}

	vector<vector<int>> dist(N, vector<int>(N,inf));
	FloydWarshall(edges, dist);
	vector<vector<int>> pseudo_graph = dist;
	for (int i=0; i<N; ++i) {
		for (int j=0; j<N; ++j) {
			pseudo_graph[i][j] = dist[i][j] + dist[j][i] - 1;
		}
		pseudo_graph[i][i] = 0;
	}

	int res = dijkstra(0,N-1,pseudo_graph);
	if (res == -1) cout << "nej" << endl;
	else cout << res + 1 << endl;
}
