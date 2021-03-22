from getAccessToken import getToken
from databaseOperations import createClient, insertOne, insertMany
from credentials import stockApiKey, userAgent
from datetime import datetime
import requests
import itertools
import time
import re

def main():
    db = createClient()
    stockSymbols = searchReddit()
    jsonData = searchStockInfo(stockSymbols)
    print("Phase 3: Saving to MongoDb")
    insertOne(db, jsonData)

def isValidSymbol(symbolToCheck):
    regex = re.compile('[0-9@_!#%^&*()<>?/\|}{~:]')
    if len(symbolToCheck) > 0 and len(symbolToCheck) <= 5 and regex.search(symbolToCheck) == None:
        return True
    return False

def searchReddit():
    print("Phase 1: Scanning subreddits")
    seenTitles = set()
    stockSymbols = dict()
    newToken = getToken()
    headers = {"Authorization": "bearer " + newToken, "User-Agent": userAgent}
    payload = {'limit': 100}
    redditEndpoint = "https://oauth.reddit.com/r/<SUBREDDIT>/<FILTER>"
    stockSubreddits = ['stocks', 'investing', 'wallstreetbets']
    stockFilters = ['rising', 'new', 'top', 'best']
    # Iterate through the possible subreddits and filters
    for subreddit, filterKey in itertools.product(stockSubreddits, stockFilters):
        # Iterate through at most 4 papges
        for i in range(5):
            response = requests.get(redditEndpoint.replace("<SUBREDDIT>", subreddit).replace("<FILTER>", filterKey), headers=headers, params=payload)
            for i in range(len(response.json()['data']['children'])):
                responseData = response.json()['data']['children'][i]['data']
                title = responseData['title']
                # If this is a new title, search for the ticker and add it to the map with the amount seen
                if title not in seenTitles:
                    seenTitles.add(title)
                    splitTitle = title.split()
                    for word in splitTitle:
                        index = word.find("$")
                        if index != -1 and isValidSymbol(word):
                            ticker = word[index + 1:].upper()
                            value = stockSymbols.get(ticker)
                            if value is None:
                                redditStockData = dict()
                                redditStockData["symbol"] = ticker
                                redditStockData["numberOfMentions"] = 1
                                redditStockData["ups"] = [responseData["ups"]]
                                redditStockData["upvote_ratio"] = [responseData["upvote_ratio"]]
                                redditStockData["total_awards_received"] = [responseData["total_awards_received"]]
                                redditStockData["gilded"] = [responseData["gilded"]]
                                redditStockData["num_comments"] = [responseData["num_comments"]]
                                stockSymbols[ticker] = redditStockData
                            else:
                                value["numberOfMentions"] = value["numberOfMentions"] + 1
                                value["ups"].append(responseData["ups"])
                                value["upvote_ratio"].append(responseData["upvote_ratio"])
                                value["total_awards_received"].append(responseData["total_awards_received"])
                                value["gilded"].append(responseData["gilded"])
                                value["num_comments"].append(responseData["num_comments"])
                                stockSymbols[ticker] = value
            # No Page afterwards
            payload['after'] = response.json()['data']['after']
            if payload['after'] is None:
                break
    return stockSymbols

def searchStockInfo(stockSymbols):
    print("Phase 2: Searching for stock info")
    stockQuoteEndpoint = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=<SYMBOL>&apikey=" + stockApiKey
    counter = 0
    jsonData = {"timeStamp" : datetime.now()}
    totalData = []
    for ticker in stockSymbols:
        # Api only allows 5 calls per minute, 500 calls per day
        if counter % 5 == 0:
            counter = 0
            time.sleep(60)
        stockResponse = requests.get(stockQuoteEndpoint.replace("<SYMBOL>", ticker))
        if "Global Quote" in stockResponse.json() and len(stockResponse.json()["Global Quote"]) != 0:
            extraStockData = dict()
            # Clean up json response data
            for key in stockResponse.json()["Global Quote"]:
                extraStockData[key[4:]] = stockResponse.json()["Global Quote"][key]
            totalData.append({**stockSymbols[ticker], **extraStockData})
        counter+= 1
    jsonData["data"] = totalData
    return jsonData

if __name__ == "__main__":
    main()