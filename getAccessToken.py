from credentials import *
import requests
import requests.auth

def getToken():
    client_auth = requests.auth.HTTPBasicAuth(clientId, clientSecret)
    post_data = {"grant_type": "password", "username": userName, "password": password}
    headers = {"User-Agent": "pythonScript:StonkFinder/0.1 by thiccc69696969"}
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    if (response.json()["access_token"]):
        return response.json()["access_token"]
    else:
        return "NO TOKEN"
