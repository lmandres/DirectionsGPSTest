import audioop
import io
import math
import os
import struct
import time

import pyaudio

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
swidth = 2


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

        rec = []
        recResampled = []

        if firstChunk:
            rec.append(firstChunk)

        current = time.time()
        end = time.time() + self.timeoutLength

        while current <= end:

            data = self.stream.read(chunk)
            if self.rms(data) >= self.audioThreshold:
                end = time.time() + self.timeoutLength

            current = time.time()
            rec.append(data)

        recResampled = audioop.ratecv(b"".join(rec), 2, 1, RATE, 16000, None)

        return recResampled[0]

    def translateSpeech(self, recording):
        print("Translating speech . . .")

    def listen(self, callback=None):
        self.initializeStream()
        print('Listening beginning')
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)
            if rms_val > self.audioThreshold:
                print("Noise detected")
                speechText = self.translateSpeech(
                    self.record(firstChunk=input)
                )
                self.stream.close()
                return speechText
