import time
import httpx

# API Access
class SpotifyAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = ''
        self.access_token_timeout = 0
        self.auth_token = ''
        self.auth_refresh_token = ''
        self.auth_token_timeout = 0

    def request_access_token(self):
        r = (httpx.post('https://accounts.spotify.com/api/token',
                       headers={'Content-Type': 'application/x-www-form-urlencoded'},
                       data={'grant_type': 'client_credentials',
                             'client_id': self.client_id,
                             'client_secret': self.client_secret}))

        data = r.json()
        self.access_token, self.access_token_timeout = data['access_token'], time.time() + data['expires_in']

    def request_auth_token(self):
        r = httpx.post('https://accounts.spotify.com/api/token',
                       headers={'Content-Type': 'application/x-www-form-urlencoded'},
                       data={'grant_type': 'refresh_token',
                             'client_id': self.client_id,
                             'refresh_token': self.auth_refresh_token})

        data = r.json()
        self.auth_token = data['access_token']
        self.auth_refresh_token = data['refresh_token']
        self.auth_token_timeout = data['expires_in']

    def check_access_token_timeout(self, func):
        def wrapper():
            if self.access_token_timeout - time.time() < 1:
                self.request_access_token()
            return func()

        return wrapper

    def check_auth_token_timeout(self, func):
        def wrapper():
            if self.auth_token_timeout - time.time() < 1:
                self.request_auth_token()
            return func()

        return wrapper