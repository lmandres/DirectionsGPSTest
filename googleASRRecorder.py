import math
import struct
import time

import pyaudio

from google.cloud import speech

Threshold = 10

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
swidth = 2

TIMEOUT_LENGTH = 2

class Recorder:

    speechClient = None
    stream = None

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

    def __init__(self):
        self.speechClient = speech.SpeechClient.from_service_account_json(
            "service_account_file.json"
        )

    def initializeStream(self):
        p = pyaudio.PyAudio()
        self.stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            output=False,
            frames_per_buffer=chunk
        )

    def record(self, firstChunk=None):

        print('Recording beginning')

        rec = []
        if firstChunk:
            rec.append(firstChunk)

        current = time.time()
        end = time.time() + TIMEOUT_LENGTH

        while current <= end:

            data = self.stream.read(chunk)
            if self.rms(data) >= Threshold:
                end = time.time() + TIMEOUT_LENGTH

            current = time.time()
            rec.append(data)

        return rec

    def translateSpeech(self, recording):

        print("Translating speech . . .")
        transcript = None

        content = b"".join(recording)
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US"
        )
        resp = self.speechClient.recognize(
            request={
                "config": config,
                "audio": audio
            }
        )

        if resp.results:
            result = resp.results[0]
            transcript = result.alternatives[0].transcript

        return transcript

    def listen(self, callback=None):
        self.initializeStream()
        print('Listening beginning')
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)
            if rms_val > Threshold:
                print("Noise detected")
                speechText = self.translateSpeech(
                    self.record(firstChunk=input)
                )
                self.stream.close()
                return speechText
