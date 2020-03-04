from pathlib import Path
import librosa, librosa.display
import numpy, scipy, matplotlib.pyplot as plt, sklearn, librosa, IPython.display, urllib
import constants
from scipy.spatial import distance
import heapq

NIEGHBOURS = 5

class Processor:  
    def __init__(self):
        self.Y = None
        self.Sr = None

    def load_track(self):
        self.Y, self.Sr =librosa.load(constants.LOCAL_FILENAME, duration=10.0, offset=10.0)

    def get_flattened_mfcc(self):
        self.mfcc = librosa.feature.mfcc(y=self.Y, sr=self.Sr).flatten()
        return self.mfcc

    def get_chroma_features(self):
        self.chroma = librosa.feature.chroma_stft(y=self.Y, sr=self.Sr).flatten()
        return self.chroma

    def get_tempo(self):
        self.tempo = librosa.beat.beat_track(y=self.Y, sr=self.Sr, units='time')
        return self.tempo

    def nearest_neighbours(self, seed_track, all_tracks):
        neighbours = []
        # euclidean = {}
        for track in all_tracks: 
            # one feature for now will use the rest once this is implemented properly 
            dis = -distance.euclidean(seed_track['chroma'], track['chroma'])
            # euclidean[track['_id']] = dis
            heapq.heappush(neighbours, (dis, track))
            if len(neighbours) > NIEGHBOURS: 
                heapq.heappop(neighbours)
        # making the list of songs not a tuple 
        neighbours_dict = {}
        for track in neighbours:
            neighbours_dict[track[1]['_id']] = track[0]
        return neighbours_dict





