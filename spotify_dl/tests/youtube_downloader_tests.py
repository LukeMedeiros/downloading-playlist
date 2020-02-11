import sys
sys.path.append(".")
import youtube_downloader

youtube_downloader = youtube_downloader.YoutubeDownloader()

url = youtube_downloader.search("The Way", ["CARSTN"])
youtube_downloader.download_song(url)