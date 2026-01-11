import base64
import os
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from starlette.responses import JSONResponse

from auth import SpotifyAuth
from mood import build_mood

router = APIRouter()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

spotify_auth = SpotifyAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

# User Authorization
@router.get('/login')
def login():
    params = {
        'client_id': spotify_auth.client_id,
        'response_type': 'code',
        'redirect_uri': spotify_auth.redirect_uri,
        'scope': 'user-library-read user-top-read user-read-recently-played'
    }
    return RedirectResponse(f'https://accounts.spotify.com/authorize?{urlencode(params)}')

@router.get('/callback')
def callback(request: Request):
    code = request.query_params.get('code')
    if not code:
        return {'error': 'No code returned'}

    auth_header = base64.b64encode(f'{spotify_auth.client_id}:{spotify_auth.client_secret}'.encode()).decode()

    response = httpx.post('https://accounts.spotify.com/api/token', headers={
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    })

    token_data = response.json()
    spotify_auth.auth_token = token_data['access_token']
    spotify_auth.auth_refresh_token = token_data['refresh_token']
    spotify_auth.auth_token_timeout = token_data['expires_in']

    response = RedirectResponse("http://127.0.0.1:3000/stats")  # UI
    response.set_cookie(
        key="access_token",
        value=token_data["access_token"],
        httponly=True,
        max_age=token_data["expires_in"],
        secure=False,
        samesite="lax"
    )
    return response

# API
@router.get('/user-data')
# @spotify_auth.check_auth_token_timeout
def user_data(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        return JSONResponse({'error': 'No access token'}, status_code=401)

    r = httpx.get('https://api.spotify.com/v1/me',
                   headers={'Authorization': f'Bearer {token}'})

    r_data = r.json()

    return {
        'name': r_data.get('display_name'),
        'photo': r_data.get('images', [{}])[0].get("url")
    }

@router.get('/top-tracks')
# @spotify_auth.check_auth_token_timeout
def top_tracks(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse({"error": "No access token"}, status_code=401)

    time_range = 'long_term'
    r = httpx.get(f'https://api.spotify.com/v1/me/top/tracks?limit=10&time_range={time_range}',
                   headers={'Authorization': f'Bearer {token}'})

    r_data = r.json()
    top_tracks = []

    for item in r_data.get('items', []):
        track_info = {
            'name': item['name'],
            'artist': ', '.join(artist['name'] for artist in item['artists']),
            'album_image_url': item['album']['images'][0]['url'] if item['album']['images'] else None
        }
        top_tracks.append(track_info)

    return top_tracks

@router.get('/top-artists')
# @spotify_auth.check_auth_token_timeout
def top_artists(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse({"error": "No access token"}, status_code=401)

    time_range = 'long_term'
    r = httpx.get(f'https://api.spotify.com/v1/me/top/artists?limit=10&time_range={time_range}',
                   headers={'Authorization': f'Bearer {token}'})

    r_data = r.json()
    top_artists = []

    for item in r_data.get('items', []):
        artist_info = {
            'name': item['name'],
            'image_url': item['images'][0]['url'] if item['images'] else None
        }
        top_artists.append(artist_info)

    return top_artists

@router.get('/top-tracks-by-artist')
# @spotify_auth.check_auth_token_timeout
def top_tracks_by_artist(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse({"error": "No access token"}, status_code=401)

    offset = 0
    limit = 50
    time_range = 'long_term'
    top_tracks_by_artist = {}

    while offset <= 50:
        r = httpx.get(
            f'https://api.spotify.com/v1/me/top/tracks?limit={limit}&offset={offset}&time_range={time_range}',
            headers={'Authorization': f'Bearer {token}'}
        )
        r_data = r.json()

        for item in r_data.get('items', []):
            first_artist  = item.get('artists', [{}])[0]
            artist_id  = first_artist.get('id', 'unknown_id')
            artist_name  = first_artist.get('name', 'Unknown Artist')
            if artist_id not in top_tracks_by_artist:
                top_tracks_by_artist[artist_id] = {
                    'name': artist_name,
                    'tracks': []
                }

            top_tracks_by_artist[artist_id]['tracks'].append({
                'id': item['id'],
                'name': item['name'],
                'album_image_url': item['album']['images'][0]['url'] if item['album']['images'] else None
            })

        offset += limit

    return top_tracks_by_artist

@router.get('/mood')
# @spotify_auth.check_auth_token_timeout
def mood(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse({"error": "No access token"}, status_code=401)

    limit = 20
    r = httpx.get(f'https://api.spotify.com/v1/me/player/recently-played?limit={limit}',
                   headers={'Authorization': f'Bearer {token}'})

    r_data = r.json()
    recently_listened_tracks = []

    for item in r_data.get('items', []):
        track_info = {
            'name': item['track']['name'],
            'artist': item['track']['artists'][0]['name']
        }
        recently_listened_tracks.append(track_info)

    return build_mood(recently_listened_tracks)