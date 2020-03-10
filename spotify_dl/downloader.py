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
import logging


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

def get_neighbors(chroma, all_tracks):
    neighbors = []
    for compare_track in all_tracks: 
        # one feature for now will use the rest once this is implemented properly 
        dis = -distance.euclidean(chroma, compare_track[constants.CHROMA_FIELD])
        heapq.heappush(neighbors, (dis, compare_track[constants.ID_FIELD]))
        if len(neighbors) > constants.NIEGHBOURS: 
            heapq.heappop(neighbors)

    # making the list of songs not a tuple 
    neighbors_dict = {}
    for track in neighbors:
        neighbors_dict[track[1]] = track[0]
    return neighbors_dict

def update_neighbors(new_track, all_tracks, tracks_db, Processor):
    for track in all_tracks: 
        track_id = track[constants.ID_FIELD]
        neighbors = []

        # if the track is missing neighbors we need to add them for the track
        if constants.NEIGHBORS not in track:
            new_neighbors = get_neighbors(track[constants.CHROMA_FIELD], all_tracks)
            tracks_db.update_one({constants.ID_FIELD: track_id}, {"$set": {constants.NEIGHBORS: new_neighbors}})  
            continue

        for key in track[constants.NEIGHBORS]: 
            neighbors.append((track[constants.NEIGHBORS][key], key))

        neighbors.sort(key = lambda arr: arr[0])
        dis = -distance.euclidean(new_track[constants.CHROMA_FIELD], track[constants.CHROMA_FIELD])
        if dis > neighbors[0][0]: 
            neighbors.pop() 
            neighbors.append((dis, track_id))

        # making the list of songs not a tuple 
        neighbours_dict = {}
        for track in neighbors:
            neighbours_dict[track[1]] = track[0]

        tracks_db.update_one({constants.ID_FIELD: track_id}, {"$set": {constants.NEIGHBORS: neighbours_dict}})

def create_track(processor, preview_url, spotify_download, track_id, spotify_track, spotify_downloader, tracks_db, missing_track_genres, genre):             
    mfcc = processor.get_flattened_mfcc()
    chroma = processor.get_chroma_features()
    tempo = processor.get_tempo()
    song_name = spotify_track[constants.NAME_FIELD]  
    artists = spotify_downloader.get_artists(spotify_track) 
    genres = [genre] 
    # genres = spotify_downloader.get_genres(spotify_track)   
    # if len(genres) == 0:
    #     print("missing track genres: " + track_id)
    #     if missing_track_genres.find_one({constants.ID_FIELD: track_id}) is None:                       
    #             missing_track_genres.insert_one(create_missing_track(track_id, song_name))
    #     return

    # passing the genre from the playlist.json 2

    return {
        constants.ID_FIELD : track_id,
        constants.PREVIEW_URL_FIELD : preview_url,
        constants.NAME_FIELD : song_name,
        constants.ARTISTS_FIELD : artists, 
        constants.GENRES_FIELD: genres,
        constants.MFCC_FIELD : mfcc.tolist(),
        constants.CHROMA_FIELD : chroma.tolist(),
        constants.TEMPO_FIELD: tempo,
        constants.SPOTIFY_DOWNLOAD_FIELD : spotify_download
    }

def download():
    with open('passwords.json', 'r') as file: 
        passwords = json.load(file)
    with MongoClient("mongodb+srv://JustFlowAdmin:"+passwords['db_password']+"@justflow-l8dim.mongodb.net/JustFlow?retryWrites=true&w=majority") as client:
        db = client.get_database('JustFlow')
        tracks = db.test_tracks
        missing_tracks = db.missing_tracks
        missing_track_genres = db.missing_track_genres
        spotify_downloader = SpotifyDownloader()

        with open('playlists.json', 'r') as file: 
            playlists = json.load(file)

        
        for genre, playlist_ids in playlists['playlists'].items():
            for playlist_id in playlist_ids:
                count = 0
                playlist = spotify_downloader.get_playlist(playlist_id)
                for item in playlist['items']:
                    processor = Processor()
                    spotify_track = item['track']      
                    track_id = spotify_track['id']      
                    
                    if tracks.find_one({constants.ID_FIELD: track_id}) is None:
                        if spotify_track[constants.PREVIEW_URL_FIELD] is not None:
                            count +=1
                            print("creating track: " + track_id)
                            preview_url = spotify_downloader.download_preview(spotify_track[constants.PREVIEW_URL_FIELD]) 
                            spotify_download = True
                            processor.load_track()
                            new_track = create_track(processor, preview_url, spotify_download, track_id, spotify_track, spotify_downloader, tracks, missing_track_genres, genre)
                            # checking to see if the new song affects any of the neighbors from the previous songs
                            # not doing this for now 
                            # update_neighbors(new_track, list(tracks.find({})), tracks, processor)
                            tracks.insert_one(new_track)         
                            delete_file(constants.LOCAL_FILENAME)
                            if count == 50: 
                                break
                        else:
                            print('missing track: ' + spotify_track[constants.NAME_FIELD]   + ' ' + track_id)
                            if missing_tracks.find_one({constants.ID_FIELD: track_id}) is None:                       
                                missing_tracks.insert_one(create_missing_track(track_id, spotify_track[constants.NAME_FIELD]))              

if __name__ == "__main__":
    logger = logging.getLogger('downloader')
    download()









