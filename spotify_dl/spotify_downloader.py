import spotipy
import spotipy.util as util
import spotipy.oauth2 as oauth2
import json
import requests
import constants

class SpotifyDownloader:
    def __init__(self):
        with open('passwords.json', 'r') as file: 
            passwords = json.load(file)
        CLIENT_ID = "e82e0eb0f4a846239ea74e71b554d459"
        CLIENT_SECRET = passwords['CLIENT_SECRET']

        auth = oauth2.SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        self.token = auth.get_access_token()

    def download_preview(self, url):
        # Creates the file in the working directory
        spotify_preview = requests.get(url)   
        downloaded_preview = open(constants.LOCAL_FILENAME, 'wb')
        for chunk in spotify_preview.iter_content(chunk_size=512 * 1024): 
            if chunk: # filter out keep-alive new chunks
                downloaded_preview.write(chunk)
        downloaded_preview.close()
        return url
    
    def get_artists(self, track):
        track_artists = track[constants.ARTISTS_FIELD]
        artists = []
        for artist in track_artists:
            artists.append(artist[constants.NAME_FIELD])
        return artists

    def get_playlist(self, playlist_id):
        playlist_url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'
        response = requests.get(playlist_url, headers={'Authorization': 'Bearer ' + self.token}) 
        return json.loads(response.content)

    def get_genres(self, track):
        album_id = track['album']['id']
        album_url = 'https://api.spotify.com/v1/albums/' + album_id
        response = requests.get(album_url, headers={'Authorization': 'Bearer ' + self.token}) 
        album_details = json.loads(response.content)
        genres = album_details['genres']
        if len(genres) == 0:
            genres = self.get_artist_genres(track)
        return genres
    
    def get_artist_genres(self, track):
        genres = []
        for artist in track[constants.ARTISTS_FIELD]:
            # This artist object is the simplified version that doesn't contain the artist genres    
            artist_id = artist['id']
            artist_url = 'https://api.spotify.com/v1/artists/' + artist_id
            response = requests.get(artist_url, headers={'Authorization': 'Bearer ' + self.token}) 
            artist_details = json.loads(response.content)
            genres = artist_details['genres']
            if len(genres) > 0:
                return genres     
        return genres

    def get_track_by_id(self, id):
        track_url = "https://api.spotify.com/v1/tracks/" + id
        response = requests.get(track_url, headers={'Authorization': 'Bearer ' + self.token})
        return json.loads(response.content)


