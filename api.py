import base64
import os
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from auth import SpotifyAuth

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
        'scope': 'user-library-read'
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
    return token_data

# API
@router.get('/')
def hello_world():
    return 'Hello world!'
@router.get('/user_data')
@spotify_auth.check_auth_token_timeout
def user_data():
    r = httpx.get('https://api.spotify.com/v1/me',
                   headers={'Authorization': f'Bearer {spotify_auth.access_token}'}).json()

    return {
        'name': r['display_name'],
        'photo': r['images'][0]['url'],
    }