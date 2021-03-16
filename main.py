from getAccessToken import getToken
from credentials import stockApiKey
import requests

def main():
    newToken = getToken()
    headers = {"Authorization": "bearer " + newToken, "User-Agent": "pythonScript:StonksFinder/0.1 by thiccc69696969"}
    payload = {'limit': 100}
    redditEndpoint = "https://oauth.reddit.com/r/<SUBREDDIT>/rising"
    stockSubreddits = ['stocks', 'investing', 'wallstreetbets']
    stockQuoteEndpoint = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=<SYMBOL>&apikey=" + stockApiKey
    for i in range(4):
        print("PAGE: " + str(i))
        response = requests.get(redditEndpoint.replace("<SUBREDDIT>", stockSubreddits[0]), headers=headers, params=payload)
        for i in range(len(response.json()['data']['children'])):
            print(response.json()['data']['children'][i]['data']['title'] + "\n")
        payload['after'] = response.json()['data']['after']
        if payload['after'] is None:
            break
    stockResponse = requests.get(stockQuoteEndpoint.replace("<SYMBOL>", "GME"))
    print(stockResponse.json())

if __name__ == "__main__":
    main()
