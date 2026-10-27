#!/usr/bin/env python3
"""Compare existing center-cell CHIRPS weighting with polygon intersection-area weighting.

Requires UNCROPPED original CHIRPS monthly GeoTIFF raster(s) and the fixed polygon.
No downloads, no modification of published rainfall CSVs. Outputs a separate audit CSV.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds, transform as window_transform
from rasterio.features import geometry_mask
from shapely.geometry import shape, box, mapping
from shapely.ops import transform as shapely_transform
from pyproj import Transformer

def compare(path, geom, proj):
    with rasterio.open(path) as src:
        if src.crs is None or src.transform.b != 0 or src.transform.d != 0:
            raise ValueError("Requires georeferenced north-up CHIRPS GeoTIFF")
        from rasterio.warp import transform_geom
        g = shape(transform_geom("EPSG:4326", src.crs, mapping(geom)))
        wb = from_bounds(*g.bounds, transform=src.transform)
        wb = wb.round_offsets().round_lengths()
        from rasterio.windows import Window
        col=max(0,int(wb.col_off)-1); row=max(0,int(wb.row_off)-1)
        width=min(src.width-col,int(wb.width)+3); height=min(src.height-row,int(wb.height)+3)
        if width<=0 or height<=0: raise ValueError("No raster polygon overlap")
        win=Window(col,row,width,height)
        t=src.window_transform(win)
        band=src.read(1,window=win,masked=True).astype("float64")
        vals=np.asarray(band.filled(np.nan))
        valid=np.isfinite(vals) & (vals>=0)
        center_mask=geometry_mask([mapping(g)],out_shape=vals.shape,transform=t,invert=True,all_touched=False)
        rr,cc=np.where(valid & center_mask)
        if len(rr)==0: raise ValueError("No valid center cells")
        lat=t.f+(rr+0.5)*t.e
        old=float(np.average(vals[rr,cc],weights=np.cos(np.radians(lat))))
        # Area intersections in an equal-area projection, including boundary cells.
        to_ea=Transformer.from_crs(src.crs, "EPSG:6933",always_xy=True).transform
        gp=shapely_transform(to_ea,g)
        weighted=0.; area=0.; nboundary=0; nintersect=0
        bounds=g.bounds
        for r in range(vals.shape[0]):
            for c in range(vals.shape[1]):
                if not valid[r,c]:continue
                x0,y0=t*(c,r); x1,y1=t*(c+1,r+1)
                cell=box(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1))
                if not cell.intersects(g):continue
                cp=shapely_transform(to_ea,cell)
                intersection=cp.intersection(gp).area
                if intersection <= 0:continue
                nintersect+=1
                if intersection/cp.area < 0.999999: nboundary+=1
                weighted+=float(vals[r,c])*intersection
                area+=intersection
        if area==0:raise ValueError("No valid fractional overlap")
        frac=weighted/area
        return {"month":path.stem,"center_cos_mm":round(old,6),
                "fractional_area_mm":round(frac,6),
                "delta_mm":round(frac-old,6),
                "delta_pct":round((frac-old)/old*100,4) if old!=0 else np.nan,
                "center_cells":len(rr),"fractional_cells":nintersect,"boundary_cells":nboundary}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rasters",required=True,help="Directory containing original monthly CHIRPS GeoTIFFs")
    p.add_argument("--polygon",default="handoff_writer/selected_data/song_ba_ha_catchment.geojson")
    p.add_argument("--output",default="outputs/quality/rainfall_spatial_sensitivity.csv")
    a=p.parse_args()
    import json
    geo=json.loads(Path(a.polygon).read_text(encoding="utf-8"))
    g=shape(geo["features"][0]["geometry"] if geo["type"]=="FeatureCollection" else geo["geometry"] if geo["type"]=="Feature" else geo)
    rasters=sorted(Path(a.rasters).glob("*.tif"))
    if len(rasters)!=36:raise SystemExit(f"Need 36 UNCROPPED monthly rasters, got {len(rasters)}; do not infer bias without inputs")
    rows=[compare(path,g,None) for path in rasters]
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(out,index=False)
    print(f"Saved {out}; max |delta_pct|={pd.DataFrame(rows)['delta_pct'].abs().max():.3f}%")
if __name__=="__main__":main()
