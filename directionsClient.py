import json
import os
import time

import pyttsx3
import requests

import configReader
import gpsScanner
import googleASR
import pocketSphinxASR


class DirectionsClient():


    configReader = None
    googleASRClient = None
    gpsScanner = None
    pocketSphinxClient = None
    textToSpeech = None

    directionsAPIURL = None
    directionsAPIKey = None
    geocodingAPIURL = None

    directionsHash = None 


    def __init__(
        self,
        configFile="config.xml",
        directionsAPIURLIn=None,
        directionsAPIKeyIn=None,
        geocodingAPIURLIn=None,
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
            self.geocodingAPIURL = geocodingAPIURL

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

        self.textToSpeech = pyttsx3.init()
        self.textToSpeech.setProperty("rate", ttsWordRate)

        self.googleASR = googleASR.GoogleASR(
            googleServiceAccountJSON=googleServiceAccountJSON,
            audioInputDeviceIndex=audioInputDeviceIndex,
            audioThreshold=audioThreshold,
            timeoutLength=timeoutLength
        )

        self.pocketSphinxASR = pocketSphinxASR.PocketSphinxASR(
            audioInputDeviceIndex=audioInputDeviceIndex,
            audioThreshold=audioThreshold,
            timeoutLength=timeoutLength
        )

        #self.gpsScanner = gpsScanner.GPSScanner(
        #    serialPortIn=gpsPort,
        #    serialBaudIn=gpsBaud
        #)
        #self.gpsScanner.runLocate()

    def getLocationLatLong(self):

        latitude = None
        longitude = None

        while True:
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

        return (latitude, longitude)

    def printAndSay(self, message):
        print(message)
        self.textToSpeech.say(message)
        self.textToSpeech.runAndWait()

    def resetDirections(self):
        self.locations = []
        self.directionsHash = {}

    def getStartLocation(self):

        self.resetDirections()
        #latitude, longitude = self.getLocationLatLong()
        latitude, longitude = (39.357513, -76.551423)
        
        return "{},{}".format(
            str(latitude),
            str(longitude)
        )

    def getLocationFromASR(self, prompt):
        location = None
        while not location:
            self.printAndSay(prompt)
            location = self.googleASR.listen()
        print(location)
        return location

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

            self.printAndSay("Do you want to enter another waypoint?")

            resp = None
            for wordItem in self.pocketSphinxASR.listen().split(" "):
                print(wordItem)
                if wordItem.upper() in ("YES", "NO"):
                    resp = wordItem.upper()
                    break

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
        reqData = {
            "location": returnLocation,
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
        locationResp = json.loads(req.text)
        locationResult = locationResp["results"][0]["locations"][0]

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

        self.printAndSay("Is this correct?")

        while True:

            resp = None
            for wordItem in self.pocketSphinxASR.listen().split(" "):
                print(wordItem)
                if wordItem.upper() in ("YES", "NO"):
                    resp = wordItem.upper()
                    break

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

    def showDirections(self, locationsListIn):

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

        for legIndex in range(0, len(directionsResp["route"]["legs"]), 1):
            legHash = directionsResp["route"]["legs"][legIndex]
            for maneuverIndex in range(0, len(legHash["maneuvers"]), 1):
                maneuverHash = legHash["maneuvers"][maneuverIndex]
                self.printAndSay(maneuverHash["narrative"])

    def stopDirections(self):
        #self.gpsScanner.stopLocate()
        pass


if __name__ == "__main__":
    dc = DirectionsClient()
    locationsList = dc.getLocationSearchList()
    dc.showDirections(locationsList)
    dc.stopDirections()
