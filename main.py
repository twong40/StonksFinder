from getAccessToken import getToken
import requests

def main():
    newToken = getToken()
    headers = {"Authorization": "bearer " + newToken, "User-Agent": "pythonScript:StonksFinder/0.1 by thiccc69696969"}
    response = requests.get("https://oauth.reddit.com/api/v1/me", headers=headers)
    print(response.json())

if __name__ == "__main__":
    main()
