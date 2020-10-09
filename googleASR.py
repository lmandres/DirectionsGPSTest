from baseRecorder import Recorder

from google.cloud import speech


class GoogleASR(Recorder):

    speechClient = None

    def __init__(self, *args, **kwargs):
        googleServiceAccountJSON = kwargs.pop("googleServiceAccountJSON")
        self.speechClient = speech.SpeechClient.from_service_account_json(
            googleServiceAccountJSON
        )
        super().__init__(*args, **kwargs)

    def translateSpeech(self, recording):
        super().translateSpeech(recording)
        transcript = None

        content = recording
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
