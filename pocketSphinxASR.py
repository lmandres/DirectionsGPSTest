from baseRecorder import Recorder
import io
import os

import pocketsphinx


class PocketSphinxASR(Recorder):


    speechClient = None


    def translateSpeech(self, recording):
        super().translateSpeech(recording)
        bytesIO = io.BytesIO(recording)
        buf = bytearray(1024)

        decoder = pocketsphinx.Pocketsphinx(
            lm=os.path.join(os.getcwd(), "yesno.lm"),
            dict=os.path.join(os.getcwd(), "yesno.dict"),
            verbose=False
        )

        decoder.start_utt()
        while bytesIO.readinto(buf):
            decoder.process_raw(buf, False, False)
        decoder.end_utt()

        return " ".join([seg.word for seg in decoder.seg()])
