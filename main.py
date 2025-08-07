import time
import httpx

from fastapi import FastAPI


app = FastAPI()
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'http://localhost:8000/callback'

# API Access
class SpotifyAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = ''
        self.access_token_timeout = 0

    def request_token(self):
        r = httpx.post('https://accounts.spotify.com/api/token',
                       headers={'Content-Type': 'application/x-www-form-urlencoded'},
                       data={'grant_type': 'client_credentials',
                             'client_id': self.client_id,
                             'client_secret': self.client_secret}).json()

        self.access_token, self.access_token_timeout = r['access_token'], time.time() + r['expires_in']

spotify_auth = SpotifyAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

def check_token_timeout(func):
    def wrapper():
        if spotify_auth.access_token_timeout - time.time() < 1:
            spotify_auth.request_token()
        return func()
    return wrapper