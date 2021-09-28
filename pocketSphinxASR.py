from baseRecorder import Recorder
import io
import os

import pocketsphinx


class PocketSphinxASR(Recorder):


    hmmPath = None
    lmPath = None
    dictPath = None
    speechClient = None


    def __init__(self, *args, **kwargs):
        if "hmmPath" in kwargs.keys():
            self.hmmPath = kwargs.pop("hmmPath")
        if "lmPath" in kwargs.keys():
            self.lmPath = kwargs.pop("lmPath")
        if "dictPath" in kwargs.keys():
            self.dictPath = kwargs.pop("dictPath")
        super().__init__(*args, **kwargs)

    def translateSpeech(self):
        print("Translating speech . . .")

        bytesIO = self.getRecording()
        buf = bytearray(1024)

        decoder = pocketsphinx.Pocketsphinx(
            hmm=self.hmmPath,
            lm=self.lmPath,
            dict=self.dictPath,
            verbose=False
        )

        decoder.start_utt()
        while bytesIO.readinto(buf):
            decoder.process_raw(buf, False, False)
        decoder.end_utt()

        return " ".join([seg.word for seg in decoder.seg()])
