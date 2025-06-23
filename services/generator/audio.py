import os
import gtts
from datetime import datetime

AUDIO_DIR = 'anki_audio'
AUDIO_FILENAME = "{}_{}"


class AudioGenerator:
    def __init__(self, path):
        self.path = path
        self.language = 'en'
        self.audio_tag = '[sound:{audio_filename}]'
        os.makedirs(AUDIO_DIR, exist_ok=True)

    def __set_audio_filaneme(self, name):
        filename = AUDIO_FILENAME.format(
            name, datetime.now().strftime('%d_%M_%Y')
        )

        return filename

    def audio_generator(self, card):
        tts = gtts.gTTS(card.word, self.language, tld='com')

        self.__set_audio_filaneme(name=card.word)

        tts.save(self.path)



