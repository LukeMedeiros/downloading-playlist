from pathlib import Path
from pymongo import MongoClient
from scipy.spatial import distance
from spotify_downloader import SpotifyDownloader
from processor import Processor
import constants
from scipy.spatial import distance
import heapq
import librosa
import requests
import sys
import os
import json
NIEGHBOURS = 20

def delete_file(path):
    os.remove(path)

def create_missing_track(track_id, song_name):
    return {
        constants.ID_FIELD : track_id,
        constants.NAME_FIELD : song_name
    }

def create_missing_track_genres(track_id, song_name):
    return {
        constants.ID_FIELD : track_id,
        constants.NAME_FIELD : song_name
    }

def get_neighbors(processor, all_tracks):
    neighbors = []
    for compare_track in all_tracks: 
        # one feature for now will use the rest once this is implemented properly 
        dis = -distance.euclidean(processor.chroma, compare_track['chroma'])
        heapq.heappush(neighbors, (dis, compare_track['_id']))
        if len(neighbors) > NIEGHBOURS: 
            heapq.heappop(neighbors)

    # making the list of songs not a tuple 
    neighbors_dict = {}
    for track in neighbors:
        neighbors_dict[track[1]] = track[0]
    return neighbors_dict

def update_neighbors(new_track, all_tracks, tracks_db):
    for track in all_tracks: 
        neighbors = []
        for key in track['neighbors']: 
            neighbors.append((track['neighbors'][key], key))
        neighbors.sort(key = lambda arr: arr[0])
        dis = -distance.euclidean(new_track['chroma'], track['chroma'])
        if dis > neighbors[0][0]: 
            neighbors.pop() 
            neighbors.append((dis, track['_id']))

        # making the list of songs not a tuple 
        neighbours_dict = {}
        for track in neighbors:
            neighbours_dict[track[1]] = track[0]
        tracks_db.update_one({constants.ID_FIELD: track['_id']}, {"$set": {constants.NEIGHBORS: neighbours_dict}})

def create_track(processor, preview_url, spotify_download, track_id, spotify_track, spotify_downloader, tracks_db, missing_track_genres):             
    mfcc = processor.get_flattened_mfcc()
    chroma = processor.get_chroma_features()
    tempo = processor.get_tempo()
    song_name = spotify_track[constants.NAME_FIELD]  
    artists = spotify_downloader.get_artists(spotify_track) 
    genres = spotify_downloader.get_genres(spotify_track)    
    if len(genres) == 0:
        print("missing track genres: " + track_id)
        if missing_track_genres.find_one({constants.ID_FIELD: track_id}) is None:                       
                missing_track_genres.insert_one(create_missing_track(track_id, song_name))
        return
    neighbors = get_neighbors(processor, list(tracks_db.find({})))
    return {
        constants.ID_FIELD : track_id,
        constants.PREVIEW_URL_FIELD : preview_url,
        constants.NAME_FIELD : song_name,
        constants.ARTISTS_FIELD : artists, 
        constants.GENRES_FIELD: genres,
        constants.MFCC_FIELD : mfcc.tolist(),
        constants.CHROMA_FIELD : chroma.tolist(),
        constants.TEMPO_FIELD: tempo,
        constants.SPOTIFY_DOWNLOAD_FIELD : spotify_download, 
        constants.NEIGHBORS : neighbors
    }

def download():
    with open('passwords.json', 'r') as file: 
        passwords = json.load(file)
    with MongoClient("mongodb+srv://JustFlowAdmin:"+passwords['db_password']+"@justflow-l8dim.mongodb.net/JustFlow?retryWrites=true&w=majority") as client:
        db = client.get_database('JustFlow')
        tracks = db.tracks
        missing_tracks = db.missing_tracks
        missing_track_genres = db.missing_track_genres
        spotify_downloader = SpotifyDownloader()
        processor = Processor()

        with open('playlists.json', 'r') as file: 
            playlists = json.load(file)

        
        for playlist_id in playlists['playlists']:
            playlist = spotify_downloader.get_playlist(playlist_id)
            for item in playlist['items']:
                spotify_track = item['track']      
                track_id = spotify_track['id']      
                
                if tracks.find_one({constants.ID_FIELD: track_id}) is None:
                    if spotify_track[constants.PREVIEW_URL_FIELD] is not None:
                        print("creating track: " + track_id)
                        preview_url = spotify_downloader.download_preview(spotify_track[constants.PREVIEW_URL_FIELD]) 
                        spotify_download = True
                        processor.load_track()
                        new_track = create_track(processor, preview_url, spotify_download, track_id, spotify_track, spotify_downloader, tracks, missing_track_genres)
                        # checking to see if the new song affects any of the neighbors from the previous songs
                        update_neighbors(new_track, list(tracks.find({})), tracks)
                        tracks.insert_one(new_track)         
                        delete_file(constants.LOCAL_FILENAME)
                    else:
                        print('missing track: ' + spotify_track[constants.NAME_FIELD]   + ' ' + track_id)
                        if missing_tracks.find_one({constants.ID_FIELD: track_id}) is None:                       
                            missing_tracks.insert_one(create_missing_track(track_id, spotify_track[constants.NAME_FIELD]))              

if __name__ == "__main__":
    download()









