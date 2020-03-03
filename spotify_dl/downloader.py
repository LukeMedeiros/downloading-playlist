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

def delete_file(path):
    os.remove(path)

def get_artists(track_artists):
    artists = []
    for artist in track_artists:
        artists.append(artist[constants.NAME_FIELD])
    return artists

def create_track(processor, preview_url, spotify_download, track_id, spotify_track, spotify_downloader):             
    mfcc = processor.get_flattened_mfcc()
    chroma = processor.get_chroma_features()
    tempo = processor.get_tempo()
    song_name = spotify_track[constants.NAME_FIELD]  
    artists = get_artists(spotify_track[constants.ARTISTS_FIELD]) 
    genres = spotify_downloader.get_genres(spotify_track)    
    return  {
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

def create_missing_track(track_id, song_name):
    return {
        constants.ID_FIELD : track_id,
        constants.NAME_FIELD : song_name
    }

def download():
    with open('passwords.json', 'r') as file: 
        passwords = json.load(file)
    with MongoClient("mongodb+srv://JustFlowAdmin:"+passwords['db_password']+"@justflow-l8dim.mongodb.net/JustFlow?retryWrites=true&w=majority") as client:
        db = client.get_database('JustFlow')
        tracks = db.tracks
        missing_tracks = db.missing_tracks
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
                        new_track = create_track(processor, preview_url, spotify_download, track_id, spotify_track, spotify_downloader)
                        tracks.insert_one(new_track)
                        delete_file(constants.LOCAL_FILENAME)
                    else:
                        print('missing track: ' + spotify_track[constants.NAME_FIELD]   + ' ' + track_id)
                        if missing_tracks.find_one({constants.ID_FIELD: track_id}) is None:                       
                            missing_tracks.insert_one(create_missing_track(track_id, spotify_track[constants.NAME_FIELD]  ))
                   

if __name__ == "__main__":
    download()









