import os
import numpy as np
import json

if __name__ == "__main__":
    with open("./tles/parsedTles.json") as reader:
        tleSet = json.load(reader)

    tleKeys = list(tleSet.keys())

    numTles = len(tleKeys)

    summedData = np.empty(shape=(len(tleKeys), len(tleKeys)))
    summedData.fill(0)

    dataFolder = "perYearData"
    count = 0
    for path in os.listdir(dataFolder):
        dataPath = os.path.join(dataFolder, path)

        if count % 10 == 0:
            print("Loading file " + str(count))
        if os.path.isfile(dataPath):
            yearData = np.loadtxt(dataPath, delimiter=",")
            summedData = np.add(summedData, yearData)
        else:
            print("Error loading: " + dataPath)

        count = count + 1

    np.savetxt(
        "MergedCollideData.csv", summedData.astype(int), fmt="%i", delimiter=",",
    )

