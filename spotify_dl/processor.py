from pathlib import Path
import librosa, librosa.display
import numpy, scipy, matplotlib.pyplot as plt, sklearn, librosa, IPython.display, urllib
import constants

class Processor:  
    def __init__(self):
        self.Y = None
        self.Sr = None
        self.mfcc = None
        self.chroma = None
        self.tempo = None

    def load_track(self):
        self.Y, self.Sr =librosa.load(constants.LOCAL_FILENAME, duration=10.0, offset=10.0)

    def get_flattened_mfcc(self):
        self.mfcc = librosa.feature.mfcc(y=self.Y, sr=self.Sr).flatten()
        return self.mfcc

    def get_chroma_features(self):
        self.chroma = librosa.feature.chroma_stft(y=self.Y, sr=self.Sr).flatten()
        return self.chroma

    def get_tempo(self):
        self.tempo = librosa.beat.beat_track(y=self.Y, sr=self.Sr, units='time')[0]
        return self.tempo





