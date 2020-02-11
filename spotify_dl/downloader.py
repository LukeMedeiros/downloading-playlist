import requests
import sys
import os
from pathlib import Path
from pymongo import MongoClient
import librosa
import json
from scipy.spatial import distance
from youtube_downloader import YoutubeDownloader
from spotify_downloader import SpotifyDownloader
from processor import Processor
import constant

def delete_file(path):
    os.remove(path)

def get_artists(track_artists):
    artists = []
    for artist in track_artists:
        artists.append(artist[constant.NAME_FIELD])
    return artists

def update_track(track, song_name, artists, processor, tracks):
    if constant.NAME_FIELD not in track:
        tracks.update_one({constant.ID_FIELD: track_id}, {"$set": {constant.NAME_FIELD: song_name}}) 
    if constant.ARTISTS_FIELD not in track:
        tracks.update_one({constant.ID_FIELD: track_id}, {"$set": {constant.ARTISTS_FIELD: artists}})   
    if constant.TEMPO_FIELD not in track or constant.MFCC_FIELD not in track or constant.CHROMA_FIELD not in track:
        spotify_downloader.download_preview(track[constant.PREVIEW_URL_FIELD]) 
        processor.load_track()
    else:
        return
    if constant.TEMPO_FIELD not in track:
        tempo = processor.get_tempo()
        tracks.update_one({constant.ID_FIELD: track_id}, {"$set": {constant.TEMPO_FIELD: tempo}})                    
    if constant.MFCC_FIELD not in track:
        mfcc = processor.get_flattened_mfcc()
        tracks.update_one({constant.ID_FIELD: track_id}, {"$set": {constant.MFCC_FIELD: mfcc.tolist()}})   
    if constant.CHROMA_FIELD not in track:
        chroma = processor.get_chroma_features()
        tracks.update_one({constant.ID_FIELD: track_id}, {"$set": {constant.CHROMA_FIELD: chroma.tolist()}})
    delete_file(constant.LOCAL_FILENAME)

def create_track(processor, preview_url, spotify_download):             
    mfcc = processor.get_flattened_mfcc()
    chroma = processor.get_chroma_features()
    tempo = processor.get_tempo()
    return  {
        constant.ID_FIELD : track_id,
        constant.PREVIEW_URL_FIELD : preview_url,
        constant.NAME_FIELD : song_name,
        constant.ARTISTS_FIELD : artists, 
        constant.MFCC_FIELD : mfcc.tolist(),
        constant.CHROMA_FIELD : chroma.tolist(),
        constant.TEMPO_FIELD: tempo,
        constant.SPOTIFY_DOWNLOAD_FIELD : spotify_download
    }

def create_missing_track(track_id, song_name):
    return {
        constant.ID_FIELD : track_id,
        constant.NAME_FIELD : song_name
    }

# start
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
            track = item['track']       
            track_id = track['id']
            song_name = track[constant.NAME_FIELD]  
            artists = get_artists(track[constant.ARTISTS_FIELD])           
            if tracks.find_one({constant.ID_FIELD: track_id}) is not None:
                print("updating :" + track_id)
                update_track(tracks.find_one({constant.ID_FIELD: track_id}), song_name, artists, processor, tracks)        
            else:            
                if track[constant.PREVIEW_URL_FIELD] is not None:
                    print("creating track: " + track_id)
                    preview_url = spotify_downloader.download_preview(track[constant.PREVIEW_URL_FIELD]) 
                    spotify_download = True
                else:
                    print('missing track: ' + song_name + ' ' + track_id)
                    if missing_tracks.find_one({constant.ID_FIELD: track_id}) is None:                       
                        missing_tracks.insert_one(create_missing_track(track_id, song_name))
                    continue
                processor.load_track()
                new_track = create_track(processor, preview_url, spotify_download)
                tracks.insert_one(new_track)
                delete_file(constant.LOCAL_FILENAME)









