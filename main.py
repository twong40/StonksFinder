from getAccessToken import getToken
from databaseOperations import createClient, insertOne, insertMany
from credentials import stockApiKey
import requests
import itertools

def main():
    seenTitles = set()
    db = createClient()
    newToken = getToken()
    headers = {"Authorization": "bearer " + newToken, "User-Agent": "pythonScript:StonksFinder/0.1 by thiccc69696969"}
    payload = {'limit': 100}
    redditEndpoint = "https://oauth.reddit.com/r/<SUBREDDIT>/<FILTER>"
    stockSubreddits = ['stocks', 'investing', 'wallstreetbets']
    stockFilters = ['rising', 'new', 'top', 'best']
    stockQuoteEndpoint = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=<SYMBOL>&apikey=" + stockApiKey
    for subreddit, filter, i in itertools.product(stockSubreddits, stockFilters, range(4)):
        print("PAGE: " + str(i))
        response = requests.get(redditEndpoint.replace("<SUBREDDIT>", subreddit).replace("<FILTER>", filter), headers=headers, params=payload)
        for i in range(len(response.json()['data']['children'])):
            title = response.json()['data']['children'][i]['data']['title']
            if title not in seenTitles:
                seenTitles.add(title)
        payload['after'] = response.json()['data']['after']
        # if payload['after'] is None:
        #     break
        # stockResponse = requests.get(stockQuoteEndpoint.replace("<SYMBOL>", "GME"))
        # print(stockResponse.json())
    print(seenTitles)

if __name__ == "__main__":
    main()