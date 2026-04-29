def clamp(v,lo=0,hi=1): return max(lo,min(hi,v))
def weighted_average(values,weights):
    s=sum(w for w in weights if w>=0)
    return sum(v*w for v,w in zip(values,weights))/s if s else 0.5
def normalize_score(v,min_v,max_v):
    if max_v<=min_v: return 0.5
    return clamp((v-min_v)/(max_v-min_v),0,1)
