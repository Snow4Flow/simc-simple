import numpy as np
import simc_simple.sim
from pyproj import Transformer

def prep(confDict, nav):

    # Create data structures to hold output products
    traces              = len(nav)
    oDict               = {}
    oDict["combined"]   = np.zeros((confDict["simParams"]["tracesamples"], traces)).astype(np.float64)
    oDict["fret"]       = np.zeros((traces, 3)).astype(np.float64)

    # remove duplicate entries, calculate inverse
    _, idxUniq, inv = np.unique(nav, return_index=True, return_inverse=True, axis=0)
    nav             = nav.iloc[idxUniq].reset_index()

    # velocity vector components
    vx          = np.gradient(nav["x"])
    vy          = np.gradient(nav["y"])
    vz          = np.gradient(nav["z"])
    vMag        = np.sqrt((vx ** 2) + (vy ** 2) + (vz ** 2))
    v           = np.stack((vx / vMag, vy / vMag, vz / vMag), 
                           axis=1)
    nav["uv"]   = list(v)

    # vector to center of Earth
    cx      = -nav["x"]
    cy      = -nav["y"]
    cz      = -nav["z"]
    cMag    = np.sqrt((cx ** 2) + (cy ** 2) + (cz ** 2))
    c       = np.stack((cx / cMag, cy / cMag, cz / cMag), 
                       axis=1)

    # right pointing cross track vector
    l           = np.cross(c, v)
    lMag        = np.sqrt((l[:, 0] ** 2) + (l[:, 1] ** 2) + (l[:, 2] ** 2))
    nav["ul"]   = list(l / np.stack((lMag, lMag, lMag), 
                                    axis=1))

    return nav, oDict, inv

def calcBounds(dem, nav, xyzsys, atDist, ctDist):

    corners = np.zeros((len(nav) * 9, 3))

    for i in range(len(nav)):
        gx, gy, gz                          = simc_simple.sim.genGrid(nav.iloc[i], 
                                                                      1, 
                                                                      1, 
                                                                      atDist, 
                                                                      ctDist)
        corners[(i * 9):((i * 9) + 9), :]   = np.stack((gx, gy, gz), 
                                                       axis=1)

    demX, demY, _ = Transformer.from_crs(xyzsys, dem.crs).transform(corners[:, 0], 
                                                                    corners[:, 1], 
                                                                    corners[:, 2])

    ix, iy = ~dem.transform * (demX, demY)
    bounds = np.array([np.min(ix), np.max(ix), np.min(iy), np.max(iy)]).astype(int)

    if bounds[0] < 0:
        bounds[0] = 0
    if bounds[1] > dem.width - 1:
        bounds[1] = dem.width - 1
    if bounds[2] < 0:
        bounds[2] = 0
    if bounds[3] > dem.height - 1:
        bounds[3] = dem.height - 1

    return bounds