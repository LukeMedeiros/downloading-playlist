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

NIEGHBOURS = 5


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

    def update_neighbours(self, seed_track, all_tracks, tracks_db):
        # if constants.EUCLIDEAN_DIST not in seed_track: 
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
        tracks_db.update_one({constants.ID_FIELD: seed_track['_id']}, {"$set": {constants.EUCLIDEAN_DIST: neighbours_dict}})
        print("track id: ", seed_track['_id'])

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

if __name__ == "__main__":
    updater = Updater()
    with open('passwords.json', 'r') as file: 
        passwords = json.load(file)
    with MongoClient("mongodb+srv://JustFlowAdmin:"+passwords['db_password']+"@justflow-l8dim.mongodb.net/JustFlow?retryWrites=true&w=majority") as client:
        db = client.get_database('JustFlow')
        tracks = db.tracks
        spotify_downloader = SpotifyDownloader()
        all_tracks = tracks.find({})
        for db_track in all_tracks:
            print(db_track['_id'])
            # updater.update_track(db_track['_id'], tracks)
            try: 
                updater.update_neighbours(db_track, all_tracks, tracks)
            except Exception as e:
                print(e) 
