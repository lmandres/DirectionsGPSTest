from io import BytesIO
import json
import math
import time

import pygame
import requests

import gpsScanner


if __name__ == '__main__':

    def getMapImg(xtile, ytile, zoom):

        url = (
            "http://c.tile.openstreetmap.org/{}/{}/{}.png".format(
                zoom, xtile, ytile
            )
        )
        print(url)
        req = requests.get(url)
        mapImg = pygame.image.load(BytesIO(req.content))

        return mapImg

    def deg2TileNum(lat_deg, lon_deg, zoom):

        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        
        return (xtile, ytile)

    def tileNum2Deg(xtile, ytile, zoom):

        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)

        return (lat_deg, lon_deg)


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

                    zoom = 5
                    xtile, ytile = deg2TileNum(latitude, longitude, zoom)
                    mapImg = getMapImg(
                        xtile, ytile, zoom
                    )
                    pygame.draw.circle(
                        mapImg,
                        (0, 0, 255),
                        (
                            round(display_width/2),
                            round(display_height/2)
                        ),
                        10,
                        2
                    ) 
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
