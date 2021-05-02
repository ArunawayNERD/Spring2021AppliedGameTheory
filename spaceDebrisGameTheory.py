import json
import numpy as np
import time
import gambit
import random


def getTleApproxMass(tle):
    lineOne = tle["l1"]
    bStar = lineOne[53:61]

    bStarNumber = float((bStar[0].strip() + "0." + bStar[1:6]).strip()) * (10 ** int(bStar[6:]))

    if bStarNumber == 0:
        return 0

    # 1.05 is the coefficent of drag for a cube
    massApprox = (1.05 * 1) / (2 * bStarNumber)

    return abs(massApprox)


def calculateUtility(countryNoradIdSet, removedIds, collisionSet, tleKeys, tleSet, massApproxByTle, costPerKilo):
    numberOfTles = len(tleKeys)
    idAndMassApprox = []

    for noradId in countryNoradIdSet:
        # First off check if we removed this tle in the removed step
        # we don't want to consider it for the util if we did
        if noradId in removedIds:
            continue

        tleIndex = -1
        try:
            tleIndex = tleKeys.index(noradId)
        except:
            # This is expected due to the two slightly data sources
            pass

        if tleIndex == -1:
            continue

        massApprox = massApproxByTle[noradId]
        numOfPotentialCollisions = 0

        for i in range(numberOfTles):

            compassionId = tleKeys[i]

            # if the id we are about to look at was remove then we don't want it to factor
            # into the cost so we just need to skip this iteration of the loop
            if compassionId in removedIds:
                continue

            # when i == tleIndex it jus going to be zero since it cant collide with itself
            collisions = collisionSet[i][tleIndex] if i <= tleIndex else collisionSet[tleIndex][i]
            numOfPotentialCollisions = numOfPotentialCollisions + (collisions)

        idAndMassApprox.append([noradId, numOfPotentialCollisions * massApprox])

    cost = sum([item[1] * costPerKilo for item in idAndMassApprox])
    return cost


def getIdsToRemove(countryNoradIdSet, numberToRemove, removedIds, collisionSet, tleKeys, tleSet, massApproxByTle):
    numberOfTles = len(tleKeys)
    idAndMassApprox = []

    for noradId in countryNoradIdSet:
        tleIndex = -1
        try:
            tleIndex = tleKeys.index(noradId)
        except:
            # This is expected due to the two slightly data sources
            pass

        if tleIndex == -1:
            continue

        massApprox = massApproxByTle[noradId]
        numOfPotentialCollisions = 0

        for i in range(numberOfTles):
            compassionId = tleKeys[i]

            # if the id we are about to look at was remove then we don't want it to factor
            # into the cost so we just need to skip this iteration of the loop
            if compassionId in removedIds:
                continue

            # when i == tleIndex it jus going to be zero since it cant collide with itself
            numOfPotentialCollisions = numOfPotentialCollisions + (
                collisionSet[i][tleIndex] if i <= tleIndex else collisionSet[tleIndex][i]
            )
            # print(numOfPotentialCollisions)

        idAndMassApprox.append([noradId, numOfPotentialCollisions * massApprox])

    idAndMassApprox = sorted(idAndMassApprox, key=lambda tleData: tleData[1], reverse=True)

    removed = idAndMassApprox[:numberToRemove]

    # Remove the set of ids that will be removed
    return [item[0] for item in removed]


def SpaceDebrisGameTheory(
    parsedTlePath, tleIdByCountryPath, MergedCollisionDataPath, countiesToExamine, maxNumberPossibleToRemove
):

    # Load the Data files
    with open("./tles/parsedTles.json") as reader:
        tleSet = json.load(reader)

    with open("./noradIdByCountryCode.json") as mappingReader:
        countryMapping = json.load(mappingReader)

    collisionSet = np.loadtxt("./MergedCollideData.csv", delimiter=",")

    tleKeys = list(tleSet.keys())

    # Get the mass approximates now since that will be constant
    massApproxByTle = {noradId: getTleApproxMass(tleSet[noradId]) for noradId in tleKeys}

    # Get the removal combos to try
    totalCombos = (maxNumberPossibleToRemove + 1) ** len(countiesToExamine)  # +1 because 0 is valid

    combos = []
    for i in range(totalCombos):
        comboString = np.base_repr(i, base=maxNumberPossibleToRemove + 1, padding=len(countiesToExamine))
        combos.append(comboString[-1 * len(countiesToExamine) :])

    startTime = time.time()

    game = gambit.Game.new_table([maxNumberPossibleToRemove + 1] * len(countiesToExamine))

    # Name the players in our game to the country codes
    for i in range(len(countiesToExamine)):
        game.players[i].label = countiesToExamine[i]

    #Now lets loop through all the move combos and add the untility values to the game
    value = 0
    for combo in combos:
        removedIds = []

        numberToRemovePerCountry = [int(i) for i in list(combo)]
        print(numberToRemovePerCountry)

        for countryIndex in range(len(numberToRemovePerCountry)):
            countryCode = countiesToExamine[countryIndex]
            numToRemove = numberToRemovePerCountry[countryIndex]
            # print(numToRemove)
            countrysIds = countryMapping[countryCode]

            # removed = getIdsToRemove(
            #     countrysIds, numToRemove, removedIds, collisionSet, tleKeys, tleSet, massApproxByTle
            # )
            removed = []
            removedIds.extend(removed)

        # Now that we have determined the ids to removed lets calclate the actual utilities
        for countryIndex in range(len(numberToRemovePerCountry)):
        # for countryCode in countiesToExamine:
            countrysIds = countryMapping[countiesToExamine[countryIndex]]
            # utility = calculateUtility(countrysIds, removedIds, collisionSet, tleKeys, tleSet, massApproxByTle, 1)
            game[numberToRemovePerCountry][countryIndex] = value
            value = value +1
            utility = 1
            # print(utility)

    
    nashEqulibs = gambit.nash.enumpure_solve(game)
    print(len(nashEqulibs[0]))
    playerStrats = np.array_split(np.array(nashEqulibs[0]),len(countiesToExamine))
    print(playerStrats)

    for playerIndex in range(len(playerStrats)):
        playerStrat = playerStrats[playerIndex]
        countryCode = countiesToExamine[playerIndex]

        for moveIndex in range(len(playerStrat)):
            if(playerStrat[moveIndex].numerator / playerStrat[moveIndex].denominator == 1):
                print('Country ' +  countryCode + " will removed " + str(moveIndex) + " of its satellites")
                break
        else:
            print('Error Country ' +  countryCode + " not pick a strategy")        

    endTime = time.time()
    print(endTime - startTime)


if __name__ == "__main__":
    # Options PRC, IND, IRAN, ISRA, JPN, CIS, NKOR, SKOR, US, ESA
    SpaceDebrisGameTheory(
        "./tles/parsedTles.json",
        "./noradIdByCountryCode.json",
        "./MergedCollideData.csv",
        # ["US", "PRC", "CIS", "IND", "JPN"],
        ["US", "PRC", "CIS", "IND"],
        # ["US", "CIS", "JPN"],
        # ["US", "CIS"],
        3,
    )

# for this dont allow IRAN, ISRA, NKOR not enough ids
