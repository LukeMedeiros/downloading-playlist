import sys
import youtube_dl
import os
import googleapiclient.discovery
import json

class YoutubeDownloader:
    API_SERVICE_NAME = "youtube"
    API_VERSIONE = "v3"
    YDL_OPTS = {
        'outtmpl': 'preview.mp3', 
        'format': 'bestaudio/best',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    
    def __init__(self):
        with open('api_key.json') as f:
            data = json.load(f)
        developer_key = data['api-key']
        self.youtube = googleapiclient.discovery.build(self.API_SERVICE_NAME, self.API_VERSIONE, developerKey = developer_key)

    def download_song(self, url):
        try:
            youtube_dl.YoutubeDL(self.YDL_OPTS).download([url])
            return url
        except youtube_dl.utils.DownloadError:
            return False 
    
    def search(self, name, artists):
        # can make cleaner
        search_name = name
        for artist in artists:
            if artist in name:
                continue
            search_name = search_name + " " + artist
        
        search_name = search_name + " audio"
        print(search_name)
        request = self.youtube.search().list(
            q = search_name,
            part="id",
            maxResults=3
            )

        response = request.execute()
        if response['pageInfo']['totalResults'] <= 0:
            return False
        for v in response['items']:
            if v['id']['kind'] == "youtube#video":
                # getting the specific video id for each video in the playlist
                song = v
      
        print(song)
        # downloading a specific youtube video
        return 'https://www.youtube.com/watch?v='+song['id']['videoId']