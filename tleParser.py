import json


def readConvertWrite(path, outPath):
    tleDict = {}
    with open(path) as reader:
        allTleLines = reader.read().splitlines()

        linesPerTLE = 3
        for i in range(0, len(allTleLines), linesPerTLE):
            tleLines = allTleLines[i : i + linesPerTLE]
            noradId = tleLines[linesPerTLE - 2][2:7]
            print(noradId)

            tleDict[str(noradId)] = {"name": tleLines[0].strip(), "l1": tleLines[1], "l2": tleLines[2]}

    with open(outPath, "w") as writer:
        json.dump(tleDict, writer)


if __name__ == "__main__":
    readConvertWrite("./tles/active.txt", "./tles/parsedTles.json")

