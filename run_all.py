"""
run_all.py - Reproduce every artefact of ICS Week 11.

Execution order:
  1. QC Gate 1 physics benchmarks
  2. Monte Carlo dataset (>=10k) + GBR surrogate
  3. Hero + secondary visuals
  4. Wall-loss evolution GIF
Run:  python run_all.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def step(title, argv):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    rc = subprocess.call([sys.executable] + argv, cwd=HERE)
    if rc != 0:
        print(f"STEP FAILED ({rc}): {title}")
        sys.exit(rc)


def main():
    step("QC GATE 1 - physics benchmarks", ["validation/benchmarks.py"])
    # dataset + surrogate
    step("Monte Carlo dataset + surrogate", ["-c",
         "import sys;sys.path.insert(0,'.');"
         "from src import monte_carlo as mc, surrogate_gbr as gbr;"
         "import csv,json,math,os;"
         "ds=mc.run(n=12000,seed=11);os.makedirs('assets',exist_ok=True);"
         "k=list(ds.rows[0].keys());"
         "w=csv.DictWriter(open('assets/mc_dataset.csv','w',newline=''),fieldnames=k);"
         "w.writeheader();[w.writerow(r) for r in ds.rows];"
         "X=ds.X();y=[math.log10(max(v,1e-3)) for v in ds.y()];"
         "m,met,(Xte,yte,yp)=gbr.train(X,y,n_estimators=300,max_depth=4,learning_rate=0.05);"
         "md={kk:(round(vv,5) if isinstance(vv,float) else vv) for kk,vv in met.items()};"
         "md['target']='log10(total_mm_yr)';md['mae_log10']=md.pop('mae',None);md['rmse_log10']=md.pop('rmse',None);"
         "rt=[10**t for t in yte];rp=[10**p for p in yp];"
         "md['mae_mm_yr']=round(sum(abs(a-b) for a,b in zip(rt,rp))/len(rt),4);"
         "md['rmse_mm_yr']=round((sum((a-b)**2 for a,b in zip(rt,rp))/len(rt))**0.5,4);"
         "json.dump(md,open('assets/surrogate_metrics.json','w'),indent=2);"
         "cw=csv.writer(open('assets/parity.csv','w',newline=''));cw.writerow(['y_true_mm_yr','y_pred_mm_yr']);[cw.writerow([10**t,10**p]) for t,p in zip(yte,yp)];"
         "imp=getattr(m,'feature_importances_',None);"
         "json.dump({n:round(float(v),5) for n,v in zip(ds.feature_names,imp)} if imp is not None else {},open('assets/feature_importance.json','w'),indent=2);"
         "print('dataset rows',len(ds.rows),'surrogate R2',round(met['r2'],4))"])
    step("Hero visual", ["viz/plot_hero.py"])
    step("Secondary visuals", ["viz/plot_secondary.py"])
    step("Wall-loss evolution GIF", ["viz/plot_gif.py"])
    print("\nAll artefacts regenerated in assets/.")


if __name__ == "__main__":
    main()
