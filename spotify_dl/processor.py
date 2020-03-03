from pathlib import Path
import librosa, librosa.display
import numpy, scipy, matplotlib.pyplot as plt, sklearn, librosa, IPython.display, urllib
import constants

class Processor:  
    def __init__(self):
        self.Y = None
        self.Sr = None

    def load_track(self):
        self.Y, self.Sr =librosa.load(constants.LOCAL_FILENAME, duration=10.0, offset=10.0)

    def get_flattened_mfcc(self):
        return librosa.feature.mfcc(y=self.Y, sr=self.Sr).flatten()

    def get_chroma_features(self):
        return librosa.feature.chroma_stft(y=self.Y, sr=self.Sr).flatten()

    def get_tempo(self):
        return round(librosa.beat.beat_track(y=self.Y, sr=self.Sr, units='time')[0])




