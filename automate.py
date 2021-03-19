from secrets import spotify_token
from secrets import spotify_userid
from secrets import youtube_client_id
from secrets import youtube_client_secret
import youtube_dl
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json
import requests
import os

s_token = spotify_token
s_uid = spotify_userid
all_tracks_information = {}
all_playlists={}
#getting liked videos from user
def gettingLikedVideos():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "yt_secretfile2.json"
    # Get credentials and create an API client
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()

    # from the Youtube DATA API
    youtube_client = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)
    request = youtube_client.videos().list(
        part="snippet,contentDetails,statistics",
        myRating="like"
    )
    # response_file = request.execute()
    getTrackInfo(request.execute())

def getTrackInfo(response_file):
    for item in response_file["items"]:
        video_title = item["snippet"]["title"]
        youtube_url = "https://www.youtube.com/watch?v={}".format(
            item["id"])
        video = youtube_dl.YoutubeDL({}).extract_info(
            youtube_url, download=False)
        song_name = video["track"]
        artist = video["artist"]
        if song_name is not None and artist is not None:
            # save all important info and skip any missing song and artist
            all_tracks_information[video_title] = {
                "youtube_url": youtube_url,
                "song_name": song_name,
                "artist": artist,

                # add the uri, easy to get song to put into playlist
                "spotify_uri": getSpotifyUri(song_name, artist)
            }


#getting all playlists from user
def getPlaylists():
    query = "https://api.spotify.com/v1/users/{}/playlists".format(s_uid);
    response = requests.get(query,
                            headers={
                                "Content-type": "application/json",
                                "Authorization": "Bearer {}".format(s_token)
                            })
    response_json = response.json()
    i = 1
    for item in response_json["items"]:
        all_playlists[i]= {
            "name_of_playlist" : item["name"],
            "playlist_id" : item["id"],
        }
        i = i+1
    return all_playlists
#creating a playlist
def createPlaylist(playlist_name):
    query = "https://api.spotify.com/v1/users/{}/playlists".format(s_uid);
    r_body = {
        "name":playlist_name,
        "description":"First Spotify automation",
        "public":True
    }
    request_body = json.dumps(r_body);
    respone = requests.post(query, data=request_body,
                            headers = {
                                "Content-type": "application/json",
                                "Authorization": "Bearer {}".format(s_token)
                            })
    respone_json = respone.json()
    return respone_json["id"];

#get spotify uri song
def getSpotifyUri(song_name,artist):
    query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
        song_name,
        artist
    )
    respone = requests.get(query,
                            headers={
                                "Content-type": "application/json",
                                "Authorization": "Bearer {}".format(s_token)
                            })
    respone_json = respone.json()
    songs = respone_json["tracks"]["items"]
    uri = songs[0]["uri"]
    return uri

#adding songs to the playlist
def addSongs(playlist_name):
    gettingLikedVideos()
    uris = [info["spotify_uri"]
            for song, info in all_tracks_information.items()]

    query = "https://api.spotify.com/v1/playlists/{}/tracks".format(createPlaylist(playlist_name))
    r_body = uris
    request_body = json.dumps(r_body)
    response = requests.post(query, data=request_body,
                           headers={
                               "Content-type": "application/json",
                               "Authorization": "Bearer {}".format(s_token)
                           })
    response_json = response.json()
    return response_json

print("*** Check if your YouTube API key and Spotify API key are not expired ***");
str = input(("If yes, enter OK"));
num = input("Do you want to create a new playlist or add songs to an existing playlist? Enter 1 for the former and 2 for the latter");
if int(num) == 1:
       playlist_name = input("Enter the name of the newly created playlist");
       print(addSongs(playlist_name));
       print(getPlaylists())
else:
    print("SHOWING CURRENT PLAYLISTS. ENTER THE CORRESPONDING ID TO WHICH YOU WOULD LIKE TO ADD SONGS");
    print(getPlaylists())







