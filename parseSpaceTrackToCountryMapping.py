import json

if __name__ == "__main__":
    countryCodesOfInterest = ["PRC", "IND", "IRAN", "ISRA", "JPN", "CIS", "NKOR", "SKOR", "US", "ESA"]

    with open("./spaceTrackData.json") as reader:
        spaceTrackSet = json.load(reader)

    dataToParse = spaceTrackSet["data"]

    noradIdByCountry = {key: [] for key in countryCodesOfInterest}
    for tleData in dataToParse:
        countryCode = tleData["COUNTRY_CODE"]
        noradId = tleData["NORAD_CAT_ID"]

        if countryCode in countryCodesOfInterest:
            # pad to match the norad if field in the tle format
            noradIdByCountry[countryCode].append(noradId.zfill(5))

    json.dump(noradIdByCountry, open("./noradIdByCountryCode.json", "w"))

