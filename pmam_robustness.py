"""PMAM robustness analyses (Section 3.5, Section 4.3, Tables 5-7, Appendix B).
Usage: python pmam_robustness.py pmam_scores.csv results.json
"""
import numpy as np, itertools, json, sys
import csv
def load_scores(path):
    J=["Denmark","Flanders","Italy","Greece","Portugal","Ireland"]
    M={(r["jurisdiction"],r["dimension"]):int(r["score"]) for r in csv.DictReader(open(path,encoding="utf8"))}
    return np.array([[M[(j,f"D{k}")] for k in range(1,9)] for j in J])
J=["Denmark","Flanders","Italy","Greece","Portugal","Ireland"]
S=load_scores(sys.argv[1])
n,m=S.shape; R={}
tot=S.sum(1); R["totals"]=dict(zip(J,tot.tolist()))
def band(t): return ["foundational","developing","advanced","frontier"][min(3,(t-1)//8) if t>0 else 0] if t>8 else "foundational"
def band(t):
    return "foundational" if t<=8 else "developing" if t<=16 else "advanced" if t<=24 else "frontier"
def comp_rank(v):  # competition ranking, 1=best, ties share best
    return np.array([1+np.sum(v>x) for x in v])
# --- level-value mappings
maps={"linear 0-1-2-3-4":[0,1,2,3,4],"convex 0-1-2-4-8":[0,1,2,4,8],"concave sqrt":[0,1,2**.5,3**.5,2]}
R["mappings"]={k:{"scores":dict(zip(J,np.round(np.array(v)[S].sum(1),2).tolist())),"rank":dict(zip(J,comp_rank(np.array(v)[S].sum(1)).tolist()))} for k,v in maps.items()}
# --- non-compensatory
R["count_L3plus"]=dict(zip(J,(S>=3).sum(1).tolist()))
R["min_level"]=dict(zip(J,S.min(1).tolist()))
R["count_L1minus"]=dict(zip(J,(S<=1).sum(1).tolist()))
R["median"]=dict(zip(J,np.median(S,1).tolist()))
# lexicographic weakest-link: sort each profile ascending, compare lexicographically
R["leximin_order"]=[J[i] for i in sorted(range(n),key=lambda i:tuple(sorted(S[i])),reverse=True)]
# --- alternative bands
alt={}
for shift in (-2,-1,0,1,2):
    th=(8+shift,16+shift,24+shift)
    alt[f"shift {shift:+d}"]={J[i]:("foundational" if t<=th[0] else "developing" if t<=th[1] else "advanced" if t<=th[2] else "frontier") for i,t in enumerate(tot)}
# conjunctive: band set by minimum level
alt["conjunctive (minimum level)"]={J[i]:["foundational","developing","advanced","frontier","frontier"][S[i].min()] for i in range(n)}
# attained-maximum rescaling: bands on 0..max observed per dimension
mx=S.max(0); resc=(S/mx).sum(1)/m
alt["rescaled to observed maxima (quartiles)"]={J[i]:("foundational" if r<=.25 else "developing" if r<=.5 else "advanced" if r<=.75 else "frontier") for i,r in enumerate(resc)}
R["resc_share"]=dict(zip(J,np.round(resc,3).tolist()))
R["alt_bands"]=alt
# --- dominance
dom={}
for i in range(n):
    dom[J[i]]=[J[j] for j in range(n) if i!=j and np.all(S[i]>=S[j]) and np.any(S[i]>S[j])]
R["dominance"]=dom
# --- Dirichlet
rng=np.random.default_rng(42); W=rng.dirichlet(np.ones(m),200000); T=W@S.T
ranks=np.array([comp_rank(t) for t in T[:20000]]) # rank acceptability on subset for speed? do full vectorised
gt=(T[:,:,None]>T[:,None,:]).sum(2); rk=1+ (T[:,None,:]>T[:,:,None]).sum(2)
RA=np.array([[np.mean(rk[:,i]==k) for k in range(1,n+1)] for i in range(n)])
R["RA_weights"]={J[i]:np.round(100*RA[i],1).tolist() for i in range(n)}
PW=np.array([[np.mean(T[:,i]>T[:,j]) for j in range(n)] for i in range(n)])
R["PW_weights"]={J[i]:np.round(100*PW[i],1).tolist() for i in range(n)}
R["Pfirst_weights_sole"]={J[i]:round(100*np.mean((T[:,i][:,None]>np.delete(T,i,1)).all(1)),1) for i in range(n)}
# --- perturbation variants
def perturb(scen,N=100000,seed=42):
    rng=np.random.default_rng(seed); X=np.repeat(S[None],N,0).astype(int)
    if scen["type"]=="indep":
        pu=np.broadcast_to(np.array(scen["pu"]),(n,m)) if np.ndim(scen["pu"]) else np.full((n,m),scen["pu"])
        pd=np.broadcast_to(np.array(scen["pd"]),(n,m)) if np.ndim(scen["pd"]) else np.full((n,m),scen["pd"])
        u=rng.random((N,n,m)); X=X+(u<pu)-((u>=pu)&(u<pu+pd))
    elif scen["type"]=="jur":   # common shock per jurisdiction + independent noise
        u=rng.random((N,n)); sh=(u<scen["q"]/2).astype(int)-((u>=scen["q"]/2)&(u<scen["q"])).astype(int)
        X=X+sh[:,:,None]; v=rng.random((N,n,m)); X=X+(v<scen["p"])-((v>=scen["p"])&(v<2*scen["p"]))
    elif scen["type"]=="dim":   # common shock per dimension across jurisdictions + independent noise
        u=rng.random((N,m)); sh=(u<scen["q"]/2).astype(int)-((u>=scen["q"]/2)&(u<scen["q"])).astype(int)
        X=X+sh[:,None,:]; v=rng.random((N,n,m)); X=X+(v<scen["p"])-((v>=scen["p"])&(v<2*scen["p"]))
    X=np.clip(X,0,4); T=X.sum(2)
    out={}
    mxT=T.max(1); mnT=T.min(1)
    out["DK sole first"]=round(100*np.mean((T[:,0]==mxT)&((T==mxT[:,None]).sum(1)==1)),1)
    out["DK first incl ties"]=round(100*np.mean(T[:,0]==mxT),1)
    out["IE sole last"]=round(100*np.mean((T[:,5]==mnT)&((T==mnT[:,None]).sum(1)==1)),1)
    out["IE last incl ties"]=round(100*np.mean(T[:,5]==mnT),1)
    bands=np.digitize(T,[8.5,16.5,24.5])
    b0=np.digitize(tot,[8.5,16.5,24.5])
    out["stay band"]={J[i]:round(100*np.mean(bands[:,i]==b0[i]),1) for i in range(n)}
    out["any frontier"]=round(100*np.mean((bands==3).any(1)),1)
    out["IE developing"]=round(100*np.mean(bands[:,5]==1),1)
    rk=1+(T[:,None,:]>T[:,:,None]).sum(2)
    out["RA"]={J[i]:[round(100*np.mean(rk[:,i]==k),1) for k in range(1,n+1)] for i in range(n)}
    out["PW"]={J[i]:[round(100*np.mean(T[:,i]>T[:,j]),1) for j in range(n)] for i in range(n)}
    return out
dimp=[0.05,0.05,0.05,0.15,0.15,0.15,0.15,0.05]
scen={"A symmetric 10%":{"type":"indep","pu":0.10,"pd":0.10},
      "B symmetric 8.3% (observed disagreement)":{"type":"indep","pu":0.083,"pd":0.083},
      "C stress 20%":{"type":"indep","pu":0.20,"pd":0.20},
      "D upward-biased (10% up, 5% down)":{"type":"indep","pu":0.10,"pd":0.05},
      "E dimension-specific (15% D4-D7, 5% others)":{"type":"indep","pu":dimp,"pd":dimp},
      "F jurisdiction-correlated (10% common shock + 5% noise)":{"type":"jur","q":0.10,"p":0.05},
      "G dimension-correlated (10% common shock + 5% noise)":{"type":"dim","q":0.10,"p":0.05}}
R["perturb"]={k:perturb(v) for k,v in scen.items()}
json.dump(R,open(sys.argv[2],"w"),indent=1,ensure_ascii=False,default=float)
# summary print
print("totals",R["totals"]); print("bands",{j:band(t) for j,t in R["totals"].items()})
for k,v in R["mappings"].items(): print(k,v["scores"],v["rank"])
print("L3+",R["count_L3plus"]); print("min",R["min_level"]); print("<=L1",R["count_L1minus"]); print("leximin",R["leximin_order"])
for k,v in alt.items(): print(k,v)
print("resc",R["resc_share"])
print("dom",dom)
print("RA weights",R["RA_weights"]); print("PW weights",R["PW_weights"]); print("sole first w",R["Pfirst_weights_sole"])
for k,v in R["perturb"].items():
    print(k,{x:v[x] for x in ["DK sole first","DK first incl ties","IE sole last","IE last incl ties","any frontier","IE developing"]},v["stay band"])
for i in range(8): print("LOO omit",i+1,{J[j]:int(tot[j]-S[j,i]) for j in range(6)})
