
import sys
import youtube_dl
import os
import googleapiclient.discovery
import json

with open('api_key.json') as f:
    data = json.load(f)

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = data['apiKey']
ydl_opts = {
    'outtmpl': 'songset/%(title)s-%(id)s.%(ext)s', 
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey = DEVELOPER_KEY)

# getting the contents of a specific playlist
request = youtube.playlistItems().list(
    part="contentDetails",
    playlistId="PLBY2oJTdHuT8pJN2P8URHHEmmJOu-ZLpm"
)
response = request.execute()

# getting the specific video id for each video in the playlist
for video in response['items']: 
    # downloading a specific youtube video
    youtube_dl.YoutubeDL(ydl_opts).download(['https://www.youtube.com/watch?v='+video['contentDetails']['videoId']])



    