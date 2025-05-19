# Simplified version of SIMC clutter simulator developed by Michael Christoffersen and Brandon Tober. 
# Forked from https://github.com/lpl-tapir/simc
# Refactored into fewer functions and intended only for Earth.
# 
# Joe MacGregor (NASA/GSFC)

import numpy as np
import rasterio as rio
import simc.ingest, simc.output, simc.prep, simc.sim
import tqdm
from pyproj import CRS, Transformer

def main():

    argDict     = simc.ingest.parseCmd()
    confDict    = simc.ingest.readConfig(argDict)
    dem         = rio.open(confDict["paths"]["dempath"], 
                           mode="r")
    nav         = simc.ingest.readNav(confDict["paths"]["navpath"],
                                      confDict["navigation"]["navsys"],
                                      confDict["navigation"]["xyzsys"])

    # Parse DEM CRS
    xform           = Transformer.from_crs(confDict["navigation"]["xyzsys"], 
                                           CRS.from_user_input(dem.crs))
    nav, oDict, inv = simc.prep.prep(confDict, nav)
    bounds          = simc.prep.calcBounds(dem,
                                           dem.crs,
                                           nav,
                                           confDict["navigation"]["xyzsys"],
                                           confDict["facetParams"]["atdist"],
                                           confDict["facetParams"]["ctdist"])

    rowSub = (bounds[2], bounds[3] + 1)
    colSub = (bounds[0], bounds[1] + 1)

    win     = rio.windows.Window.from_slices(rowSub, colSub)
    demData = dem.read(1, 
                       window=win)
    gt      = ~demData.window_transform(win) # # geotransform DEM x,y to pixel coordinates

    for i in tqdm.tqdm(range(len(nav)), 
                       disable=(not argDict["p"])):
        fcalc = simc.sim.sim(confDict, dem, nav, xform, demData, gt, i)
        if fcalc.shape[0] == 0:
            continue
        
        # Putting things back in order
        simc.output.build(confDict, oDict, fcalc, nav["datum"][i], np.where(inv == i)[0])

    simc.output.save(confDict, oDict, nav.iloc[inv, :].reset_index(), dem, win, demData)
    dem.close()

if __name__ == "__main__":
    main()