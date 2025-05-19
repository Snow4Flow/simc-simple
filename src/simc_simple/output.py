import numpy as np
from pyproj import Transformer

def build(confDict, oDict, fcalc, navDatum, oi):
    # bincount requires assumptions - all positive integers, nothing greater than tracelen. Need to make sure these are met

    pwr     = fcalc[:, 0]
    twttAdj = fcalc[:, 1] - navDatum
    cbin    = (twttAdj / confDict["simParams"]["dt"]).astype(np.int32)

    # get rid of data that is after end of trace
    pwr[cbin >= confDict["simParams"]["tracesamples"]] = 0

    # modulo enforces sharad FPB matching behavior. should probably do this in a better way
    cbin = np.mod(cbin, confDict["simParams"]["tracesamples"])

    oDict["combined"][:, oi[0]] = np.bincount(cbin, 
                                              weights=pwr, 
                                              minlength=confDict["simParams"]["tracesamples"])
    oDict["fret"][oi[0], :]     = fcalc[twttAdj == twttAdj.min(), :][0, 4:7]

    if len(oi) > 1:
        for j in range(1, len(oi)):
            oDict["combined"][:, oi[j]] = oDict["combined"][:, oi[0]]
            oDict["fret"][oi[j], :]     = oDict["fret"][oi[0], :]

    return 0

def save(confDict, oDict, nav):

    flat, flon, felev = Transformer.from_crs(confDict["navigation"]["xyzsys"], 
                                             confDict["navigation"]["llesys"]).transform(oDict["fret"][:, 0], 
                                                                                         oDict["fret"][:, 1], 
                                                                                         oDict["fret"][:, 2])

    np.savetxt(confDict["paths"]["outpath"] + "firstReturn.csv",
               np.stack((flat, 
                         flon, 
                         felev, 
                         ((((2 * np.sqrt(((nav["x"].to_numpy() - oDict["fret"][:, 0]) ** 2) + 
                                         ((nav["y"].to_numpy() - oDict["fret"][:, 1]) ** 2) + 
                                         ((nav["z"].to_numpy() - oDict["fret"][:, 2]) ** 2))) / 
                                         confDict["simParams"]["speedlight"]) - nav["datum"].to_numpy()) 
                                         / confDict["simParams"]["dt"]).astype(np.int32)), 
                                         axis=1), 
               delimiter=",",
               header="lat,lon,elev,sample",
               fmt="%.6f,%.6f,%.3f,%d",
               comments="")

    oDict["combined"].astype("float32").tofile(confDict["paths"]["outpath"] + "combined.img")

    return 0