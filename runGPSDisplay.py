from io import BytesIO
import json
import math
import time

import pygame
import requests

import gpsScanner


if __name__ == '__main__':

    def getMapImg(latitude, longitude):

        url = (
            "http://10.0.0.245:8080/styles/klokantech-basic/static/" +
            str(longitude) + "," + str(latitude) + ",15/" +
            str(display_width) + "x" + str(display_height) +
	    ".png"
        )
        print(url)
        req = requests.get(url)
        mapImg = pygame.image.load(BytesIO(req.content))

        return mapImg	


    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    font = pygame.font.Font(None, 36)

    display_width = screen.get_width()
    display_height = screen.get_height()

    prevTimestamp = None
    locationHash = {}

    gpsScanner = gpsScanner.GPSScanner(
        serialPortIn="/dev/ttyUSB0",
        serialBaudIn=4800
    )
    gpsScanner.runLocate()

    done = False
    try:

        while not done:

            try:
                locationHash = gpsScanner.getLocationHash()
            except Exception as ex:
                screen.fill((0, 0, 0))
                text = font.render(str(ex), False, (255, 255, 255))
                screen.blit(text, [0, 0])
            except KeyboardInterrupt as ki:
                done = True

            if (
                locationHash and
                'timestamp' in locationHash.keys() and
                'date' in locationHash.keys() and
                locationHash['timestamp'] != None and
                locationHash['date'] != None and
                locationHash['timestamp'] != prevTimestamp
            ):

                try:

                    print(locationHash)
                    print(done)

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

                    mapImg = getMapImg(
                        latitude,
                        longitude
                    )
                    pygame.draw.circle(mapImg, (0, 0, 255), (round(display_width/2), round(display_height/2)), 10, 2) 
                    screen.blit(mapImg, (0, 0))
                except Exception as ex:
                    screen.fill((0, 0, 0))
                    text = font.render(str(ex), False, (255, 255, 255))
                    screen.blit(text, [0, 0])
                except KeyboardInterrupt as ki:
                    done = True


            pygame.display.flip()
            time.sleep(1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    done = True


    finally:
    	gpsScanner.stopLocate()
    	pygame.quit()

    raise SystemExit
