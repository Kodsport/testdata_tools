N,K = map(int,raw_input().split())
l = map(int,raw_input().split())
positions = [[] for _ in range(K+1)]
for i in range(N):
    positions[l[i]].append(i)
answers = [-1]*N
for pos in positions[-1]:
    answers[pos] = 0
for div in range(K-1,0,-1):
    for pos in positions[div]:
        if positions[div+1][-1] < pos:
            answers[pos] = N-pos+positions[div+1][0] + answers[positions[div+1][0]] 
        else:
            lo = -1 #impossible
            hi = len(positions[div+1])-1 #possible
            while hi - lo > 1:
                mid = (hi+lo)/2
                if positions[div+1][mid] > pos: hi = mid
                else: lo = mid
            answers[pos] = positions[div+1][hi]-pos + answers[positions[div+1][hi]]
best = 10**20
for st in positions[1]:
    best = min(best,answers[st])
print best+1
