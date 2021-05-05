import json
import numpy as np
import time
import gambit
import random
import os


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


def mergeCollisionData(numOfTles, dataFolderPath, numOfYears):
    summedData = np.empty(shape=(numOfTles, numOfTles))
    summedData.fill(0)

    #Need sort this becuse the order returned from the file system probably
    #wont be in order. Since we are potentially onyl looking at a subset 
    #of the data insuring the order is important 
    paths = sorted(os.listdir(dataFolderPath))
    
    print("Info: Starting loading collision data")
    for pathIndex in range(min(numOfYears, len(paths))):
        dataPath = os.path.join(dataFolderPath, paths[pathIndex])

        if os.path.isfile(dataPath):
            yearData = np.loadtxt(dataPath, delimiter=",")
            summedData = np.add(summedData, yearData)
        else:
            print("Error: Loading: " + dataPath + ' failed')

    print("Info: Done loading collision data")

    return summedData


def SpaceDebrisGameTheory(
    parsedTlePath, tleIdByCountryPath, collisionDataFolder, countiesToExamine, maxNumberPossibleToRemove, costPerKilo, costToRemoveOne, yearsToExamine
):

    # Load the Data files
    try:
        with open(parsedTlePath) as reader:
            tleSet = json.load(reader)
    except:
        print('Error: File path for input field parsedTlePath is not valid. Aborting.')
        return
    try:
        with open(tleIdByCountryPath) as mappingReader:
            countryMapping = json.load(mappingReader)
    except:
        print('Error: File path for input field tleIdByCountryPath is not valid. Aborting.')
        return

    tleKeys = list(tleSet.keys())
    numTles = len(tleKeys)
    
    collisionSet = mergeCollisionData(numTles, collisionDataFolder, yearsToExamine)
    #Leaving this here for testing or if a user wants to pre compute the merged data
    # collisionSet = np.loadtxt("./MergedCollideData.csv", delimiter=",")
    print("Info: Done loading all setup data")
    

    # Get the mass approximates now since that will be constant
    print("Info: Starting mass approximation calculations")
    massApproxByTle = {noradId: getTleApproxMass(tleSet[noradId]) for noradId in tleKeys}
    print("Info: Done mass approximation calculations")

    numCountries= len(countiesToExamine)


    print("Info: Starting to determine all player action combos")
    # Get the removal combos to examine
    totalCombos = (maxNumberPossibleToRemove + 1) ** numCountries  # +1 because 0 is valid

    combos = []
    for i in range(totalCombos):
        #Counting in this base will actually produce all of the combinations we need to examine
        comboString = np.base_repr(i, base=maxNumberPossibleToRemove + 1, padding=numCountries)
        combos.append(comboString[-1 * numCountries :])
    print("Info: Done determining all player action combos")

    
    print("Info: Setting up gambit game")
    #Set up the empty gambit game representation
    game = gambit.Game.new_table([maxNumberPossibleToRemove + 1] * numCountries)

    # Name the players in our game to the country codes
    for i in range(numCountries):
        game.players[i].label = countiesToExamine[i]
    print("Info: Done setting up gambit game")

    print("Info: Starting utility calculations (this could take a while)")
    startTime = time.time()

    #Now lets loop through all the move combos and add the utility values to the game
    for combo in combos:
        removedIds = []

        numberToRemovePerCountry = [int(i) for i in list(combo)]
        # print(numberToRemovePerCountry)

        for countryIndex in range(len(numberToRemovePerCountry)):
            countryCode = countiesToExamine[countryIndex]
            numToRemove = numberToRemovePerCountry[countryIndex]
            # print(numToRemove)
            countrysIds = countryMapping[countryCode]

            removed = getIdsToRemove(
                countrysIds, numToRemove, removedIds, collisionSet, tleKeys, tleSet, massApproxByTle
            )
            # removed = []
            removedIds.extend(removed)

        # Now that we have determined the ids to removed lets calclate the actual utilities
        for countryIndex in range(len(numberToRemovePerCountry)):
            numToRemove = numberToRemovePerCountry[countryIndex]
            countrysIds = countryMapping[countiesToExamine[countryIndex]]
            utility = calculateUtility(countrysIds, removedIds, collisionSet, tleKeys, tleSet, massApproxByTle, costPerKilo)
            
            #Subtract the costs for removing sats
            utility = utility + numToRemove * costToRemoveOne
            
            game[numberToRemovePerCountry][countryIndex] = int(utility)
    print("Info: Done utility calculations")
    
    nashEqulibs = gambit.nash.enumpure_solve(game)
    
    print('------Results------')
    print('Total nash equilibrium: ' + str(len(nashEqulibs)))
    playerStrats = np.array_split(np.array(nashEqulibs[0]),numCountries)

    for equilibriumIndex in range(len(nashEqulibs)):
        if len(nashEqulibs) > 1:
            print("Nash equilibrium" + str(equilibriumIndex))

        playerStrats = np.array_split(np.array(nashEqulibs[0]),numCountries)
    
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


