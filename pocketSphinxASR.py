from baseRecorder import Recorder
import io
import os

import pocketsphinx


class PocketSphinxASR(Recorder):


    dictPath = None
    lmPath = None
    speechClient = None


    def __init__(self, *args, **kwargs):
        if "dictPath" in kwargs.keys():
            self.dictPath = kwargs.pop("dictPath")
        if "lmPath" in kwargs.keys():
            self.lmPath = kwargs.pop("lmPath")
        super().__init__(*args, **kwargs)

    def translateSpeech(self, recording):
        super().translateSpeech(recording)
        bytesIO = io.BytesIO(recording)
        buf = bytearray(1024)

        decoder = pocketsphinx.Pocketsphinx(
            lm=self.lmPath,
            dict=self.dictPath,
            verbose=False
        )

        decoder.start_utt()
        while bytesIO.readinto(buf):
            decoder.process_raw(buf, False, False)
        decoder.end_utt()

        return " ".join([seg.word for seg in decoder.seg()])
