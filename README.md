This repository was developed as part of the the JHU - EP Spring 2021 Applied Game theory course. The project goal was to apply game theory to the space debris problem 

## Install 
There are a couple libraries which will be required. They are

- numpy
- skyfield
- gambit

The gambit library requires some extra attention since it is not as easy to install as other python packages. You cannot simply pip install it. Instead you will need to build the python package yourself. 
The first step in this is cloning the master branch of the gambit github repository found at 

https://github.com/gambitproject/gambit

You will want to make sure you clone the master branch and not a previous released tag because as far as I can tell only the master branch supports python 3. After cloning the branch you will likely need to make a source code change specified in this issue comment 

https://github.com/gambitproject/gambit/issues/258#issuecomment-628738010  

from there you just need to follow the steps in their documentation which is found here

https://gambitproject.readthedocs.io/en/latest/build.html#build-python


It should be noted that this tool can only work in its entirety on a Linux system. This is due to the fact that the Gambit python package does not support windows. However, the collision detection data generation (collisionDetection.py) will work on both windows and linux

## Run
After the set up in the previous section has been carried out you can now start running the code. This is done by running the spaceDebrisGameTheory.py file. It does not take any command line arguments. instead it will read in the runSettings.json file if it exists (if it does not exist defaults will be used). It will look in the following runSettings.json for the following keys 

- costPerKilo - the cost to move one kg of mass (Default: .1)
- costToRemoveOne - the cost to remove one object (Default: 52 million)
- maxNumberToRemove - The max number of objects a player could remove (Default: 3)
- parsedTlePath - The file location of the parsed tle data (Default: ./tles/parsedTles.json)
- tleIdByCountryPath - The file location to the json file mapping country ids to tle ids (Default: ./noradIdByCountryCode.json)
- collisionDataFolder - The path to the folder that containers the generated yearly potential collision data (Default: perYearData)
- yearsToExamine - How many years into the future should the game examine (Default: 25)
- countiesToExamine - The set of country codes to use as players in the game (Default: ["US", "PRC", "JPN"])
    - Options ['PRC', 'IND', 'JPN', 'CIS', 'SKOR', 'US', 'ESA'] 

Once you have specificized your desired options then you just need to run spaceDebrisGameTheory.py. The results along with status, warning, and error messages will output in the console. 