if __name__ == "__main__":
    # The valid options are PRC, IND, IRAN, ISRA, JPN, CIS, NKOR, SKOR, US, ESA
    # but for this we wont actually allow IRAN, ISRA, NKOR because they dont have 
    # enough ids compared to the others
    validOptions = ['PRC', 'IND', 'JPN', 'CIS', 'SKOR', 'US', 'ESA']

    inputData = {}
    try:
        with open("./runSettings.json") as reader:
            inputData = json.load(reader)
    except:
        print("Warn: No ./runSettings.json file found. Default values will be used")

    #Now that we have the inputs lets validate them

    #Standardize the the input costs. People might naturally put positive numbers in for the costs
    #This will result in positive utility values. however gambit tries to maximize the utility so
    #it will actually use negative numbers for the costs (which also kinda makes sense if you think about it)
    #To make sure we are using negatives we will abs() the input and then multiple  by -1
    inputCostPerKilo = -1 * abs(inputData.get("costPerKilo",-0.1))
    inputCostToRemoveOne = -1 * abs(inputData.get("costToRemoveOne",-52000000))
    
    #Make sure they entered a positive number
    inputMaxNumber = inputData.get("maxNumberToRemove",3)
    if inputMaxNumber <= 0:
        print("Warn: Entered max number to remove was less then 1. Defaulting to 1")
        inputMaxNumber = 1

    if inputMaxNumber > 5:
       print("Warn: Entered max number is greater then 5. Run times might be significant") 

    #Lets make sure the supplied file paths exist
    inputParsedTlePath = inputData.get("parsedTlePath","./tles/parsedTles.json")
    if not os.path.exists(inputParsedTlePath):
        print('Warn:File supplied for field parsedTlePath does not exist. Falling back to default')
        inputParsedTlePath = "./tles/parsedTles.json"

    inputTleIdByCountryPath = inputData.get("tleIdByCountryPath","./noradIdByCountryCode.json")
    if not os.path.exists(inputTleIdByCountryPath):
        print('Warn:File supplied for field tleIdByCountryPath does not exist. Falling back to default')
        inputTleIdByCountryPath = "./noradIdByCountryCode.json"

    #perYearData50KeepOut
    inputCollisionDataFolder = inputData.get("collisionDataFolder","perYearData50KeepOut")
    if not os.path.exists(inputCollisionDataFolder):
        print('Warn:File supplied for field collisionDataFolder does not exist. Falling back to default')
        inputCollisionDataFolder = "perYearData50KeepOut"


    inputYearsToExamine = inputData.get("yearsToExamine", 25)
    if inputYearsToExamine < 1:
        print("Warn: Years to examine cannot be less than 1. Defaulting to 1")

    #Make sure the supplied codes are valid
    inputCountryCodes = inputData.get("countiesToExamine",["US", "PRC", "JPN"])
    # Alt test sets left in for testing
    # ["US", "PRC", "CIS", "IND", "JPN"],
    # ["US", "PRC", "CIS", "IND"],

    #For this one we will error out and tell the user to fix it because the players is kinda 
    #a critical part of game theory....
    for code in inputCountryCodes:
        if code not in validOptions:
            print('Error: Country code \'' + code + '\' is not a valid option. Aborting\n'+
                'Valid options are ' + str(validOptions) + '\nAborting')
            break
    else:        
        SpaceDebrisGameTheory(
            inputParsedTlePath,
            inputTleIdByCountryPath,
            inputCollisionDataFolder,
            inputCountryCodes,
            inputMaxNumber,
            inputCostPerKilo,
            inputCostToRemoveOne,
            inputYearsToExamine
        )


