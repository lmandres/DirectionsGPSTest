import audioop
import io
import math
import os
import soundfile
import struct
import time
import wave

import noisereduce
import numpy
import pyaudio

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

swidth = 2
VOLUME_ADJUST = 1.0 

class Recorder:


    audioThreshold = None
    inputDeviceIndex = None
    stream = None
    timeoutLength = None


    @staticmethod
    def rms(frame):
        count = len(frame) / swidth
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(
        self,
        audioInputDeviceIndex=None,
        audioThreshold=20,
        timeoutLength=2
    ):
        self.audioThreshold = audioThreshold
        self.inputDeviceIndex = audioInputDeviceIndex
        self.timeoutLength = timeoutLength

    def initializeStream(self):
        p = pyaudio.PyAudio()
        self.stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            output=False,
            frames_per_buffer=chunk,
            input_device_index=self.inputDeviceIndex
        )

    def record(self, firstChunk=None):

        print('Recording beginning')

        returnRec = []
        rec = []

        if firstChunk:
            rec.append(firstChunk)

        current = time.time()
        end = time.time() + self.timeoutLength

        try:
            while current <= end:

                data = self.stream.read(chunk)
                if self.rms(data) >= self.audioThreshold:
                    end = time.time() + self.timeoutLength

                current = time.time()
                rec.append(data)
        except KeyboardInterrupt:
            pass

        returnRec = rec

        if VOLUME_ADJUST != 1.0:
            returnRec = self.adjustVolume(returnRec)

        returnRec = self.resample(returnRec)

        return returnRec

    def resample(self, recording):
        returnSample = None
        returnSample = audioop.ratecv(
            b"".join(recording),
            2,
            1,
            RATE,
            16000,
            None
        )
        return returnSample[0]

    def adjustVolume(self, recording):
        returnSample = []
        tempRec = numpy.fromstring(b"".join(recording), numpy.int16)
        for recChunk in tempRec:
            tempChunk = recChunk
            tempChunk *= VOLUME_ADJUST
            returnSample.append(tempChunk.astype(numpy.int16))
        return returnSample

    def saveSpeech(self, recording):
        dirPath = os.path.join(os.getcwd(), "recordings")
        fileName = os.path.join(dirPath, "utterance.wav")
        
        wavRec = wave.open(fileName, mode="wb")
        wavRec.setnchannels(1)
        wavRec.setsampwidth(2)
        wavRec.setframerate(16000)
        wavRec.writeframes(recording)

    def filterSpeech(self):
        print("Filtering speech . . .")

        dirPath = os.path.join(os.getcwd(), "recordings")
        utteranceFileName = os.path.join(dirPath, "utterance.wav")
        noiseFileName = os.path.join(dirPath, "backgroundnoise.wav")
        filteredFileName = os.path.join(dirPath, "filteredutterance.wav")

        utterance, srate = soundfile.read(utteranceFileName)
        noise, srate = soundfile.read(noiseFileName)
        filtered = noisereduce.reduce_noise(y=utterance, sr=srate, y_noise=noise)

        soundfile.write(filteredFileName, filtered, srate)
    def getRecording(self):
        dirPath = os.path.join(os.getcwd(), "recordings")
        filteredFileName = os.path.join(dirPath, "filteredutterance.wav")

        return open(filteredFileName, "rb")

    def listen(self, callback=None):
        self.initializeStream()
        print('Listening beginning')
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)
            if rms_val > self.audioThreshold:
                print("Noise detected")
                self.saveSpeech(
                    self.record(firstChunk=input)
                )
                self.filterSpeech()
                speechText = self.translateSpeech()
                self.stream.close()
                return speechText
