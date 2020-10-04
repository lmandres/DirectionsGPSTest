import json
import os
import time

import pyttsx3
import requests

import gpsScanner
import googleASRRecorder
import pocketsphinx

apiURL = "http://www.mapquestapi.com/directions/v2/route"
appKey = "GGpAZjZy8IHEWmbYs4t8g0GGqB4SQkR7"

if __name__ == "__main__":

    locations = []
    directionHash = {}

    tts = pyttsx3.init()
    tts.setProperty("rate", 150)

    asrRecorder = googleASRRecorder.Recorder()

    gps = gpsScanner.GPSScanner(
        serialPortIn="/dev/ttyUSB0",
        serialBaudIn=4800
    )
    gps.runLocate()

    latitude = None
    longitude = None

    while True:
        locationHash = gps.getLocationHash()
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
            print("Getting start location . . .")

        time.sleep(1)

    locations.append(
        "{},{}".format(
            str(latitude),
            str(longitude)
        )
    )

    prompt = "Say your first waypoint or destination."
    print(prompt)
    tts.say(prompt)
    tts.runAndWait()

    location = asrRecorder.listen()
    locations.append(location)
    locationIndex = 1

    print(location)

    prompt = "Do you want to enter another waypoint?"
    print(prompt)
    tts.say(prompt)
    tts.runAndWait()

    for resp in pocketsphinx.LiveSpeech():

        print(resp)
        if str(resp).upper() == "YES":

            prompt = "Say your next waypoint or final destination."
            print(prompt)
            tts.say(prompt)
            tts.runAndWait()

            location = asrRecorder.listen()
            locations.append(location)
            locationIndex += 1

            print(location)

        elif str(resp).upper() == "NO":
            break
        else:
            print("I did not understand that.")

        prompt = "Do you want to enter another waypoint?"
        print(prompt)
        tts.say(prompt)
        tts.runAndWait()

    locationIndex = 0
    while True:

        locationIndex += 1

        if locationIndex >= len(locations):
            break

        reqData = {
            "locations": locations
        }
        req = requests.post(apiURL + "?key=" + str(appKey), json=reqData)
        directionHash = json.loads(req.text)
        directionLocations = directionHash["route"]["locations"]

        prompt = (
            "Please confirm the following waypoint or " +
            "destination."
        )

        print(prompt)
        tts.say(prompt)
        tts.runAndWait()

        print(
            "Waypoint/destination: " +
            str(locationIndex)
        )
        print(
            "Original location input: " +
            str(locations[locationIndex])
        )
        print(
            "Interpreted location response: " +
            str(directionLocations[locationIndex])
        )

        prompt = "Is this correct?"
        print(prompt)
        tts.say(prompt)
        tts.runAndWait()

        for resp in pocketsphinx.LiveSpeech():

            print(resp)
            if str(resp).upper() == "NO":
       
                prompt = "Enter waypoint or destination." 
                print(prompt)
                tts.say(prompt)
                tts.runAndWait()

                locations[locationIndex] = asrRecorder.listen()
                locationIndex -= 1

                break

            elif str(resp).upper() == "YES":
                break
            else:
                print("Invalid input.  Please reenter.")

    for legIndex in range(0, len(directionHash["route"]["legs"]), 1):
        legHash = directionHash["route"]["legs"][legIndex]
        for maneuverIndex in range(0, len(legHash["maneuvers"]), 1):
            maneuverHash = legHash["maneuvers"][maneuverIndex]
            print(maneuverHash["narrative"])
            tts.say(maneuverHash["narrative"])
            tts.runAndWait()

    gps.stopLocate()
