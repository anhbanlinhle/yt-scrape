from googleapiclient.discovery import build
import json
from youtube_transcript_api import YouTubeTranscriptApi
import ftfy
from underthesea import sent_tokenize
import os
from dotenv import load_dotenv

load_dotenv('./.env')

api_key = os.environ.get("API_KEY")
channel_ids = ['UCg3eoOGaArWo0AqEb7kzW2Q']
youtube = build('youtube', 'v3', developerKey=api_key)

# get the playlist id of the upload playlist
def UploadPlaylist(youtube, channel_ids):
  all_data = []
  request = youtube.channels().list(
    part = 'snippet, contentDetails, statistics',
    id = ','.join(channel_ids)
  )
  response = request.execute()

  for i in range(len(response['items'])):
    data = dict(UploadId = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'])
    all_data.append(data)

  return all_data

# get the video id of the upload playlist
def PlaylistItems(youtube, channel_ids):
  playlist_id = UploadPlaylist(youtube, channel_ids)[0]['UploadId']
  
  all_data = []
  
  request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=50,
        playlistId=playlist_id,
    )
  response = request.execute()

  for i in range(len(response['items'])):
    data = dict(id = response['items'][i]['id'],
                etag = response['items'][i]['etag'],
                videoId = response['items'][i]['contentDetails']['videoId'],
                channelId = response['items'][i]['snippet']['channelId'],
                playlistId = response['items'][i]['snippet']['playlistId'])
    data = dict(metadata = data)
    all_data.append(data)

  nextPageToken = response.get('nextPageToken')
  while ('nextPageToken' in response):
      nextPage = youtube.playlistItems().list(
              part="snippet,contentDetails",
              playlistId=playlist_id,
              maxResults=50,
              pageToken=nextPageToken
      ).execute()
      
      for i in range(len(nextPage['items'])):
        data = dict(id = nextPage['items'][i]['id'],
                    etag = nextPage['items'][i]['etag'],
                    videoId = nextPage['items'][i]['contentDetails']['videoId'],
                    channelId = nextPage['items'][i]['snippet']['channelId'],
                    playlistId = nextPage['items'][i]['snippet']['playlistId'])
        data = dict(metadata = data)
        all_data.append(data)

      if 'nextPageToken' not in nextPage:
          response.pop('nextPageToken', None)
      else:
          nextPageToken = nextPage['nextPageToken']

  return all_data

# get the transcript of the video
def VideoTransciptById(video_id):
  sub = ''
  text = str(video_id)
  try:
    response = YouTubeTranscriptApi.get_transcript(video_id, languages=['vi'])
    for i in range(len(response)):
      sub += ftfy.fix_text(response[i]['text']) + '\n'
    text += ': Done\n'
  except:
    text += ': No transcript\n'
  open('progress.txt', 'a').write(text)

  return sub

# get all transcript of the channel
def GetAllTranscript(youtube, channel_ids):
  all_data = []
  video_ids = PlaylistItems(youtube, channel_ids)
  open('progress.txt', 'w').write('')
  for i in range(len(video_ids)):
    videoId = video_ids[i]['metadata']['videoId']
    metadata = video_ids[i]['metadata']
    transcript = VideoTransciptById(videoId)
    
    data = dict(metadata = metadata, transcript = transcript)
    all_data.append(data)

  with open('result.json', 'w') as fp:
    json.dump(all_data, fp, indent=2, ensure_ascii=False)
  return 

GetAllTranscript(youtube, channel_ids)
# print(api_key)