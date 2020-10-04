import json
import time

import pyttsx3
import requests

import gpsScanner

apiURL = "http://www.mapquestapi.com/directions/v2/route"
appKey = "GGpAZjZy8IHEWmbYs4t8g0GGqB4SQkR7"


if __name__ == "__main__":

    locations = []
    directionHash = {}

    ttsEngine = pyttsx3.init()
    ttsEngine.setProperty("rate", 150)

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

    prompt = (
        "Input first waypoint or destination."
    )
    locationIndex = 0
    while True:

        print(prompt)
        ttsEngine.say(prompt)
        ttsEngine.runAndWait()

        print("Enter Ctrl-C at prompt to finish.")

        try:
            location = input("Location: ")
            locations.append(location)
            locationIndex += 1
        except KeyboardInterrupt:
            break

        prompt = (
            "Input next waypoint or final destination."
        )

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
        ttsEngine.say(prompt)
        ttsEngine.runAndWait()

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

        while True:
            resp = input("Is this correct [y/n]: ")
            if resp.upper() == "N":
       
                prompt = "Enter waypoint or destination." 
                print(prompt)
                ttsEngine.say(prompt)
                ttsEngine.runAndWait()

                locations[locationIndex] = input("Location: ")
                locationIndex -= 1

                break

            elif resp.upper() == "Y":
                break
            else:
                print("Invalid input.  Please reenter.")

    for legIndex in range(0, len(directionHash["route"]["legs"]), 1):
        legHash = directionHash["route"]["legs"][legIndex]
        print(legHash)
        for maneuverIndex in range(0, len(legHash["maneuvers"]), 1):
            maneuverHash = legHash["maneuvers"][maneuverIndex]
            print(maneuverHash["narrative"])
            ttsEngine.say(maneuverHash["narrative"])
            ttsEngine.runAndWait()

    gps.stopLocate()
