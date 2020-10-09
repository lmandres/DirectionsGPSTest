from xml.etree import ElementTree


class ConfigReader():


    configXML = None


    def __init__(self, fileName="config.xml"):
        self.configXML = ElementTree.parse(fileName)

    def getTextByXPath(self, xpath):
        returnValue = None
        try:
            returnValue = self.configXML.find(xpath).text
        except:
            pass
        return returnValue

    def getDirectionsAPIURL(self):
        return self.getTextByXPath(
            ".//DirectionsAPISettings/DirectionsAPIURL"
        )

    def getDirectionsAPIKey(self):
        return self.getTextByXPath(".//DirectionsAPISettings/APIKey")

    def getGeocodingAPIURL(self):
        return self.getTextByXPath(
            ".//DirectionsAPISettings/GeocodingAPIURL"
        )

    def getGPSDevicePort(self):
        return self.getTextByXPath(".//GPSSettings/Port")

    def getGPSDeviceBaud(self):
        returnValue = None
        try:
            returnValue = int(
                self.getTextByXPath(".//GPSSettings/Baud")
            )
        except:
            pass
        return returnValue

    def getAudioInputDeviceIndex(self):
        returnValue = None
        try:
            returnValue = int(
                self.getTextByXPath(".//SpeechToTextSettings/InputDeviceIndex")
            )
        except:
            pass
        return returnValue

    def getAudioThreshold(self):
        returnValue = None
        try:
            returnValue = int(
                self.getTextByXPath(".//SpeechToTextSettings/AudioThreshold")
            )
        except:
            pass
        return returnValue

    def getTimeoutLength(self):
        returnValue = None
        try:
            returnValue = int(
                self.getTextByXPath(".//SpeechToTextSettings/TimeoutLength")
            )
        except:
            pass
        return returnValue

    def getGoogleServiceAccountJSONFilePath(self):
        return self.getTextByXPath(
            ".//GoogleSpeechClientSettings/ServiceAccountJSON"
        )

    def getTextToSpeechWordRate(self):
        returnValue = None
        try:
            returnValue = int(
                self.getTextByXPath(".//TextToSpeechSettings/WordRate")
            )
        except:
            pass
        return returnValue
