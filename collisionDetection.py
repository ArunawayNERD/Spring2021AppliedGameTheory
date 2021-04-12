from skyfield.api import EarthSatellite, load, utc
import json
from datetime import datetime, timedelta
import time
from dependencies.discrete_frechet.distances.discrete import *

# from dependencies.discrete_frechet.distances.discrete import FastDiscreteFrechetMatrix, DiscreteFrechet, haversine
import numpy as np
import sys


# fdfdm = FastDiscreteFrechetMatrix(haversine)


rdfd = DiscreteFrechet(euclidean)
ldfd = LinearDiscreteFrechet(euclidean)
fdfds = FastDiscreteFrechetSparse(euclidean)
fdfdm = FastDiscreteFrechetMatrix(euclidean)


au_to_km = 149598073


def calculateFrechetDistance(satOneData, satTwoData):

    # start = time.time()

    dist = np.sqrt(np.sum((satTwoData - satOneData) ** 2, axis=1))
    minDist = np.amin(dist)
    # end = time.time()
    # print(end - start)
    # print(np.sqrt(np.sum((npOrbitTwo - npOrbitOne) ** 2, axis=1))[0:5])

    # minDist = sys.maxsize
    # for i in range(len(satOneData)):
    #     pos1 = satOneData[i]
    #     pos2 = satTwoData[i]

    #     dist = np.sqrt((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2 + (pos2[2] - pos1[2]) ** 2)
    #     if dist < minDist:
    #         minDist = dist

    # minDist = sys.maxsize
    # for i in range(len(satOneData)):
    #     pos1 = satOneData[i]
    #     pos2 = satTwoData[i]

    #     dist = np.sqrt((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2 + (pos2[2] - pos1[2]) ** 2)
    #     # if dist < minDist:
    #     #     minDist = dist
    #     print(dist)

    return minDist


def willTwoCollide(satOneData, satTwoData, collisionDistance):
    # start = time.time()

    # Get and set up the time points to request
    # skyfieldTimeScale = load.timescale(builtin=True)

    # totalHours = ((endtime - startTime).total_seconds()) / (60 * 60)
    # timePoints = [startTime + timedelta(hours=i) for i in range(0, int(totalHours), timeStepHours)]

    # requestPoints = skyfieldTimeScale.utc(timePoints)

    # # Set up the sats and get the postions for the time points
    # satOne = EarthSatellite(satOneData["l1"], satOneData["l2"])
    # satTwo = EarthSatellite(satTwoData["l1"], satTwoData["l2"])

    # satOnePos = satOne.ITRF_position_velocity_error(requestPoints)[0]
    # satTwoPos = satTwo.ITRF_position_velocity_error(requestPoints)[0]

    # # Reform the return positions
    # orbitOne = [
    #     [satOnePos[0][i] * au_to_km, satOnePos[1][i] * au_to_km, satOnePos[2][i] * au_to_km]
    #     for i in range(len(satOnePos[0]))
    # ]
    # orbitTwo = [
    #     [satTwoPos[0][i] * au_to_km, satTwoPos[1][i] * au_to_km, satTwoPos[2][i] * au_to_km]
    #     for i in range(len(satTwoPos[0]))
    # ]

    # npOrbitOne = np.array(satOneData)
    # npOrbitTwo = np.array(satTwoData)

    # dist = np.sqrt(np.sum((npOrbitOne - npOrbitTwo) ** 2, axis=0))
    # minDist = np.amin(dist)

    # npOrbitOne = np.array(satOneData)
    # npOrbitTwo = np.array(satTwoData)

    minDist = calculateFrechetDistance(satOneData, satTwoData)

    # minDist = fdfdm.distance(npOrbitOne, npOrbitTwo)

    # end = time.time()
    # print(end - start)
    # print(minDist)

    return minDist < collisionDistance


if __name__ == "__main__":
    with open("./tles/parsedTles.json") as reader:
        tleSet = json.load(reader)

    tleKeys = list(tleSet.keys())
    # tleKeys = ["00900", "00902"]
    print(len(tleKeys))

    keepOutArea = 50

    for year in range(2023, 2025):
        print("Starting year " + str(year) + " at " + str(datetime.now()))
        tleOrbits = {}

        startTime = datetime(year, 1, 1, tzinfo=utc)
        endtime = datetime(year, 12, 31, tzinfo=utc)
        timeStepHours = 1

        skyfieldTimeScale = load.timescale(builtin=True)

        totalHours = ((endtime - startTime).total_seconds()) / (60 * 60)
        timePoints = [startTime + timedelta(hours=i) for i in range(0, int(totalHours), timeStepHours)]

        requestPoints = skyfieldTimeScale.utc(timePoints)
        # print(len(requestPoints))
        print("Starting Satellite Gen at " + str(datetime.now()))
        for i in range(len(tleKeys)):
            if i % 100 == 0:
                print("starting sat gen " + str(i) + " -- " + tleKeys[i] + " at " + str(datetime.now()))

            sat = EarthSatellite(tleSet[tleKeys[i]]["l1"], tleSet[tleKeys[i]]["l2"])
            pos = sat.ITRF_position_velocity_error(requestPoints)[0]

            # Reform the return positions
            orbit = [[pos[0][i] * au_to_km, pos[1][i] * au_to_km, pos[2][i] * au_to_km] for i in range(len(pos[0]))]
            orbit = [[pos[0][i] * au_to_km, pos[1][i] * au_to_km, pos[2][i] * au_to_km] for i in range(len(pos[0]))]

            tleOrbits[tleKeys[i]] = np.array(orbit)

        # willTwoCollide(tleOrbits[tleKeys[0]], tleOrbits[tleKeys[1]])

        print("Done Satellite Gen at " + str(datetime.now()))

        collide = np.empty(shape=(len(tleKeys), len(tleKeys)))
        collide.fill(0)
        for i in range(len(tleKeys)):
            if i % 100 == 0:
                print("starting sat " + str(i) + " -- " + tleKeys[i] + " at " + str(datetime.now()))

            for j in range(i + 1, len(tleKeys)):
                # https://www.nasa.gov/mission_pages/station/news/orbital_debris.html "This box is about a mile deep by 30 miles across by 30 miles long (1.5 x 50 x 50 kilometers),""
                collide[i, j] = willTwoCollide(tleOrbits[tleKeys[i]], tleOrbits[tleKeys[j]], keepOutArea)

        print("Start data write for " + str(year) + " at " + str(datetime.now()))
        np.savetxt(
            "./data/collide_year" + str(year) + "_keepOut " + str(keepOutArea) + ".csv",
            collide.astype(int),
            fmt="%i",
            delimiter=",",
        )
        print("Done data write for " + str(year) + " at " + str(datetime.now()))
        print("Done year " + str(year) + " at " + str(datetime.now()))

