#!/usr/bin/env python3
"""Recalculate monthly Pearson lag-0/lag-1 with VALID-only and as-reported SUSPECT days.
Preserves original QA flags and published main-case figures.
"""
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
HYDRO=ROOT/"handoff_writer/selected_data/hydrology_clean.csv"
MONTHS=ROOT/"handoff_writer/selected_data/hydromet_monthly.csv"
OUT=ROOT/"handoff_writer/tables/T08_alternative_suspect_sensitivity.csv"
def pearson(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if len(x)<3 or not np.isfinite(x).all() or not np.isfinite(y).all(): raise ValueError("Invalid comparison pairs")
    return float(np.corrcoef(x,y)[0,1])
def main():
    h=pd.read_csv(HYDRO,parse_dates=["date"])
    m=pd.read_csv(MONTHS).sort_values("year_month").copy()
    if len(h)!=1096 or len(m)!=36: raise SystemExit("Unexpected data coverage")
    h["year_month"]=h["date"].dt.strftime("%Y-%m")
    h["inflow_m3s"]=pd.to_numeric(h["inflow_m3s"],errors="coerce")
    allowed=h[h["inflow_quality"].isin(["VALID","CORRECTED","SUSPECT"])]
    alternative=allowed.groupby("year_month")["inflow_m3s"].mean()
    if alternative.isna().any():raise SystemExit("NaN month in alternate case")
    m["alt"]=m["year_month"].map(alternative)
    if m["alt"].isna().any():raise SystemExit("Missing month")
    rain=m["rainfall_total_mm"].to_numpy(float)
    valid=m["inflow_mean_m3s"].to_numpy(float)
    all_reported=m["alt"].to_numpy(float)
    rows=[]
    for label,v in [("VALID_ONLY",valid),("INCLUDE_SUSPECT_AS_REPORTED",all_reported)]:
        rows.append({"scenario":label,"n_pairs_lag0":len(v),"pearson_lag0":round(pearson(rain,v),6),
          "n_pairs_lag1":len(v)-1,"pearson_lag1":round(pearson(rain[:-1],v[1:]),6),
          "inflow_nov_2025_m3s":round(float(m.loc[m.year_month=="2025-11", "inflow_mean_m3s" if label=="VALID_ONLY" else "alt"].iloc[0]),6),
          "notes":"QA-screened published series" if label=="VALID_ONLY" else "Sensitivity only, not a validation of extremes"})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT,index=False,encoding="utf-8-sig")
    print(pd.DataFrame(rows).to_string(index=False))
if __name__=="__main__":main()
