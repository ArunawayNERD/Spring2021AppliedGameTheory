from skyfield.api import EarthSatellite, load, utc
import json
from datetime import datetime, timedelta
import time
import numpy as np
import sys
import os

au_to_km = 149598073


def willTwoCollide(satOneData, satTwoData, collisionDistance):
    dist = np.sqrt(np.sum((satTwoData - satOneData) ** 2, axis=1))
    minDist = np.amin(dist)

    return minDist < collisionDistance


def genOneYear(tleKeys, year, keepOutArea, dataFolderPath):
    print("Starting year " + str(year) + " at " + str(datetime.now()))
    tleOrbits = {}
    numTles = len(tleKeys)

    startTime = datetime(year, 1, 1, tzinfo=utc)
    endtime = datetime(year, 12, 31, tzinfo=utc)
    timeStepHours = 1

    skyfieldTimeScale = load.timescale(builtin=True)

    totalHours = ((endtime - startTime).total_seconds()) / (60 * 60)
    timePoints = [startTime + timedelta(hours=i) for i in range(0, int(totalHours), timeStepHours)]

    requestPoints = skyfieldTimeScale.utc(timePoints)

    print("Starting Satellite Gen at " + str(datetime.now()))
    for i in range(numTles):
        if i % 100 == 0:
            print("starting sat gen " + str(i) + " -- " + tleKeys[i] + " at " + str(datetime.now()))

        sat = EarthSatellite(tleSet[tleKeys[i]]["l1"], tleSet[tleKeys[i]]["l2"])
        pos = sat.ITRF_position_velocity_error(requestPoints)[0]

        # Reform the returned positions
        orbit = [[pos[0][i] * au_to_km, pos[1][i] * au_to_km, pos[2][i] * au_to_km] for i in range(len(pos[0]))]

        tleOrbits[tleKeys[i]] = np.array(orbit)

    print("Done Satellite Gen at " + str(datetime.now()))

    collide = np.empty(shape=(numTles, numTles))
    collide.fill(0)

    for i in range(numTles):
        if i % 100 == 0:
            print("starting sat " + str(i) + " -- " + tleKeys[i] + " at " + str(datetime.now()))

        for j in range(i + 1, numTles):
            collide[i, j] = willTwoCollide(tleOrbits[tleKeys[i]], tleOrbits[tleKeys[j]], keepOutArea)

    print("Start data write for " + str(year) + " at " + str(datetime.now()))
    np.savetxt(
        dataFolderPath + "/year" + str(year) + "_keepOut " + str(keepOutArea) + ".csv",
        collide.astype(int),
        fmt="%i",
        delimiter=",",
    )
    print("Done data write for " + str(year) + " at " + str(datetime.now()))
    print("Done year " + str(year) + " at " + str(datetime.now()))


if __name__ == "__main__":
    with open("./tles/parsedTles.json") as reader:
        tleSet = json.load(reader)

    tleKeys = list(tleSet.keys())
    # For testing
    # tleKeys = ["00900", "00902"]

    # https://www.nasa.gov/mission_pages/station/news/orbital_debris.html "This box is about a mile deep by 30 miles across by 30 miles long (1.5 x 50 x 50 kilometers),""
    keepOutArea = 50

    dataFolderPath = "./perYearData" + str(keepOutArea) + "KeepOut"

    if not os.path.exists(dataFolderPath):
        os.makedirs(dataFolderPath)

    for year in range(2021, 2122):
        genOneYear(tleKeys, year, keepOutArea, dataFolderPath)

