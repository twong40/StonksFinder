from getAccessToken import getToken
from databaseOperations import createClient, insertOne, insertMany
from credentials import stockApiKey
import requests
import itertools
import time

def main():
    seenTitles = set()
    stockSymbols = dict()
    db = createClient()
    newToken = getToken()
    headers = {"Authorization": "bearer " + newToken, "User-Agent": "pythonScript:StonksFinder/0.1 by thiccc69696969"}
    payload = {'limit': 100}
    redditEndpoint = "https://oauth.reddit.com/r/<SUBREDDIT>/<FILTER>"
    stockSubreddits = ['stocks', 'investing', 'wallstreetbets']
    stockFilters = ['rising', 'new', 'top', 'best']
    stockQuoteEndpoint = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=<SYMBOL>&apikey=" + stockApiKey
    # Iterate through the possible subreddits and filters
    for subreddit, filter in itertools.product(stockSubreddits, stockFilters):
        # Iterate through at most 4 papges
        for i in range(4):
            print("PAGE: " + str(i))
            response = requests.get(redditEndpoint.replace("<SUBREDDIT>", subreddit).replace("<FILTER>", filter), headers=headers, params=payload)
            for i in range(len(response.json()['data']['children'])):
                title = response.json()['data']['children'][i]['data']['title']
                # If this is a new title, search for the ticker and add it to the map with the amount seen
                if title not in seenTitles:
                    seenTitles.add(title)
                    splitTitle = title.split()
                    for word in splitTitle:
                        index = word.find("$")
                        if index != -1:
                            ticker = word[index + 1:]
                            value = stockSymbols.get(ticker)
                            if value is None:
                                stockSymbols[ticker] = 1
                            else:
                                stockSymbols[ticker] = value + 1
            # No Page afterwards
            payload['after'] = response.json()['data']['after']
            if payload['after'] is None:
                break
    counter = 0
    for ticker in stockSymbols:
        # Api only allows 5 calls per minute, 500 calls per day
        if counter % 5 == 0:
            counter = 0
            time.sleep(60)
        stockResponse = requests.get(stockQuoteEndpoint.replace("<SYMBOL>", ticker))
        if stockResponse.json()["Global Quote"] == None:
            stockSymbols.pop(ticker)
        print(stockResponse.json())
        counter+= 1


if __name__ == "__main__":
    main()