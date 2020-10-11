import json
import os
import time

from geopy import distance
import pyttsx3
import requests

import configReader
import gpsScanner
import googleASR
import pocketSphinxASR


class DirectionsClient():


    configReader = None
    googleASR = None
    gpsScanner = None
    pocketSphinxASRLocType = None
    pocketSphinxASRYesNo = None
    textToSpeech = None

    directionsAPIURL = None
    directionsAPIKey = None
    geocodingAPIURL = None
    placeSearchAPIURL = None

    savedAddresses = None
    directionsHash = None 


    def __init__(
        self,
        configFile="config.xml",
        directionsAPIURLIn=None,
        directionsAPIKeyIn=None,
        geocodingAPIURLIn=None,
        placeSearchAPIURLIn=None,
        gpsPortIn=None,
        gpsBaudIn=None,
        audioInputDeviceIndexIn=None,
        audioThresholdIn=None,
        timeoutLengthIn=None,
        googleServiceAccountJSONIn=None,
        ttsWordRateIn=None
    ):
        self.configReader = configReader.ConfigReader(configFile)

        self.directionsAPIURL = self.configReader.getDirectionsAPIURL()
        if directionsAPIURLIn:
            self.directionsAPIURL = directionsAPIURLIn

        self.directionsAPIKey = self.configReader.getDirectionsAPIKey()
        if directionsAPIKeyIn:
            self.directionsAPIKey = directionsAPIKeyIn

        self.geocodingAPIURL = self.configReader.getGeocodingAPIURL()
        if geocodingAPIURLIn:
            self.geocodingAPIURL = geocodingAPIURLIn

        self.placeSearchAPIURL = self.configReader.getPlaceSearchAPIURL()
        if placeSearchAPIURLIn:
            self.placeSearchAPIURL = placeSearchAPIURLIn

        ttsWordRate = self.configReader.getTextToSpeechWordRate()
        if ttsWordRateIn:
            ttsWordRate = ttsWordRateIn

        googleServiceAccountJSON = self.configReader.getGoogleServiceAccountJSONFilePath()
        if googleServiceAccountJSONIn:
            googleServiceAccountJSON = googleServiceAccountJSONIn

        audioInputDeviceIndex = self.configReader.getAudioInputDeviceIndex()
        if audioInputDeviceIndexIn != None:
            audioInputDeviceIndex = audioInputDeviceIndexIn

        audioThreshold = self.configReader.getAudioThreshold()
        if audioThresholdIn != None:
            audioThreshold = audioThresholdIn

        timeoutLength = self.configReader.getTimeoutLength()
        if timeoutLengthIn != None:
            timeoutLength = timeoutLengthIn

        gpsPort = self.configReader.getGPSDevicePort()
        if gpsPortIn:
            gpsPort = gpsPortIn

        gpsBaud = self.configReader.getGPSDeviceBaud()
        if gpsBaudIn:
            gpsBaud = gpsBaudIn

        self.savedAddresses = self.configReader.getSavedAddresses()

        self.textToSpeech = pyttsx3.init()
        self.textToSpeech.setProperty("rate", ttsWordRate)

        self.googleASR = googleASR.GoogleASR(
            googleServiceAccountJSON=googleServiceAccountJSON,
            audioInputDeviceIndex=audioInputDeviceIndex,
            audioThreshold=audioThreshold,
            timeoutLength=timeoutLength
        )

        self.pocketSphinxASRYesNo = pocketSphinxASR.PocketSphinxASR(
            audioInputDeviceIndex=audioInputDeviceIndex,
            audioThreshold=audioThreshold,
            timeoutLength=timeoutLength,
            lmPath=os.path.join(os.getcwd(), "yesno.lm"),
            dictPath=os.path.join(os.getcwd(), "yesno.dict")
        )

        self.pocketSphinxASRLocType = pocketSphinxASR.PocketSphinxASR(
            audioInputDeviceIndex=audioInputDeviceIndex,
            audioThreshold=audioThreshold,
            timeoutLength=timeoutLength,
            lmPath=os.path.join(os.getcwd(), "loctype.lm"),
            dictPath=os.path.join(os.getcwd(), "loctype.dict")
        )

        #self.gpsScanner = gpsScanner.GPSScanner(
        #    serialPortIn=gpsPort,
        #    serialBaudIn=gpsBaud
        #)
        #self.gpsScanner.runLocate()

    def getLocationLatLong(self, locationHashIn=None):

        latitude = None
        longitude = None

        '''
        while True:

            locationHash = currentHashIn
            if not locationHash:
                locationHash = self.gpsScanner.getLocationHash()

            try:

                latitude = locationHash['latitude']
                if locationHash['latitudeDir'] == 'S':
                    latitude *= -1
                elif locationHash['latitudeDir'] == 'N':
                    latitude *= 1
                else:
                    raise ValueError('Latitude direction is invalid.')

                longitude = locationHash['longitude']
                if locationHash['longitudeDir'] == 'W':
                    longitude *= -1
                elif locationHash['longitudeDir'] == 'E':
                    longitude *= 1
                else:
                    raise ValueError('Longitude direction is invalid.')

                break

            except:
                print("Getting location coordinates . . .")

            time.sleep(1)
        '''
        latitude, longitude = (39.357513, -76.551423)
        return (latitude, longitude)

    def printAndSay(self, message):
        print(message)
        self.textToSpeech.say(message)
        self.textToSpeech.runAndWait()

    def getYesNoResponse(self, prompt):
        resp = None
        while True:
            self.printAndSay(prompt)
            for wordItem in self.pocketSphinxASRYesNo.listen().split(" "):
                if wordItem.upper() in ("YES", "NO"):
                    resp = wordItem.upper()
                    print(resp)
                    break
            if resp:
                break
            self.printAndSay(
                "I did not understand that.  " +
                "Please restate your answer."
            )

        return resp

    def resetDirections(self):
        self.locations = []
        self.directionsHash = {}

    def getStartLocation(self):

        latitude, longitude = self.getLocationLatLong()
        
        return "{},{}".format(
            str(latitude),
            str(longitude)
        )

    def getLocationFromAddress(self, addressIn):

        returnResult = None
        reqData = {
            "location": addressIn,
            "options": {
                "thumbMaps": False
            }
        }
        req = requests.post(
            (
                str(self.geocodingAPIURL) +
                "?key=" +
                str(self.directionsAPIKey)
            ),
            json=reqData
        )
        addressResp = json.loads(req.text)
        returnResult = addressResp["results"][0]["locations"][0]

        return returnResult

    def searchLocationQuery(self, query):

        latitude, longitude = self.getLocationLatLong()

        startLocation = "{},{}".format(
            str(longitude),
            str(latitude)
        )
        req = requests.get(
            (
                str(self.placeSearchAPIURL) +
                "?key=" +
                str(self.directionsAPIKey) +
                "&location=" +
                str(startLocation) +
                "&sort=distance" +
                "&q=" +
                str(query)
            )
        )

        locationResp = json.loads(req.text)
        locationResult = locationResp["results"][0]["displayString"]

        return locationResult

    def getDirectionsFromLocations(self, locationsListIn):

        returnDirections = {}
        directionsResp = None
        reqData = {
            "locations": locationsListIn
        }
        req = requests.post(
            (
                str(self.directionsAPIURL) +
                "?key=" +
                str(self.directionsAPIKey)
            ),
            json=reqData
        )
        directionsResp = json.loads(req.text)
        returnDirections = []
        for legIndex in range(0, len(directionsResp["route"]["legs"]), 1):
            legItem = directionsResp["route"]["legs"][legIndex]
            returnDirections.append(
                {
                    "maneuvers": [],
                    "visited": False
                }
            )
            for maneuverIndex in range(0, len(legItem["maneuvers"]), 1):
                maneuverItem = legItem["maneuvers"][maneuverIndex]
                maneuverHash = {
                    "narrative": maneuverItem["narrative"],
                    "coords": {
                        "lat": maneuverItem["startPoint"]["lat"],
                        "long": maneuverItem["startPoint"]["lng"]
                    },
                    "visited": False
                }
                returnDirections[legIndex]["maneuvers"].append(maneuverHash)

        return returnDirections

    def getLocationFromASR(self, prompt):

        locationAddress = None
        typePrompts = (
            "If you would like to search for a place, say \"SEARCH.\"",
            "If you would like to enter an address, say \"ADDRESS.\"",
            "If you would like to go to a saved location, say \"SAVED.\""
        )

        resp = None
        while True:
            self.printAndSay("\n".join(typePrompts))
            for wordItem in self.pocketSphinxASRLocType.listen().split(" "):
                if wordItem.upper() in ("ADDRESS", "SAVED", "SEARCH"):
                    resp = wordItem.upper()
                    print(resp)
                    break
            if resp:
                break
            self.printAndSay(
                "I did not understand that.  " +
                "Please restate your answer."
            )

        while not locationAddress:
            
            locationInput = None
            self.printAndSay(prompt)
            locationInput = self.googleASR.listen()
            if locationInput:
                print(locationInput.upper())

            if str(resp).upper() == "ADDRESS":
                locationAddress = locationInput
            elif str(resp).upper() == "SAVED":
                try:
                    name = locationInput.upper()
                    locationAddress = self.savedAddresses[name]
                except:
                    pass
            elif str(resp).upper() == "SEARCH":
                locationAddress = self.searchLocationQuery(locationInput)
            else:
                self.printAndSay(
                    "I did not understand that.  " +
                    "Please restate your answer."
                )

        return locationAddress

    def getLocationSearchList(self):

        locationsList = []
        locationsList.append(self.getStartLocation())
        prompt = "Say your first waypoint or destination."
        locationsList.append(
            self.confirmLocationResult(
                self.getLocationFromASR(prompt)
            )
        )

        while True:
            resp = self.getYesNoResponse("Do you want to enter another waypoint?")
            if str(resp).upper() == "YES":
                prompt = "Say your next waypoint or final destination."
                locationsList.append(
                    self.confirmLocationResult(
                        self.getLocationFromASR(prompt)
                    )
                )
            elif str(resp).upper() == "NO":
                break
            else:
                self.printAndSay(
                    "I did not understand that.  " +
                    "Please restate your answer."
                )

        return locationsList

    def confirmLocationResult(self, locationIn):
        
        returnLocation = locationIn
        locationResult = self.getLocationFromAddress(returnLocation)

        prompt = (
            "Please confirm the following waypoint or " +
            "destination."
        )
        self.printAndSay(prompt)

        print(
            "Original location input: " +
            str(locationIn)
        )
        print(
            "Interpreted location response: " +
            str(locationResult)
        )

        while True:
            resp = self.getYesNoResponse("Is this correct?")
            if str(resp).upper() == "NO":
                prompt = "Enter waypoint or destination." 
                returnLocation = self.confirmLocationResult(
                    self.getLocationFromASR(prompt)
                )
                break
            elif str(resp).upper() == "YES":
                break
            else:
                self.printAndSay(
                    "I did not understand that.  " +
                    "Please restate your answer."
                )

        return returnLocation

    def announceManeuverPoint(self, maneuverItemIn):

        def announceManeuverInMiles(narrativeIn, distanceInMilesIn):
            narrative = narrativeIn
            if distanceInMilesIn > 1:
                narrative = "{} in {} miles.".format(
                    narrativeIn,
                    int(distanceInMilesIn)
                )
            else:
                narrative = "{} in {} feet.".format(
                    narrativeIn,
                    int(distanceInMilesIn*5280)
                )
            self.printAndSay(narrative)

        maneuverItem = maneuverItemIn
        distanceInMiles = 10

        announceList = []
        while True:

            announce = False
            lastDistanceInMiles = distanceInMiles
            narrative = maneuverItem["narrative"]

            #currentHash = self.gpsScanner.getLocationHash()
            currentLocation = self.getLocationLatLong()
            maneuverLocation = (
                maneuverItem["coords"]["lat"],
                maneuverItem["coords"]["long"]
            )
            distanceInKm = distance.distance(
                currentLocation,
                maneuverLocation
            ).km
            distanceInMiles = distance.distance(
                currentLocation,
                maneuverLocation
            ).miles

            if (
                3 < distanceInMiles and distanceInMiles <= 10 and
                "10miles" not in announceList
            ):
                announceList.append("10miles")
                announce = True
            if (
                2 < distanceInMiles and distanceInMiles <= 3 and
                "3miles" not in announceList
            ):
                announceList.append("3miles")
                announce = True
            if (
                1 < distanceInMiles and distanceInMiles <= 2 and
                "2miles" not in announceList
            ):
                announceList.append("2miles")
                announce = True
            if (
                1000 < int(distanceInMiles*5280) and
                distanceInMiles <= 1 and
                "1mile" not in announceList
            ):
                announceList.append("1mile")
                announce = True
            if (
                500 < int(distanceInMiles*5280) and
                int(distanceInMiles*5280) <= 1000 and
                "1000feet" not in announceList
            ):
                announceList.append("1000feet")
                announce = True
            if (
                200 < int(distanceInMiles*5280) and
                int(distanceInMiles*5280) <= 500 and
                "500feet" not in announceList
            ):
                announceList.append("500feet")
                announce = True
            if (
                100 < int(distanceInMiles*5280) and
                int(distanceInMiles*5280) <= 200 and
                "200feet" not in announceList
            ):
                announceList.append("200feet")
                announce = True
            if (
                10 < int(distanceInMiles*5280) and
                int(distanceInMiles*5280) <= 100 and
                "100feet" not in announceList
            ):
                announceList.append("100feet")
                announce = True
            if int(distanceInMiles*5280) <= 10:
                announce = True

            if announce:
                announceManeuverInMiles(
                    narrative,
                    distanceInMiles
                )

            if (
                distanceInMiles > lastDistanceInMiles or
                int(distanceInMiles*5280) <= 10
            ):
                break

            time.sleep(1)
            print("Waiting for maneuver point . . .")

    def showDirections(self, locationsListIn):

        directionsList = self.getDirectionsFromLocations(locationsListIn)
        for legItem in directionsList:
            for maneuverItem in legItem["maneuvers"]:
                self.announceManeuverPoint(maneuverItem)

    def stopDirections(self):
        #self.gpsScanner.stopLocate()
        pass


if __name__ == "__main__":
    dc = DirectionsClient()
    dc.resetDirections()
    locationsList = dc.getLocationSearchList()
    dc.showDirections(locationsList)
    dc.stopDirections()
