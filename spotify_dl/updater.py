import requests
import sys
import os
from pathlib import Path
from pymongo import MongoClient
import librosa
import json
from scipy.spatial import distance
from spotify_downloader import SpotifyDownloader
from processor import Processor
import constants
from scipy.spatial import distance
import heapq

NIEGHBOURS = 20

import logging
from logging.handlers import RotatingFileHandler

class Updater:
    def __init__(self):

        self.logger = logging.getLogger('Updater')
        self.logger.setLevel(logging.INFO)
        handler = RotatingFileHandler('updater_logs/info.log')
        self.logger.addHandler(handler)
        self.processor = Processor()
        self.spotify_downloader = SpotifyDownloader()

    def delete_file(self, path):
        os.remove(path)

    def update_track(self, db_track_id, tracks):
        spotify_track = self.spotify_downloader.get_track_by_id(db_track_id)
        song_name = spotify_track[constants.NAME_FIELD]  
        if constants.NAME_FIELD not in db_track:
            tracks.update_one({constants.ID_FIELD: db_track_id}, {"$set": {constants.NAME_FIELD: song_name}}) 

        artists = []
        if constants.ARTISTS_FIELD not in db_track:
            artists = self.spotify_downloader.get_artists(spotify_track)
            tracks.update_one({constants.ID_FIELD: db_track_id}, {"$set": {constants.ARTISTS_FIELD: artists}}) 

        genres = self.spotify_downloader.get_genres(spotify_track)
        if len(genres) == 0:
            self.logger.info(song_name + " , " + db_track_id + " , " + str(genres))
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

    def update_neighbours(self, seed_track, all_tracks, tracks_db):
        neighbours = []
        for compare_track in all_tracks: 
            # one feature for now will use the rest once this is implemented properly 
            dis = -distance.euclidean(seed_track['chroma'], compare_track['chroma'])
            if seed_track['_id'] != compare_track['_id']: 
                heapq.heappush(neighbours, (dis, compare_track['_id']))
            if len(neighbours) > NIEGHBOURS: 
                heapq.heappop(neighbours)

        # making the list of songs not a tuple 
        neighbours_dict = {}
        for track in neighbours:
            neighbours_dict[track[1]] = track[0]
        tracks_db.update_one({constants.ID_FIELD: seed_track['_id']}, {"$set": {constants.NEIGHBORS: neighbours_dict}})

if __name__ == "__main__":
    updater = Updater()
    with open('passwords.json', 'r') as file: 
        passwords = json.load(file)
    with MongoClient("mongodb+srv://JustFlowAdmin:"+passwords['db_password']+"@justflow-l8dim.mongodb.net/JustFlow?retryWrites=true&w=majority") as client:
        db = client.get_database('JustFlow')
        tracks = db.test_tracks
        spotify_downloader = SpotifyDownloader()
        all_tracks = list(tracks.find({}))
        for db_track in all_tracks:
            updater.update_track(db_track['_id'], tracks)
            updater.update_neighbours(db_track, all_tracks, tracks)
