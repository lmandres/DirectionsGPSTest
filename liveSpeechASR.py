import audioop
import io
import math
import os
import struct
import time

import pocketsphinx
import pyaudio

Threshold = 20

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
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

    def initializeStream(self):
        p = pyaudio.PyAudio()
        self.stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            output=False,
            frames_per_buffer=chunk,
            input_device_index=0
        )

    def record(self, firstChunk=None):

        print('Recording beginning')

        rec = []
        recResampled = []

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

        recResampled = audioop.ratecv(b"".join(rec), 2, 1, RATE, 16000, None)

        return recResampled[0]

    def translateSpeech(self, recording):

        print("Translating speech . . .")

        bytesIO = io.BytesIO(recording)
        buf = bytearray(1024)

        content = recording
        config = pocketsphinx.DefaultConfig()
        config.set_string("-hmm", os.path.join(pocketsphinx.get_model_path(), "en-us"))
        config.set_string("-lm", os.path.join(pocketsphinx.get_model_path(), "en-us.lm.bin"))
        config.set_string("-dict", os.path.join(pocketsphinx.get_model_path(), "cmudict-en-us.dict"))
        decoder = pocketsphinx.Decoder(config)

        decoder.start_utt()
        while bytesIO.readinto(buf):
            decoder.process_raw(buf, False, False)
        decoder.end_utt()

        return [seg.word for seg in decoder.seg()]

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
