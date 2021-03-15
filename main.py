from getAccessToken import getToken
import requests

def main():
    newToken = getToken()
    headers = {"Authorization": "bearer " + newToken, "User-Agent": "pythonScript:StonksFinder/0.1 by thiccc69696969"}
    payload = { 'limit': 1}
    response = requests.get("https://oauth.reddit.com/r/stocks/rising", headers=headers, params=payload)
    print(response.json())

if __name__ == "__main__":
    main()
