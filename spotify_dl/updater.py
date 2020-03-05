import requests
import sys
import os
from pathlib import Path
from pymongo import MongoClient
import librosa
import json
from scipy.spatial import distance
import numpy as np
from spotify_downloader import SpotifyDownloader
from processor import Processor
import constants
from scipy.spatial import distance
import heapq

NIEGHBOURS = 20


class Updater:
    def __init__(self):
        self.processor = Processor()
        self.spotify_downloader = SpotifyDownloader()

    def delete_file(self, path):
        os.remove(path)

    def get_artists(self, track_artists):
        artists = []
        for artist in track_artists:
            artists.append(artist[constants.NAME_FIELD])
        return artists

    def update_track(self, db_track_id, tracks):
        spotify_track = self.spotify_downloader.get_track_by_id(db_track_id)
        if constants.NAME_FIELD not in db_track:
            song_name = spotify_track[constants.NAME_FIELD]  
            tracks.update_one({constants.ID_FIELD: db_track_id}, {"$set": {constants.NAME_FIELD: song_name}}) 

        if constants.ARTISTS_FIELD not in db_track:
            artists = self.get_artists(spotify_track[constants.ARTISTS_FIELD])
            tracks.update_one({constants.ID_FIELD: db_track_id}, {"$set": {constants.ARTISTS_FIELD: artists}}) 

        if constants.GENRES_FIELD not in db_track:
            genres = spotify_downloader.get_genres(spotify_track)
            print(db_track_id + " , " + str(genres))
            tracks.update_one({constants.ID_FIELD: db_track_id}, {"$set": {constants.GENRES_FIELD: genres}})

        if constants.TEMPO_FIELD not in db_track or constants.MFCC_FIELD not in db_track or constants.CHROMA_FIELD not in db_track:
            spotify_downloader.download_preview(db_track[constants.PREVIEW_URL_FIELD]) 
            self.processor.load_track()
        else:
            return

        if constants.TEMPO_FIELD not in db_track:
            tempo = self.processor.get_tempo()
            tracks.update_one({constants.ID_FIELD: db_track_id}, {"$set": {constants.TEMPO_FIELD: tempo}})  
                         
        if constants.MFCC_FIELD not in db_track:
            mfcc = self.processor.get_flattened_mfcc()
            tracks.update_one({constants.ID_FIELD: db_track_id}, {"$set": {constants.MFCC_FIELD: mfcc.tolist()}})   
            
        if constants.CHROMA_FIELD not in db_track:
            chroma = self.processor.get_chroma_features()
            tracks.update_one({constants.ID_FIELD: db_track_id}, {"$set": {constants.CHROMA_FIELD: chroma.tolist()}})
        self.delete_file(constants.LOCAL_FILENAME)

    def update_neighbours(self, seed_track, all_tracks, tracks_db, feature):
        neighbours = []
        for compare_track in all_tracks: 
            # one feature for now will use the rest once this is implemented properly 
            dis = -distance.euclidean(seed_track[feature], compare_track[feature])
            if seed_track['_id'] != compare_track['_id']: 
                heapq.heappush(neighbours, (dis, compare_track['_id']))
            if len(neighbours) > NIEGHBOURS: 
                heapq.heappop(neighbours)

        # making the list of songs not a tuple 
        neighbours_dict = {}
        for track in neighbours:
            neighbours_dict[track[1]] = track[0]
        tracks_db.update_one({constants.ID_FIELD: seed_track['_id']}, {"$set": {feature + '_neighbors': neighbours_dict}})

    def update_neighbours_combined(self, seed_track, tracks_db):
        neighbours = []
        ranged_tracks = []
        tempo_range = 1
        # increasing the tempo until we have 40 tracks returned from the query 
        while len(ranged_tracks) < 40: 
            tempo_range = tempo_range * 2
            ranged_tracks = list(tracks_db.find({ 'tempo' : { '$gt' : seed_track['tempo'] - tempo_range, '$lt': seed_track['tempo'] + tempo_range }}))
        
        for compare_track in ranged_tracks: 
            features = ['mfcc', 'chroma'] 
            dis = 0 
            seed_normalize = []
            compare_normalize = []
            for feature in features: 
                # one feature for now will use the rest once this is implemented properly 
                seed_normalize = seed_track[feature] / np.linalg.norm(seed_track[feature])
                compare_normalize = compare_track[feature] / np.linalg.norm(compare_track[feature])
                dis += -distance.euclidean(seed_normalize, compare_normalize)
            if seed_track['_id'] != compare_track['_id']: 
                heapq.heappush(neighbours, (dis, compare_track['_id']))
            if len(neighbours) > NIEGHBOURS: 
                heapq.heappop(neighbours)
        # making the list of songs not a tuple 
        neighbours_dict = {}
        for track in neighbours:
            neighbours_dict[track[1]] = track[0]
        print(seed_track['_id'])
        tracks_db.update_one({constants.ID_FIELD: seed_track['_id']}, {"$set": {constants.COMBINED_NEIGHBORS: neighbours_dict}})
        tracks_db.update_one({constants.ID_FIELD: seed_track['_id']}, {"$unset": {'combined_features': ''}})

if __name__ == "__main__":
    updater = Updater()
    with open('passwords.json', 'r') as file: 
        passwords = json.load(file)
    with MongoClient("mongodb+srv://JustFlowAdmin:"+passwords['db_password']+"@justflow-l8dim.mongodb.net/JustFlow?retryWrites=true&w=majority") as client:
        db = client.get_database('JustFlow')
        tracks = db.test_tracks_genre_focus
        spotify_downloader = SpotifyDownloader()
        all_tracks = list(tracks.find({}))
        for db_track in all_tracks:
            # updater.update_track(db_track['_id'], tracks)
            # initial algorithm just uses mfcc to find the KNN  
            # updater.update_neighbours(db_track, all_tracks, tracks, 'mfcc')
            # combining mfcc, chroma and onset to find the nearest neighbors 
            updater.update_neighbours_combined(db_track, tracks)
